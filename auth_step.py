"""مصادقة Google OAuth على مرحلتين (مناسبة لخادم بعيد + Telegram).

المرحلة 1:  python auth_step.py url    -> يطبع رابط التفويض
المرحلة 2:  AUTH_CODE=<code> python auth_step.py code  -> يحفظ token.json
"""
import os
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly",
]

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

mode = sys.argv[1] if len(sys.argv) > 1 else "url"

flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
flow.redirect_uri = "http://localhost"

if mode == "url":
    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline",
        include_granted_scopes="true",
    )
    print(auth_url)

elif mode == "code":
    code = os.environ.get("AUTH_CODE", "").strip()
    if not code:
        print("ERROR: AUTH_CODE is empty")
        sys.exit(1)
    flow.fetch_token(code=code)
    with open(TOKEN_FILE, "w") as f:
        f.write(flow.credentials.to_json())
    print("TOKEN_SAVED:", TOKEN_FILE)
