from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, login
from django.contrib.auth import logout as auth_logout
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, resolve_url

from .backends import OktaBackend
from .utils import get_nonce_from_token

try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse

import logging

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import uuid

logger = logging.getLogger("okta_auth")


@never_cache
def auth(request):
    backend = OktaBackend()
    redirect_uri = request.build_absolute_uri(reverse("okta:callback"))
    redirect_to = request.GET.get(REDIRECT_FIELD_NAME, "")
    if redirect_to:
        # redirect_uri = "{}?{}={}".format(redirect_uri, REDIRECT_FIELD_NAME, redirect_to)
        request.session[REDIRECT_FIELD_NAME] = redirect_to
    state = str(uuid.uuid4())
    request.session["state"] = state
    nonce = str(uuid.uuid4())
    request.session["nonce"] = nonce
    login_url = backend.login_url(
        redirect_uri=redirect_uri,
        state=state,
        nonce=nonce,
    )
    return HttpResponseRedirect(login_url)


@never_cache
def logout(request):
    backend = OktaBackend()
    id_token = request.session.get("id_token")
    logout_redirect_url = getattr(settings, "LOGOUT_REDIRECT_URL", "/")
    redirect_uri = request.build_absolute_uri(resolve_url(logout_redirect_url))
    logout_url = backend.logout_url(
        id_token=id_token,
        redirect_uri=redirect_uri,
    )
    auth_logout(request)
    return HttpResponseRedirect(logout_url)


@never_cache
@csrf_exempt
def callback(request):
    login_response = redirect("okta:login")
    backend = OktaBackend()

    original_state = request.session.get("state")
    state = request.POST.get("state")
    if original_state != state:
        logger.debug("Expected state {} but received {}.".format(original_state, state))
        return login_response

    token = request.POST.get("id_token")
    request.session["id_token"] = token
    logger.debug("Token {} received".format(token))

    original_nonce = request.session.get("nonce")
    nonce = get_nonce_from_token(token=token)
    if original_nonce != nonce:
        logger.debug("Expected nonce {} but received {}.".format(original_nonce, nonce))
        return login_response

    user = backend.authenticate(token=token)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect(get_login_success_url(request))
    else:
        logger.debug("Authenticated user not in user database.")
        raise PermissionDenied()


def get_login_success_url(request):
    # redirect_to = request.GET.get(REDIRECT_FIELD_NAME, "")
    redirect_to = request.session.pop(REDIRECT_FIELD_NAME, "")
    netloc = urlparse(redirect_to)[1]
    if not redirect_to:
        redirect_to = settings.LOGIN_REDIRECT_URL
    elif netloc and netloc != request.get_host():
        redirect_to = settings.LOGIN_REDIRECT_URL
    return redirect_to
