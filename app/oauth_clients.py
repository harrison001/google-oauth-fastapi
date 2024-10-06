from httpx_oauth.clients.linkedin import LinkedInOAuth2
from httpx_oauth.clients.facebook import FacebookOAuth2
from app.config import LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET

linkedin_oauth_client = LinkedInOAuth2(
    client_id=LINKEDIN_CLIENT_ID,
    client_secret=LINKEDIN_CLIENT_SECRET,
    scopes=["openid", "profile", "email"]  # 使用 OpenID Connect 标准的 scopes
)

facebook_oauth_client = FacebookOAuth2(
    client_id=FACEBOOK_CLIENT_ID,
    client_secret=FACEBOOK_CLIENT_SECRET,
    scopes=["email", "public_profile"]
)

# 移除 Twitter 相关代码