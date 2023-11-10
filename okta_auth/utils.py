import logging
from base64 import urlsafe_b64decode

import jwt
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from django.conf import settings

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


def get_logout_url(redirect_uri, client_id=CLIENT_ID, domain=DOMAIN):
    params = urlencode({"post_logout_redirect_uri": redirect_uri, "id_token_hint": client_id})
    return "https://{domain}/oauth2/v1/logout?{params}".format(domain=domain, params=params)


def _get_jwk_set(domain=DOMAIN):
    url = "https://{domain}/oauth2/v1/keys".format(domain=domain)
    response = requests.get(url)
    if response.status_code != 200:
        logger.debug("Could not retrieve JSON web key set (JWKS) from {}".format(url))
        return {}
    return response.json()


def _jwk_to_public_key(json_web_key):
    def b64_decode(data):
        data += "=" * (4 - (len(data) % 4))
        return urlsafe_b64decode(data)

    exponent_bytes = b64_decode(json_web_key["e"])
    exponent_int = int.from_bytes(exponent_bytes, "big")
    modulus_bytes = b64_decode(json_web_key["n"])
    modulus_int = int.from_bytes(modulus_bytes, "big")
    return RSAPublicNumbers(exponent_int, modulus_int).public_key(default_backend())


def _get_public_key(token):
    token_key_id = jwt.get_unverified_header(token).get("kid")
    if not token_key_id:
        logger.debug("Token header does not contain key id (kid).")
        return None
    jwk_set = _get_jwk_set()
    json_web_key = next(
        (key for key in jwk_set.get("keys", []) if key.get("kid") == token_key_id), None
    )
    if not json_web_key:
        logger.debug("JSON web key (JWK) with kid {} not found".format(token_key_id))
        return None
    key = _jwk_to_public_key(json_web_key)
    return key


@lru_cache_with_expiration(seconds=60 * 60 * 24)
def _get_payload(token, audience=CLIENT_ID):
    public_key = _get_public_key(token)
    try:
        payload = jwt.decode(
            token, key=public_key, algorithms=["RS256"], audience=audience, leeway=300
        )
        return payload
    except jwt.InvalidTokenError as e:
        logger.debug("Could not retrieve payload. Token validation error, {}".format(str(e)))

    return {}


def get_email_from_token(token=None, key=CLIENT_SECRET, audience=CLIENT_ID):
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


def is_email_verified_from_token(token=None, key=CLIENT_SECRET, audience=CLIENT_ID):
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


def get_nonce_from_token(token=None, key=CLIENT_SECRET, audience=CLIENT_ID):
    try:
        payload = _get_payload(token=token, audience=audience)
        return payload.get("nonce")
    except jwt.InvalidTokenError as e:
        logger.debug("Could not retrieve nonce. Token validation error, {}".format(str(e)))

    return None
