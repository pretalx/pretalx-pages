import django_tables2 as tables
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from pretalx.common.tables import ActionsColumn, DragsortTable

from .models import Page


def _page_url(name, record):
    return reverse(
        f"plugins:pretalx_pages:{name}",
        kwargs={"event": record.event.slug, "page": record.slug},
    )


class PageTable(DragsortTable):
    primary_column = "title"

    title = tables.Column(linkify=lambda record: _page_url("edit", record))
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

    def get_dragsort_url(self):
        return reverse("plugins:pretalx_pages:index", kwargs={"event": self.event.slug})

    class Meta:
        model = Page
        fields = ("title", "actions")
        empty_text = _("You haven't created any pages yet.")
