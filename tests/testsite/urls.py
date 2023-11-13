from django.urls import include, path

from .views import login_successful

urlpatterns = [
    path("", login_successful, name="home"),
    path("okta/", include("okta_auth.urls")),
    path("login_successful/", login_successful, name="login_successful"),
]
