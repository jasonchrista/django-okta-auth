import logging

import jwt
from cryptography.hazmat.primitives import serialization
from django.conf import settings
from jwt import PyJWKClient

from .cache import lru_cache_with_expiration

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


def get_logout_url(id_token, redirect_uri, domain=DOMAIN):
    params = urlencode({"post_logout_redirect_uri": redirect_uri, "id_token_hint": id_token})
    return "https://{domain}/oauth2/v1/logout?{params}".format(domain=domain, params=params)


@lru_cache_with_expiration(seconds=60 * 60 * 24)
def _get_payload(token, domain=DOMAIN, audience=CLIENT_ID):
    url = "https://{domain}/oauth2/v1/keys".format(domain=domain)
    jwks_client = PyJWKClient(url)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    pem_key = signing_key.key.public_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    try:
        payload = jwt.decode(
            token, key=pem_key, algorithms=["RS256"], audience=audience, leeway=300
        )
        return payload
    except jwt.InvalidTokenError as e:
        logger.debug("Could not retrieve payload. Token validation error, {}".format(str(e)))

    return {}


def get_email_from_token(token=None, audience=CLIENT_ID):
    try:
        payload = _get_payload(token=token, audience=audience)
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


def is_email_verified_from_token(token=None, audience=CLIENT_ID):
    try:
        payload = _get_payload(token=token, audience=audience)
        return payload.get("email_verified", True)
    except jwt.InvalidTokenError as e:
        logger.debug(
            "Could not determine email verification status. Token validation error, {}".format(
                str(e)
            )
        )

    return None


def get_nonce_from_token(token=None, audience=CLIENT_ID):
    try:
        payload = _get_payload(token=token, audience=audience)
        return payload.get("nonce")
    except jwt.InvalidTokenError as e:
        logger.debug("Could not retrieve nonce. Token validation error, {}".format(str(e)))

    return None
