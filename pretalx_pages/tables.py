import django_tables2 as tables
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from pretalx.common.tables import ActionsColumn, BooleanColumn, Column, DragsortTable

from .models import Page

EXPORT_ONLY = {"export_only": True}


def _page_url(name, record):
    return reverse(
        f"plugins:pretalx_pages:{name}",
        kwargs={"event": record.event.slug, "page": record.slug},
    )


class PageTable(DragsortTable):
    primary_column = "title"
    export_name = _("Pages")
    export_permission = "event.update_event"
    default_columns = ("title",)

    title = tables.Column(linkify=lambda record: _page_url("edit", record))
    slug = Column()
    position = Column()
    link_in_footer = BooleanColumn()
    text = Column(**EXPORT_ONLY)
    actions = ActionsColumn(
        actions={
            "view": {
                "icon": "eye",
                "title": _("View page"),
                "url": lambda record: reverse(
                    "plugins:pretalx_pages:show",
                    kwargs={"event": record.event.slug, "slug": record.slug},
                ),
                "extra_attrs": 'target="_blank"',
            },
            "edit": {"url": lambda record: _page_url("edit", record)},
            "delete": {"url": lambda record: _page_url("delete", record)},
        }
    )

    @classmethod
    def base_queryset(cls, event, user):
        return event.pages.all()

    def get_dragsort_url(self):
        return reverse("plugins:pretalx_pages:index", kwargs={"event": self.event.slug})

    class Meta:
        model = Page
        fields = ("title", "slug", "position", "link_in_footer", "text", "actions")
