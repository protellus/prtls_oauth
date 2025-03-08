import logging
from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

logger = logging.getLogger("oauth")

class BaseOAuthViewSet(ViewSet):
    """
    Generic OAuth viewset to handle authentication flows for multiple providers.
    Each provider should subclass this and define the appropriate OAuthService.
    """

    OAUTH_SERVICE = None  # Must be set in the subclass

    def get_oauth_service(self):
        if not self.OAUTH_SERVICE:
            raise RuntimeError("OAUTH_SERVICE must be defined in the subclass.")
        return self.OAUTH_SERVICE

    @action(detail=False, methods=["get"], url_path="authorize")
    def authorize(self, request):
        """
        Redirects to the OAuth provider's authorization page.
        """
        try:
            oauth_service = self.get_oauth_service()
            auth_url = oauth_service.get_authorization_url()
            logger.info(f"Redirecting to {oauth_service.OAUTH_PROVIDER_NAME} authorization URL")
            return redirect(auth_url)
        except RuntimeError as e:
            logger.error(f"Failed to generate authorization URL: {e}")
            return JsonResponse({"error": str(e)}, status=500)
        except Exception as e:
            logger.error(f"Unexpected error during authorization: {e}")
            return JsonResponse({"error": "An unexpected error occurred while redirecting"}, status=500)

    @action(detail=False, methods=["get"], url_path="callback")
    def callback(self, request):
        """
        Handles the OAuth callback and exchanges the authorization code for tokens.
        """
        try:
            logger.info("Handling OAuth callback")
            oauth_service = self.get_oauth_service()
            code = request.GET.get("code")

            logger.info(f"Received authorization code: {code}")
            if not code:
                logger.error("Authorization code not found in callback")
                return JsonResponse({"error": "Authorization code not found"}, status=400)

            # 🔹 Exchange code for tokens (Service handles saving)

            logger.info(f"Exchanging authorization code for tokens with {oauth_service.OAUTH_PROVIDER_NAME}")
            oauth_service.exchange_authorization_code(code)
            logger.info(f"OAuth token successfully retrieved and stored for {oauth_service.OAUTH_PROVIDER_NAME}")

            # 🎯 Redirect to Django Admin to view tokens
            return redirect(reverse("admin:prtlsoauth_oauthtoken_changelist"))

        except RuntimeError as e:
            logger.error(f"Error during OAuth callback handling: {e}")
            return JsonResponse({"error": str(e)}, status=500)
        except Exception as e:
            logger.error(f"Unexpected error during OAuth callback handling: {e}")
            return JsonResponse({"error": "An unexpected error occurred"}, status=500)
