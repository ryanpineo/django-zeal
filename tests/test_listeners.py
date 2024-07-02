import logging

import pytest
from djangoproject.social.models import Post, User
from queryspy.errors import NPlusOneError
from queryspy.listeners import queryspy_context

from .factories import PostFactory, UserFactory

pytestmark = pytest.mark.django_db


@queryspy_context()
def test_can_log_errors(settings, caplog):
    settings.QUERYSPY_RAISE = False

    [user_1, user_2] = UserFactory.create_batch(2)
    PostFactory.create(author=user_1)
    PostFactory.create(author=user_2)
    with caplog.at_level(logging.WARNING):
        for user in User.objects.all():
            _ = list(user.posts.all())
        assert "N+1 detected on User.posts" in caplog.text


@queryspy_context()
def test_can_exclude_with_allowlist(settings):
    settings.QUERYSPY_ALLOWLIST = [{"model": "social.User", "field": "posts"}]

    [user_1, user_2] = UserFactory.create_batch(2)
    PostFactory.create(author=user_1)
    PostFactory.create(author=user_2)

    # this will not raise, allow-listed
    for user in User.objects.all():
        _ = list(user.posts.all())

    with pytest.raises(NPlusOneError):
        for post in Post.objects.all():
            _ = post.author


@queryspy_context()
def test_can_use_fnmatch_pattern_in_allowlist_model(settings):
    settings.QUERYSPY_ALLOWLIST = [{"model": "social.U*"}]

    [user_1, user_2] = UserFactory.create_batch(2)
    PostFactory.create(author=user_1)
    PostFactory.create(author=user_2)

    # this will not raise, allow-listed
    for user in User.objects.all():
        _ = list(user.posts.all())

    with pytest.raises(NPlusOneError):
        for post in Post.objects.all():
            _ = post.author


@queryspy_context()
def test_can_use_fnmatch_pattern_in_allowlist_field(settings):
    settings.QUERYSPY_ALLOWLIST = [{"model": "social.User", "field": "p*st*"}]

    [user_1, user_2] = UserFactory.create_batch(2)
    PostFactory.create(author=user_1)
    PostFactory.create(author=user_2)

    # this will not raise, allow-listed
    for user in User.objects.all():
        _ = list(user.posts.all())

    with pytest.raises(NPlusOneError):
        for post in Post.objects.all():
            _ = post.author
