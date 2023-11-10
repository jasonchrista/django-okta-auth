from django.urls import re_path

from .views import auth, callback, logout

app_name = "okta"
urlpatterns = [
    re_path(r"^login/$", auth, name="login"),
    re_path(r"^logout/$", logout, name="logout"),
    re_path(r"^callback/$", callback, name="callback"),
]
