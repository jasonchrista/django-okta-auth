from django.urls import include, re_path

from .views import js_login, login_successful

urlpatterns = [
    re_path(r"^auth0/", include("auth0_auth.urls")),
    re_path(r"^js_login/$", js_login, name="js_login"),
    re_path(r"^login_successful/$", login_successful, name="login_successful"),
]
