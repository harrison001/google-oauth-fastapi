from httpx_oauth.clients.linkedin import LinkedInOAuth2
from app.config import LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET

linkedin_oauth_client = LinkedInOAuth2(
    client_id=LINKEDIN_CLIENT_ID,
    client_secret=LINKEDIN_CLIENT_SECRET,
    scopes=["openid", "profile", "email"]  # 使用 OpenID Connect 标准的 scopes
)