from functools import partial

import bleach
from csp.decorators import csp_update
from django import forms
from django.contrib import messages
from django.db import transaction
from django.db.models import Max
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)
from i18nfield.forms import I18nModelForm
from pretalx.common.templatetags import rich_text
from pretalx.common.views.mixins import EventPermissionRequired

from .models import Page

ALLOWED_ATTRIBUTES = dict(rich_text.ALLOWED_ATTRIBUTES)
ALLOWED_ATTRIBUTES["a"] = ["href", "title", "target", "class"]
ALLOWED_ATTRIBUTES["p"] = ["class"]
ALLOWED_ATTRIBUTES["li"] = ["class"]
ALLOWED_ATTRIBUTES["img"] = ["src", "title", "alt", "class"]
CLEANER = bleach.Cleaner(
    tags=rich_text.ALLOWED_TAGS
    | {"img", "p", "br", "s", "sup", "sub", "u", "h3", "h4", "h5", "h6"},
    attributes=ALLOWED_ATTRIBUTES,
    protocols=rich_text.ALLOWED_PROTOCOLS | {"data"},
    filters=[
        partial(
            bleach.linkifier.LinkifyFilter,
            url_re=rich_text.TLD_REGEX,
            parse_email=True,
            email_re=rich_text.EMAIL_REGEX,
            skip_tags={"pre", "code"},
            callbacks=bleach.linkifier.DEFAULT_CALLBACKS
            + [rich_text.safelink_callback],
        )
    ],
)


class PageList(EventPermissionRequired, ListView):
    model = Page
    context_object_name = "pages"
    paginate_by = 20
    template_name = "pretalx_pages/index.html"
    permission_required = "event.update_event"

    def get_queryset(self):
        return Page.objects.filter(event=self.request.event)


def page_move(request, page, up=True):
    """This is a helper function to avoid duplicating code in page_move_up and
    page_move_down.

    It takes a page and a direction and then tries to bring all pages
    for this event in a new order.
    """
    if not request.user.has_perm("event.update_event", request.event):
        raise Http404(_("The requested page does not exist."))

    try:
        page = request.event.pages.get(slug__iexact=page)
    except Page.DoesNotExist:
        raise Http404(_("The requested page does not exist."))
    pages = list(request.event.pages.order_by("position", "title"))

    index = pages.index(page)
    if index != 0 and up:
        pages[index - 1], pages[index] = pages[index], pages[index - 1]
    elif index != len(pages) - 1 and not up:
        pages[index + 1], pages[index] = pages[index], pages[index + 1]

    for i, p in enumerate(pages):
        if p.position != i:
            p.position = i
            p.save()

    messages.success(request, _("The order of pages has been updated."))


def page_move_up(request, event, page):
    page_move(request, page, up=True)
    return redirect("plugins:pretalx_pages:index", event=request.event.slug)


def page_move_down(request, event, page):
    page_move(request, page, up=False)
    return redirect("plugins:pretalx_pages:index", event=request.event.slug)


class PageForm(I18nModelForm):
    def __init__(self, *args, **kwargs):
        self.event = kwargs.get("event")
        super().__init__(*args, **kwargs)

    class Meta:
        model = Page
        fields = (
            "title",
            "slug",
            "text",
            "link_in_footer",
        )

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if Page.objects.filter(slug__iexact=slug, event=self.event).exists():
            raise forms.ValidationError(
                _("You already have a page on that URL."),
                code="duplicate_slug",
            )
        return slug


class PageEditForm(PageForm):
    slug = forms.CharField(label=_("URL form"), disabled=True)

    def clean_slug(self):
        return self.instance.slug


class PageDetailMixin:
    def get_object(self, queryset=None) -> Page:
        try:
            return Page.objects.get(
                event=self.request.event, slug__iexact=self.kwargs["page"]
            )
        except Page.DoesNotExist:
            raise Http404(_("The requested page does not exist."))

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretalx_pages:index",
            kwargs={
                "event": self.request.event.slug,
            },
        )


class PageDelete(EventPermissionRequired, PageDetailMixin, DeleteView):
    model = Page
    form_class = PageForm
    template_name = "pretalx_pages/delete.html"
    context_object_name = "page"
    permission_required = "event.update_event"

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.log_action(
            "pretalx_pages.page.deleted", person=self.request.user, orga=True
        )
        self.object.delete()
        messages.success(request, _("The selected page has been deleted."))
        return HttpResponseRedirect(self.get_success_url())


class PageEditorMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["locales"] = self.request.event.locales
        return kwargs


class PageUpdate(EventPermissionRequired, PageDetailMixin, PageEditorMixin, UpdateView):
    model = Page
    form_class = PageEditForm
    template_name = "pretalx_pages/form.html"
    context_object_name = "page"
    permission_required = "event.update_event"

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretalx_pages:edit",
            kwargs={"event": self.request.event.slug, "page": self.object.slug},
        )

    @transaction.atomic
    def form_valid(self, form):
        messages.success(self.request, _("Your changes have been saved."))
        if form.has_changed():
            self.object.log_action(
                "pretalx_pages.page.changed",
                person=self.request.user,
                data={k: form.cleaned_data.get(k) for k in form.changed_data},
                orga=True,
            )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, _("We could not save your changes. See below for details.")
        )
        return super().form_invalid(form)


class PageCreate(EventPermissionRequired, PageEditorMixin, CreateView):
    model = Page
    form_class = PageForm
    template_name = "pretalx_pages/form.html"
    permission_required = "event.update_event"

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretalx_pages:index",
            kwargs={
                "event": self.request.event.slug,
            },
        )

    @transaction.atomic
    def form_valid(self, form):
        form.instance.event = self.request.event
        form.instance.position = (
            self.request.event.pages.aggregate(p=Max("position"))["p"] or 0
        ) + 1
        messages.success(self.request, _("The new page has been created."))
        ret = super().form_valid(form)
        form.instance.log_action(
            "pretalx_pages.page.added",
            data=dict(form.cleaned_data),
            person=self.request.user,
            orga=True,
        )
        return ret

    def form_invalid(self, form):
        messages.error(
            self.request, _("We could not save your changes. See below for details.")
        )
        return super().form_invalid(form)


@method_decorator(csp_update({"img-src": "*"}), name="dispatch")
class ShowPageView(TemplateView):
    template_name = "pretalx_pages/show.html"

    def get_page(self):
        try:
            return Page.objects.get(
                event=self.request.event, slug__iexact=self.kwargs["slug"]
            )
        except Page.DoesNotExist:
            raise Http404(_("The requested page does not exist."))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        page = self.get_page()
        ctx["page_title"] = page.title
        ctx["content"] = CLEANER.clean(rich_text.md.reset().convert(str(page.text)))
        return ctx
