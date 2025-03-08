import requests
import datetime
import secrets
import logging
from django.apps import apps
from django.urls import reverse
from django.utils.timezone import now
from prtls_utils.utils import get_setting

logger = logging.getLogger('oauth')

class OAuthService:
    """
    Generic OAuth service that can be subclassed for specific providers (Google, Zoho, Microsoft, etc.).
    Subclasses must define their provider-specific class variables.
    """
    # These MUST be defined in subclasses

    OAUTH_PROVIDER_NAME = None
    OAUTH_CLIENT_ID = None
    OAUTH_CLIENT_SECRET = None
    OAUTH_BASE_URL = None
    OAUTH_AUTH_ENDPOINT = None
    OAUTH_TOKEN_ENDPOINT = None
    OAUTH_REVOKE_ENDPOINT = None
    OAUTH_SCOPE = None
    APP_NAME = "oauth" # The Django app name, needed for reverse URLs, override in subclass
    EXTRA_AUTH_PARAMS = {}  # Allow subclasses to specify provider-specific parameters

    @property
    def AUTH_TOKEN_MODEL(self):
        """ Lazily load the OAuthToken model to avoid AppRegistryNotReady issues """
        return apps.get_model("prtls_oauth", "OAuthToken")  # ✅ This ensures the model is loaded dynamically

    
    @classmethod
    def get_token(cls, user_id="default"):
        """
        Get a valid access token for a user. 
        - If the token is expired, attempt to refresh it.
        - If no refresh token is available, log an error and request reauthorization.
        
        Args:
            user_id (str): Identifier for the user.

        Returns:
            str: A valid access token.
        """
        OAuthToken = cls().AUTH_TOKEN_MODEL
        try:
            # Check for an existing valid access token
            token = OAuthToken.objects.filter(
                user_id=user_id, 
                service=cls.OAUTH_PROVIDER_NAME, 
                expires_at__gt=now()
            ).first()

            if token:
                logger.info(f"Using existing valid {cls.OAUTH_PROVIDER_NAME} token for user {user_id}")
                return token.access_token

            # If no valid token, check for a refresh token
            token = OAuthToken.objects.filter(
                user_id=user_id, 
                service=cls.OAUTH_PROVIDER_NAME, 
                refresh_token__isnull=False
            ).first()

            if token:
                logger.info(f"Refreshing {cls.OAUTH_PROVIDER_NAME} token for user {user_id}")
                refreshed_token = cls.refresh_access_token(token)

                if refreshed_token and refreshed_token.access_token:
                    return refreshed_token.access_token

                logger.error(f"Failed to refresh {cls.OAUTH_PROVIDER_NAME} token for user {user_id}")
            
            # If refresh token is not available, log error and request reauthorization
            logger.warning(f"No valid {cls.OAUTH_PROVIDER_NAME} token or refresh token found for user {user_id}. Reauthorization required.")
            raise RuntimeError(f"No valid {cls.OAUTH_PROVIDER_NAME} token. Please reauthorize.")

        except Exception as e:
            logger.error(f"Failed to get {cls.OAUTH_PROVIDER_NAME} token for user {user_id}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get {cls.OAUTH_PROVIDER_NAME} token: {e}")


    @classmethod
    def get_authorization_url(cls, state=None):
        """
        Generate the OAuth authorization URL dynamically based on the provider.

        Returns:
            str: The authorization URL.
        """
        if not all([cls.OAUTH_CLIENT_ID, cls.OAUTH_BASE_URL, cls.OAUTH_AUTH_ENDPOINT, cls.OAUTH_SCOPE, cls.OAUTH_PROVIDER_NAME]):
            raise RuntimeError("OAuth configuration missing. Ensure required class variables are set.")

        state = state or secrets.token_urlsafe(16)
        redirect_uri = cls.get_redirect_uri()

        params = {
            "response_type": "code",
            "client_id": cls.OAUTH_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": cls.OAUTH_SCOPE,
            "state": state,
        }

        params.update(cls.EXTRA_AUTH_PARAMS)

        auth_url = f"{cls.OAUTH_BASE_URL}{cls.OAUTH_AUTH_ENDPOINT}?" + "&".join(f"{key}={value}" for key, value in params.items())
        return auth_url

    @classmethod
    def exchange_authorization_code(cls, code, user_id="default"):
        """
        Exchange the authorization code for an access and refresh token.

        Args:
            code (str): The authorization code.
            user_id (str): Identifier for the user.

        Returns:
            str: The access token.
        """

        logger.info(f"Exchanging authorization code for {cls.OAUTH_PROVIDER_NAME} tokens")

        if not cls.OAUTH_CLIENT_ID or not cls.OAUTH_CLIENT_SECRET or not cls.OAUTH_TOKEN_ENDPOINT:
            raise RuntimeError("OAuth credentials missing in subclass.")

        if not code:
            raise RuntimeError("Authorization code not provided.")

        payload = {
            "code": code,
            "client_id": cls.OAUTH_CLIENT_ID,
            "client_secret": cls.OAUTH_CLIENT_SECRET,
            "redirect_uri": cls.get_redirect_uri(),
            "grant_type": "authorization_code",
        }

        logger.info(f"Requesting tokens from {cls.OAUTH_PROVIDER_NAME}")
        logger.debug(f"Payload: {payload}")
        response = requests.post(f"{cls.OAUTH_BASE_URL}{cls.OAUTH_TOKEN_ENDPOINT}", data=payload)
        response.raise_for_status()

        logger.info(f"Received response from {cls.OAUTH_PROVIDER_NAME}")
        logger.debug(f"Response: {response.json()}")

        data = response.json()

        if "access_token" not in data or "expires_in" not in data:
            raise RuntimeError(f"Unexpected response format: {data}")

        token_type = data.get("token_type", "Bearer")

        logger.debug(f"Saving {cls.OAUTH_PROVIDER_NAME} token for user {user_id}")
        return cls.save_or_update_token(
            user_id=user_id,
            service=cls.OAUTH_PROVIDER_NAME,
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_in=data["expires_in"],
            token_type=token_type,
        )

    @classmethod
    def refresh_access_token(cls, token):
        """
        Refresh the OAuth access token using the stored refresh token.

        Args:
            token (AUTH_TOKEN_MODEL): The token model instance.

        Returns:
            Updated AUTH_TOKEN_MODEL instance.
        """
        if not cls.OAUTH_CLIENT_ID or not cls.OAUTH_CLIENT_SECRET:
            raise RuntimeError("OAuth credentials missing in subclass.")

        if not token.refresh_token:
            raise RuntimeError("Refresh token missing. Reauthorization required.")

        payload = {
            "refresh_token": token.refresh_token,
            "client_id": cls.OAUTH_CLIENT_ID,
            "client_secret": cls.OAUTH_CLIENT_SECRET,
            "grant_type": "refresh_token",
        }

        response = requests.post(f"{cls.OAUTH_BASE_URL}{cls.OAUTH_TOKEN_ENDPOINT}", data=payload)
        response.raise_for_status()

        data = response.json()

        if "access_token" not in data or "expires_in" not in data:
            raise RuntimeError(f"Unexpected response format: {data}")

        return cls.save_or_update_token(
            user_id=token.user_id,
            service=cls.OAUTH_PROVIDER_NAME,
            access_token=data["access_token"],
            refresh_token=None,
            expires_in=data["expires_in"],
        )

    @classmethod
    def revoke_token(cls, access_token):
        """
        Revoke an access token.

        Args:
            access_token (str): The access token to revoke.
        """
        if not cls.OAUTH_REVOKE_ENDPOINT:
            raise RuntimeError("OAuth revoke endpoint not defined in subclass.")

        url = f"{cls.OAUTH_BASE_URL}{cls.OAUTH_REVOKE_ENDPOINT}"
        payload = {"token": access_token}

        response = requests.post(url, data=payload)
        if response.status_code == 200:
            logger.info("OAuth token revoked successfully.")
        else:
            logger.error(f"Failed to revoke token: {response.json()}")

    @classmethod
    def save_or_update_token(cls, user_id, service, access_token, refresh_token, expires_in, token_type="Bearer"):
        """
        Save or update the OAuth token in the database.

        Args:
            user_id (str): The user ID associated with the token.
            service (str): The OAuth service provider (Google, Zoho, etc.).
            access_token (str): The new access token.
            refresh_token (str): The new refresh token (if provided).
            expires_in (int): Token expiry time in seconds.
            token_type (str): The type of token (default: "Bearer").

        Returns:
            Updated AUTH_TOKEN_MODEL instance.
        """

        logger.debug(f"Saving {service} token for user {user_id}")

        OAuthToken = cls().AUTH_TOKEN_MODEL
        if not OAuthToken:
            raise RuntimeError("AUTH_TOKEN_MODEL is not defined in subclass.")

        logger.debug(f"Token expires in {expires_in} seconds")
        # Ensure we fetch ONLY the token for the correct service
        existing_token = OAuthToken.objects.filter(user_id=user_id, service=service).first()

        logger.debug(f"Existing token: {existing_token}")
        # Preserve refresh_token if it's missing in the new response
        if not refresh_token and existing_token:
            refresh_token = existing_token.refresh_token

        token, created = OAuthToken.objects.update_or_create(
            user_id=user_id,
            service=service,  # Ensure service is used for filtering
            defaults={
                "access_token": access_token,
                "refresh_token": refresh_token,  # Preserves correct refresh token
                "expires_at": now() + datetime.timedelta(seconds=expires_in - 60),
                "token_type": token_type,
            },
        )
        logger.debug(f"Token created: {created}")
        return token

    @classmethod
    def get_redirect_uri(cls, request=None):
        """
        Generate the redirect URI dynamically.

        Args:
            request (HttpRequest, optional): The Django request object.

        Returns:
            str: The absolute redirect URI.
        """
        if not cls.OAUTH_PROVIDER_NAME:
            raise RuntimeError("OAUTH_PROVIDER_NAME must be defined in the subclass.")

        # Get the relative path for the OAuth callback
        relative_path = reverse(f"{cls.APP_NAME}:{cls.OAUTH_PROVIDER_NAME}_callback")

        logger.info(f"Building redirect URI for {cls.OAUTH_PROVIDER_NAME} callbackw with relative path: {relative_path}")

        # 1️⃣ If request is provided, use it to build the absolute URI
        if request:
            logger.info("Request is available. Building absolute URI")
            return request.build_absolute_uri(relative_path)

        # 2️⃣ If request is NOT available, use the SITE_URL from settings
        base_url = get_setting("SITE_URL")
        if not base_url:
            raise RuntimeError("SITE_URL setting is not defined.")
        return f"{base_url}{relative_path}"
    
