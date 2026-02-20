import pytest
from django.urls import reverse
from django_scopes import scopes_disabled

from pretalx_pages.models import Page
from pretalx_pages.signals import (
    event_copy_data_receiver,
    footer_link_pages,
    pretalx_activitylog_display,
    pretalx_activitylog_object_link,
    show_pages_to_orgnisers,
)


@pytest.mark.django_db
def test_orga_can_list_pages(orga_client, event):
    response = orga_client.get(
        reverse("plugins:pretalx_pages:index", kwargs={"event": event.slug}),
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_orga_can_list_pages_with_pages(orga_client, event, page):
    response = orga_client.get(
        reverse("plugins:pretalx_pages:index", kwargs={"event": event.slug}),
    )
    assert response.status_code == 200
    assert page.title in response.content.decode()


@pytest.mark.django_db
def test_reviewer_cannot_list_pages(review_client, event):
    response = review_client.get(
        reverse("plugins:pretalx_pages:index", kwargs={"event": event.slug}),
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_orga_can_create_page(orga_client, event):
    response = orga_client.get(
        reverse("plugins:pretalx_pages:create", kwargs={"event": event.slug}),
    )
    assert response.status_code == 200

    response = orga_client.post(
        reverse("plugins:pretalx_pages:create", kwargs={"event": event.slug}),
        {
            "title_0": "New Page",
            "slug": "new-page",
            "text_0": "Content here",
            "link_in_footer": "on",
        },
        follow=True,
    )
    assert response.status_code == 200
    with scopes_disabled():
        assert Page.objects.filter(event=event, slug="new-page").exists()
        p = Page.objects.get(event=event, slug="new-page")
        assert p.link_in_footer is True
        assert p.position == 1


@pytest.mark.django_db
def test_orga_can_edit_page(orga_client, event, page):
    response = orga_client.get(
        reverse(
            "plugins:pretalx_pages:edit",
            kwargs={"event": event.slug, "page": page.slug},
        ),
    )
    assert response.status_code == 200

    response = orga_client.post(
        reverse(
            "plugins:pretalx_pages:edit",
            kwargs={"event": event.slug, "page": page.slug},
        ),
        {
            "title_0": "Updated Title",
            "slug": page.slug,
            "text_0": "Updated content",
            "link_in_footer": "",
        },
        follow=True,
    )
    assert response.status_code == 200
    with scopes_disabled():
        page.refresh_from_db()
        assert str(page.title) == "Updated Title"


@pytest.mark.django_db
def test_orga_can_delete_page(orga_client, event, page):
    response = orga_client.get(
        reverse(
            "plugins:pretalx_pages:delete",
            kwargs={"event": event.slug, "page": page.slug},
        ),
    )
    assert response.status_code == 200

    response = orga_client.post(
        reverse(
            "plugins:pretalx_pages:delete",
            kwargs={"event": event.slug, "page": page.slug},
        ),
        follow=True,
    )
    assert response.status_code == 200
    with scopes_disabled():
        assert not Page.objects.filter(event=event, slug="test-page").exists()


@pytest.mark.django_db
def test_reviewer_cannot_create_page(review_client, event):
    response = review_client.get(
        reverse("plugins:pretalx_pages:create", kwargs={"event": event.slug}),
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_reviewer_cannot_edit_page(review_client, event, page):
    response = review_client.get(
        reverse(
            "plugins:pretalx_pages:edit",
            kwargs={"event": event.slug, "page": page.slug},
        ),
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_reviewer_cannot_delete_page(review_client, event, page):
    response = review_client.post(
        reverse(
            "plugins:pretalx_pages:delete",
            kwargs={"event": event.slug, "page": page.slug},
        ),
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_page_move_up(orga_client, event, page, footer_page):
    response = orga_client.get(
        reverse(
            "plugins:pretalx_pages:up",
            kwargs={"event": event.slug, "page": footer_page.slug},
        ),
        follow=True,
    )
    assert response.status_code == 200
    with scopes_disabled():
        footer_page.refresh_from_db()
        page.refresh_from_db()
        assert footer_page.position < page.position


@pytest.mark.django_db
def test_page_move_down(orga_client, event, page, footer_page):
    response = orga_client.get(
        reverse(
            "plugins:pretalx_pages:down",
            kwargs={"event": event.slug, "page": page.slug},
        ),
        follow=True,
    )
    assert response.status_code == 200
    with scopes_disabled():
        page.refresh_from_db()
        footer_page.refresh_from_db()
        assert page.position > footer_page.position


@pytest.mark.django_db
def test_page_move_up_first_stays(orga_client, event, page, footer_page):
    response = orga_client.get(
        reverse(
            "plugins:pretalx_pages:up", kwargs={"event": event.slug, "page": page.slug}
        ),
        follow=True,
    )
    assert response.status_code == 200
    with scopes_disabled():
        page.refresh_from_db()
        assert page.position == 0


@pytest.mark.django_db
def test_page_move_down_last_stays(orga_client, event, page, footer_page):
    response = orga_client.get(
        reverse(
            "plugins:pretalx_pages:down",
            kwargs={"event": event.slug, "page": footer_page.slug},
        ),
        follow=True,
    )
    assert response.status_code == 200
    with scopes_disabled():
        footer_page.refresh_from_db()
        assert footer_page.position == 1


@pytest.mark.django_db
def test_reviewer_cannot_move_pages(review_client, event, page):
    response = review_client.get(
        reverse(
            "plugins:pretalx_pages:up", kwargs={"event": event.slug, "page": page.slug}
        ),
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_move_nonexistent_page_404(orga_client, event):
    response = orga_client.get(
        reverse(
            "plugins:pretalx_pages:up",
            kwargs={"event": event.slug, "page": "nonexistent"},
        ),
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_public_page_view(client, event, page):
    response = client.get(
        reverse(
            "plugins:pretalx_pages:show",
            kwargs={"event": event.slug, "slug": page.slug},
        ),
    )
    assert response.status_code == 200
    assert "Test Page" in response.content.decode()
    assert "<strong>test</strong>" in response.content.decode()


@pytest.mark.django_db
def test_public_page_view_nonexistent(client, event):
    response = client.get(
        reverse(
            "plugins:pretalx_pages:show", kwargs={"event": event.slug, "slug": "nope"}
        ),
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_public_page_view_case_insensitive(client, event, page):
    response = client.get(
        reverse(
            "plugins:pretalx_pages:show",
            kwargs={"event": event.slug, "slug": "Test-Page"},
        ),
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_footer_links(event, footer_page, page):
    class FakeRequest:
        pass

    result = footer_link_pages(sender=event, request=FakeRequest())
    assert len(result) == 1
    assert result[0]["label"] == footer_page.title


@pytest.mark.django_db
def test_event_copy(event, other_event, page, footer_page):
    event_copy_data_receiver(sender=other_event, other=event.slug)
    with scopes_disabled():
        assert Page.objects.filter(event=other_event).count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("action", "expected"),
    (
        ("pretalx_pages.page.added", "The page has been created."),
        ("pretalx_pages.page.changed", "The page has been modified."),
        ("pretalx_pages.page.deleted", "The page has been deleted."),
        ("some.other.action", None),
    ),
)
def test_activitylog_display(event, action, expected):
    class FakeLog:
        action_type = action

    result = pretalx_activitylog_display(sender=event, activitylog=FakeLog())
    if expected:
        assert str(result) == expected
    else:
        assert result is None


@pytest.mark.django_db
def test_activitylog_object_link(event, page):
    class FakeLog:
        content_object = page

    result = pretalx_activitylog_object_link(sender=event, activitylog=FakeLog())
    assert "Test Page" in result
    assert page.slug in result


@pytest.mark.django_db
def test_activitylog_object_link_wrong_type(event):
    class FakeLog:
        content_object = event

    result = pretalx_activitylog_object_link(sender=event, activitylog=FakeLog())
    assert result is None


@pytest.mark.django_db
def test_nav_event_signal(orga_client, orga_user, event):
    class FakeRequest:
        user = orga_user
        path = f"/orga/event/{event.slug}/pages/"

    FakeRequest.event = event
    result = show_pages_to_orgnisers(sender=event, request=FakeRequest())
    assert len(result) == 1
    assert result[0]["label"] == "Pages"
    assert result[0]["active"] is True


@pytest.mark.django_db
def test_nav_event_signal_reviewer(review_user, event):
    class FakeRequest:
        user = review_user
        path = f"/orga/event/{event.slug}/pages/"

    FakeRequest.event = event
    result = show_pages_to_orgnisers(sender=event, request=FakeRequest())
    assert result == []


@pytest.mark.django_db
def test_page_ordering(event):
    with scopes_disabled():
        p1 = Page.objects.create(
            event=event, slug="z-page", position=0, title="Z", text="Z"
        )
        p2 = Page.objects.create(
            event=event, slug="a-page", position=0, title="A", text="A"
        )
        pages = list(Page.objects.filter(event=event))
    assert pages[0] == p2
    assert pages[1] == p1


@pytest.mark.django_db
def test_create_page_invalid_slug(orga_client, event):
    response = orga_client.post(
        reverse("plugins:pretalx_pages:create", kwargs={"event": event.slug}),
        {"title_0": "Bad", "slug": "!!!bad!!!", "text_0": "Invalid slug"},
    )
    assert response.status_code == 200
    with scopes_disabled():
        assert Page.objects.filter(event=event).count() == 0
