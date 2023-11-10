from django.contrib.auth import authenticate
from django.test import Client, TestCase
from django.urls import reverse


class LoginTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_login_url(self):
        url = reverse("okta:login")
        response = self.client.get(url)
        print(response.url)

    def test_logout_url(self):
        url = reverse("okta:logout")
        response = self.client.get(url)
        print(response.url)
