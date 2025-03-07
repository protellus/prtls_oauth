from django.db import models
from django.utils.timezone import now

class OAuthToken(models.Model):
    """
    Generic model for storing OAuth tokens for various services.
    Supports Google, Zoho, and future integrations.
    """
    user_id = models.CharField(max_length=255, help_text="User ID associated with the token.")
    service = models.CharField(max_length=50, help_text="The external service this token belongs to., e.g google, zoho.")
    access_token = models.TextField(help_text="Access token for API authentication.")
    refresh_token = models.TextField(null=True, blank=True, help_text="Refresh token for obtaining a new access token.")
    expires_at = models.DateTimeField(help_text="Expiration time of the access token.")
    token_type = models.CharField(max_length=50, default="Bearer", help_text="Type of token (e.g., Bearer).")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the token was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the token was last updated.")

    class Meta:
        unique_together = ("user_id", "service")  # Prevent duplicate tokens for the same user & service
        indexes = [
            models.Index(fields=["service", "expires_at"]),  # Optimize queries by service and expiration
        ]
        verbose_name = "OAuth Token"  
        verbose_name_plural = "OAuth Tokens"

    def is_expired(self):
        """Check if the access token is expired."""
        return now() >= self.expires_at

    def __str__(self):
        return f"{self.user_id} - {self.service} (Expires: {self.expires_at})"
