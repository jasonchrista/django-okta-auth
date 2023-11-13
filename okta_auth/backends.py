from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .utils import get_email_from_token, get_login_url, get_logout_url, is_email_verified_from_token

try:
    from django.contrib.auth import get_user_model
except ImportError:
    from django.contrib.auth.models import User

    def get_user_model(*args, **kwargs):
        return User


if getattr(settings, "SESSION_COOKIE_SAMESITE"):
    raise ImproperlyConfigured(
        """Please set the SESSION_COOKIE_SAMESITE to None in your settings.py. To prevent replay 
        attacks and forgery the callback URL verifies a unique state string and nonce string stored 
        the session is equal value that is posted back by Okta."""
    )


class OktaBackend(object):
    USER_CREATION = getattr(settings, "OKTA_USER_CREATION", True)

    supports_anonymous_user = False
    supports_inactive_user = True
    supports_object_permissions = False

    def __init__(self):
        self.User = get_user_model()

    def login_url(self, redirect_uri, state, nonce):
        return get_login_url(redirect_uri=redirect_uri, state=state, nonce=nonce)

    def logout_url(self, id_token, redirect_uri):
        return get_logout_url(id_token=id_token, redirect_uri=redirect_uri)

    def authenticate(self, token=None, **kwargs):
        if token is None:
            return None

        email = get_email_from_token(token=token)

        if email is None:
            return None

        email_verified = is_email_verified_from_token(token=token)

        if not email_verified:
            return None

        users = self.User.objects.filter(email=email)
        if len(users) == 0:
            user = self.create_user(email)
            if user is None:
                return None
        elif len(users) == 1:
            user = users[0]
        else:
            return None
        if not self.user_can_authenticate(user):
            return None
        user.backend = "{}.{}".format(self.__class__.__module__, self.__class__.__name__)
        return user

    def user_can_authenticate(self, user):
        is_active = getattr(user, "is_active", None)
        return is_active or is_active is None

    def get_user(self, user_id):
        try:
            user = self.User.objects.get(pk=user_id)
            return user
        except self.User.DoesNotExist:
            return None

    def create_user(self, email):
        if self.USER_CREATION:
            username_field = getattr(self.User, "USERNAME_FIELD", "username")
            user_kwargs = {"email": email}
            user_kwargs[username_field] = self.username_generator(email)
            return self.User.objects.create_user(**user_kwargs)
        else:
            return None

    @staticmethod
    def username_generator(email):
        return str(uuid4())
