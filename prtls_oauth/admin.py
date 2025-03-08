from django.contrib import admin
from django.urls import reverse, path
from django.utils.html import format_html
from django.utils.timezone import now
from django.contrib import messages
from prtls_utils.utils import get_setting
from prtls_oauth.models import OAuthToken
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)

@admin.register(OAuthToken)
class OAuthTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for managing OAuth tokens for multiple providers dynamically.
    """
    list_display = (
        "user_id",
        "service",
        "access_token_preview",
        "expires_at",
        "refresh_token_preview",
        "is_access_token_valid",
        "token_type",
        "created_at",
        "updated_at",
    )
    list_filter = ("service", "expires_at", "created_at", "updated_at", "token_type")
    search_fields = ("user_id", "service")
    ordering = ("service", "-expires_at")
    readonly_fields = ("access_token", "refresh_token", "created_at", "updated_at", "access_token_preview", "refresh_token_preview", "token_type", "user_id", "service", "expires_at", "is_access_token_valid")

    actions = ["refresh_access_token"]

    fieldsets = (
        ("User Information", {
            "fields": ("user_id", "service"),
        }),
        ("Token Details", {
            "fields": ("access_token", "refresh_token", "token_type","is_access_token_valid", "expires_at"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    # 🔹 Define a mapping of services to their respective classes dynamically
    OAUTH_PROVIDERS = get_setting("OAUTH_PROVIDERS", {})

    @classmethod
    def get_oauth_service(cls, service_name):
        """
        Dynamically import and return the OAuth service class for a given service name.
        """
        service_class_path = cls.OAUTH_PROVIDERS.get(service_name.lower())
        if not service_class_path:
            return None
        
        module_name, class_name = service_class_path.rsplit(".", 1)
        
        try:
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to import {class_name} from {module_name}: {e}")
            return None

    def access_token_preview(self, obj):
        """
        Display a preview of the access token (first 10 characters).
        """
        if obj.access_token:
            return f"{obj.access_token[:10]}..."
        return "No Access Token"
    access_token_preview.short_description = "Access Token"

    def refresh_token_preview(self, obj):
        """
        Display a preview of the refresh token (first 10 characters).
        """
        if obj.refresh_token:
            return f"{obj.refresh_token[:10]}..."
        return "No Refresh Token"
    refresh_token_preview.short_description = "Refresh Token"

    def is_access_token_valid(self, obj):
        """
        Check if the access token is still valid.
        """
        if obj.expires_at and obj.expires_at > now():
            return format_html('<span style="color: green;">Valid</span>')
        return format_html('<span style="color: red;">Expired</span>')
    is_access_token_valid.short_description = "Access Token Validity"

    def refresh_access_token(self, request, queryset):
        """
        Admin action to refresh access tokens for selected services.
        """
        if not queryset.exists():
            self.message_user(request, "No tokens selected. Please select at least one token to refresh.", messages.WARNING)
            return

        for token in queryset:
            try:
                # Dynamically get the correct service class
                service_class = self.get_oauth_service(token.service)
                if not service_class:
                    raise RuntimeError(f"No service found for {token.service}")

                # Call the refresh method
                service_class.refresh_access_token(token)
                self.message_user(request, f"Access token refreshed for {token.service} - user: {token.user_id}", messages.SUCCESS)

            except Exception as e:
                logger.error(f"Failed to refresh token for {token.service} - user {token.user_id}: {e}")
                self.message_user(request, f"Failed to refresh token for {token.service} - user {token.user_id}: {e}", messages.ERROR)

    refresh_access_token.short_description = "Refresh Access Token(s)"

    def changelist_view(self, request, extra_context=None):
        """
        Override the changelist view to add 'Authorize' buttons.
        """
        extra_context = extra_context or {}
        try:
            extra_context["authorize_google_url"] = reverse("gworkspace:authorize_google")
            extra_context["authorize_zoho_url"] = reverse("financials:authorize_zoho")
        except Exception as e:
            logger.error(f"Failed to reverse authorize urls: {e}")
            extra_context["authorize_google_url"] = None
            extra_context["authorize_zoho_url"] = None
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        """
        Add custom admin URLs for authorizing different OAuth providers.
        """
        urls = super().get_urls()
        custom_urls = [
            path(f"authorize_{service}/", self.admin_site.admin_view(self.authorize_service), name=f"authorize_{service}")
            for service in self.OAUTH_PROVIDERS.keys()
        ]
        return custom_urls + urls

    def authorize_service(self, request, service_name):
        """
        Handle the authorization redirect for different services.
        """
        try:
            service_class = self.get_oauth_service(service_name)
            if not service_class:
                self.message_user(request, f"OAuth service '{service_name}' not found.", messages.ERROR)
                return redirect("..")

            auth_url = service_class.get_authorization_url()
            return redirect(auth_url)

        except Exception as e:
            logger.error(f"Failed to initiate OAuth for {service_name}: {e}")
            self.message_user(request, f"Failed to initiate OAuth for {service_name}: {e}", messages.ERROR)
            return redirect("..")