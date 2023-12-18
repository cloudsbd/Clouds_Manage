from django.urls import path
from django.contrib import admin
from django.urls import include, path
from . import views

urlpatterns = [
    path("index", views.index, name="index"),
    path("begin_oauth_login", views.begin_oauth_login, name="begin_oauth_login"),
    path("oauth_redirect", views.oauth_redirect, name="oauth_redirect"),
    path("get_login_client", views.get_login_client, name="get_login_client"),
    path("start_auth", views.start_auth, name="start_auth"),
    path("auth_callback", views.auth_callback, name="auth_callback"),
    path("make_instance", views.make_instance, name="make_instance"),
    path("create_stackscript", views.create_stackscript, name="create_stackscript"),
]

