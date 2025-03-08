from django.urls import path
from prtls_oauth.views import BaseOAuthViewSet

app_name = "oauth"  # Define the namespace

urlpatterns = [
    path("authorize/base/", BaseOAuthViewSet.as_view({"get": "authorize"}), name="authorize_base"),
    path("callback/base/", BaseOAuthViewSet.as_view({"get": "callback"}), name="base_callback"),
]
