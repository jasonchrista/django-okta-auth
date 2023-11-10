import logging
from base64 import urlsafe_b64decode

import jwt
from django.conf import settings

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode


logger = logging.getLogger("okta_auth")


DOMAIN = getattr(settings, "OKTA_DOMAIN")
SCOPE = getattr(settings, "OKTA_SCOPE", "openid email")
RESPONSE_TYPE = getattr(settings, "OKTA_RESPONSE_TYPE", "id_token")
CLIENT_ID = getattr(settings, "OKTA_CLIENT_ID")
CLIENT_SECRET = getattr(settings, "OKTA_CLIENT_SECRET")


def get_login_url(
    domain=DOMAIN,
    scope=SCOPE,
    client_id=CLIENT_ID,
    redirect_uri=None,
    response_type=RESPONSE_TYPE,
    response_mode="form_post",
    state=None,
    nonce=None,
):
    param_dict = {
        "response_type": response_type,
        "response_mode": response_mode,
        "scope": scope,
        "nonce": "nonce",
        "client_id": client_id,
    }
    if redirect_uri is not None:
        param_dict["redirect_uri"] = redirect_uri
    if state is not None:
        param_dict["state"] = state
    if nonce is not None:
        param_dict["nonce"] = nonce
    params = urlencode(param_dict)
    return "https://{domain}/oauth2/v1/authorize?{params}".format(domain=domain, params=params)


def get_logout_url(redirect_uri, client_id=CLIENT_ID, domain=DOMAIN):
    params = urlencode({"post_logout_redirect_uri": redirect_uri, "id_token_hint": client_id})
    return "https://{domain}/oauth2/v1/logout?{params}".format(domain=domain, params=params)


def get_email_from_token(token=None, key=CLIENT_SECRET, audience=CLIENT_ID):
    try:
        payload = jwt.decode(
            token, key=key, algorithms=["HS256", "RS256"], audience=audience, leeway=300
        )
        if "email" in payload:
            return payload["email"]
        elif "sub" in payload:
            return payload["sub"].split("|").pop()
        else:
            logger.debug(
                'Could not retrieve email. Token payload does not contain keys: "email" or "sub".'
            )
    except jwt.InvalidTokenError as e:
        logger.debug("Could not retrieve email. Token validation error, {}".format(str(e)))

    return None


def is_email_verified_from_token(token=None, key=CLIENT_SECRET, audience=CLIENT_ID):
    try:
        payload = jwt.decode(
            token, key=key, algorithms=["HS256", "RS256"], audience=audience, leeway=300
        )
        return payload.get("email_verified", True)
    except jwt.InvalidTokenError as e:
        logger.debug(
            "Could not determine email verification status. Token validation error, {}".format(
                str(e)
            )
        )

    return None


def get_nonce_from_token(token=None, key=CLIENT_SECRET, audience=CLIENT_ID):
    try:
        payload = jwt.decode(
            token, key=key, algorithms=["HS256", "RS256"], audience=audience, leeway=300
        )
        return payload.get("nonce")
    except jwt.InvalidTokenError as e:
        logger.debug("Could not retrieve nonce. Token validation error, {}".format(str(e)))

    return None
