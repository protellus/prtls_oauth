# 🔑 OAuth Package for Django

This package provides a reusable **OAuth authentication system** for Django that supports multiple providers like **Google, Zoho, Microsoft, etc.**. Each provider should **subclass** the base service and viewset to customize its behavior.

## 🚀 Features
✅ **Pluggable OAuth authentication flow** (supports multiple providers)  
✅ **Authorization, token retrieval, and automatic refresh**  
✅ **Customizable via service provider overrides**  
✅ **Django Admin integration for managing tokens**  
✅ **Dynamic service-based provider structure**  

## **🛠️ Installation**
To install from a private GitHub repository:  

pip install git+https://github.com/YOUR_USERNAME/oauth.git@main

For local development:  
pip install -e /path/to/oauth

## **⚙️ Configuration**
Add `"oauth"` to your Django **`INSTALLED_APPS`** in `settings.py`:  

INSTALLED_APPS = [
    "django.contrib.admin",
    "oauth",
]

Define the available OAuth providers and credentials in `settings.py`:  

SITE_URL = "https://yourdomain.com"

OAUTH_PROVIDERS = {
    "google": "gworkspace.services.GoogleOAuthService",
    "zoho": "financials.services.ZohoOAuthService",
}

GOOGLE_CLIENT_ID = "your-google-client-id"
GOOGLE_CLIENT_SECRET = "your-google-client-secret"
ZOHO_CLIENT_ID = "your-zoho-client-id"
ZOHO_CLIENT_SECRET = "your-zoho-client-secret"

## **📤 OAuth Workflow**
The OAuth package provides a **standardized authentication flow** that can be **overridden for each provider**:  
1️⃣ **Authorization Request:** Redirects the user to the provider’s authorization page.  
2️⃣ **Callback Handling:** Exchanges the authorization code for an access token.  
3️⃣ **Token Refresh:** Automatically refreshes expired access tokens.  
4️⃣ **Token Revocation:** Revokes access tokens when needed.  

## **🔌 Overriding the Base OAuth Implementation**
Each provider must override `OAuthService` to customize its behavior:  

from oauth.services import OAuthService

class GoogleOAuthService(OAuthService):
    OAUTH_PROVIDER_NAME = "google"
    OAUTH_CLIENT_ID = "your-google-client-id"
    OAUTH_CLIENT_SECRET = "your-google-client-secret"
    OAUTH_BASE_URL = "https://accounts.google.com/o"
    OAUTH_AUTH_ENDPOINT = "/oauth2/auth"
    OAUTH_TOKEN_ENDPOINT = "/oauth2/token"
    OAUTH_REVOKE_ENDPOINT = "/oauth2/revoke"
    OAUTH_SCOPE = "https://www.googleapis.com/auth/userinfo.email"
    EXTRA_AUTH_PARAMS = {"access_type": "offline"}

Each provider must also override `BaseOAuthViewSet` to specify the correct service:  

from oauth.views import BaseOAuthViewSet
from gworkspace.services import GoogleOAuthService

class GoogleOAuthViewSet(BaseOAuthViewSet):
    OAUTH_SERVICE = GoogleOAuthService

Then, register the provider-specific OAuth endpoints in `urls.py`:  

from django.urls import path
from gworkspace.views import GoogleOAuthViewSet

app_name = "gworkspace"

urlpatterns = [
    path("authorize/google/", GoogleOAuthViewSet.as_view({"get": "authorize"}), name="authorize_google"),
    path("callback/google/", GoogleOAuthViewSet.as_view({"get": "callback"}), name="callback_google"),
]

