import pytest
from djangoproject.social.models import Post, Profile, User
from queryspy import NPlusOneError, queryspy_context

from .factories import PostFactory, ProfileFactory, UserFactory

pytestmark = pytest.mark.django_db


@queryspy_context()
def test_detects_nplusone_in_forward_many_to_one():
    [user_1, user_2] = UserFactory.create_batch(2)
    PostFactory.create(author=user_1)
    PostFactory.create(author=user_2)
    with pytest.raises(NPlusOneError):
        for post in Post.objects.all():
            _ = post.author.username

    for post in Post.objects.select_related("author").all():
        _ = post.author.username


@queryspy_context()
def test_detects_nplusone_in_reverse_many_to_one():
    [user_1, user_2] = UserFactory.create_batch(2)
    PostFactory.create(author=user_1)
    PostFactory.create(author=user_2)
    with pytest.raises(NPlusOneError):
        for user in User.objects.all():
            _ = list(user.posts.all())

    for user in User.objects.prefetch_related("posts").all():
        _ = list(user.posts.all())


@queryspy_context()
def test_detects_nplusone_in_forward_one_to_one():
    [user_1, user_2] = UserFactory.create_batch(2)
    ProfileFactory.create(user=user_1)
    ProfileFactory.create(user=user_2)
    with pytest.raises(NPlusOneError):
        for profile in Profile.objects.all():
            _ = profile.user.username

    for profile in Profile.objects.select_related("user").all():
        _ = profile.user.username


@queryspy_context()
def test_detects_nplusone_in_reverse_one_to_one():
    [user_1, user_2] = UserFactory.create_batch(2)
    ProfileFactory.create(user=user_1)
    ProfileFactory.create(user=user_2)
    with pytest.raises(NPlusOneError):
        for user in User.objects.all():
            _ = user.profile.display_name

    for user in User.objects.select_related("profile").all():
        _ = user.profile.display_name


@queryspy_context()
def test_detects_nplusone_in_forward_many_to_many():
    [user_1, user_2] = UserFactory.create_batch(2)
    user_1.following.add(user_2)
    user_2.following.add(user_1)
    with pytest.raises(NPlusOneError):
        for user in User.objects.all():
            _ = list(user.following.all())

    for user in User.objects.prefetch_related("following").all():
        _ = list(user.following.all())


@queryspy_context()
def test_detects_nplusone_in_reverse_many_to_many():
    [user_1, user_2] = UserFactory.create_batch(2)
    user_1.following.add(user_2)
    user_2.following.add(user_1)
    with pytest.raises(NPlusOneError):
        for user in User.objects.all():
            _ = list(user.followers.all())

    for user in User.objects.prefetch_related("followers").all():
        _ = list(user.followers.all())


@queryspy_context()
def test_detects_nplusone_in_reverse_many_to_many_with_no_related_name():
    [user_1, user_2] = UserFactory.create_batch(2)
    user_1.blocked.add(user_2)
    user_2.blocked.add(user_1)
    with pytest.raises(NPlusOneError):
        for user in User.objects.all():
            _ = list(user.user_set.all())

    for user in User.objects.prefetch_related("user_set").all():
        _ = list(user.user_set.all())


@queryspy_context()
def test_detects_nplusone_due_to_deferred_fields():
    [user_1, user_2] = UserFactory.create_batch(2)
    PostFactory.create(author=user_1)
    PostFactory.create(author=user_2)
    with pytest.raises(NPlusOneError):
        for post in (
            Post.objects.all().select_related("author").only("author__id")
        ):
            _ = post.author.username

    for post in (
        Post.objects.all().select_related("author").only("author__username")
    ):
        _ = post.author.username


def test_has_configurable_threshold(settings):
    settings.QUERYSPY_NPLUSONE_THRESHOLD = 3
    [user_1, user_2] = UserFactory.create_batch(2)
    PostFactory.create(author=user_1)
    PostFactory.create(author=user_2)

    for post in Post.objects.all():
        _ = post.author.username


def test_does_nothing_if_not_in_middleware(settings, client):
    settings.MIDDLEWARE = []
    [user_1, user_2] = UserFactory.create_batch(2)
    ProfileFactory.create(user=user_1)
    ProfileFactory.create(user=user_2)

    # this does not raise an N+1 error even though the same
    # related field gets hit twice
    response = client.get(f"/user/{user_1.pk}/")
    assert response.status_code == 200
    response = client.get(f"/user/{user_2.pk}/")
    assert response.status_code == 200


def test_works_in_web_requests(client):
    [user_1, user_2] = UserFactory.create_batch(2)
    ProfileFactory.create(user=user_1)
    ProfileFactory.create(user=user_2)
    with pytest.raises(NPlusOneError):
        response = client.get("/users/")
        assert response.status_code == 500

    # but multiple requests work fine
    response = client.get(f"/user/{user_1.pk}/")
    assert response.status_code == 200
    response = client.get(f"/user/{user_2.pk}/")
    assert response.status_code == 200
