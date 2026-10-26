"""
auth_google.py - المصادقة الكاملة مع Google OAuth 2.0
مناسب لـ PythonAnywhere وبيئات الطرفية
"""

import os
import logging
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

LOG_PATH = os.getenv('LOG_PATH', '/home/moatasim/youtube_cleaner/kids_guardian.log')
CREDENTIALS_FILE = os.path.join(BASE_DIR, os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json'))
TOKEN_FILE = os.path.join(BASE_DIR, os.getenv('GOOGLE_TOKEN_FILE', 'token.json'))

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

SCOPES = [
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtube.readonly',
]


def get_google_credentials() -> Credentials:
    creds = None

    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            logging.info("✅ تم تحميل token.json")
        except Exception as e:
            logging.warning(f"⚠️ تعذر تحميل token.json: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logging.info("🔄 تم تجديد التوكن تلقائياً")
            except Exception as e:
                logging.warning(f"⚠️ فشل تجديد التوكن: {e}")
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"❌ ملف credentials.json غير موجود في: {CREDENTIALS_FILE}\n"
                    "📌 حمّله من: console.cloud.google.com → APIs & Services → Credentials"
                )

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)

            # وضعان:
            # 1) run_local_server (افتراضي) — للمستخدم على جهازه المحلي، يفتح المتصفح.
            # 2) يدوي (AUTH_MODE=manual) — لخادم بعيد: يطبع رابط، تلصق الكود بعد التفويض.
            if os.getenv("AUTH_MODE", "").lower() == "manual":
                flow.redirect_uri = "http://127.0.0.1:8080/"
                auth_url, _ = flow.authorization_url(
                    prompt="consent",
                    access_type="offline",
                    include_granted_scopes="true",
                )
                print("\n" + "=" * 60)
                print("🔐 افتح الرابط التالي في متصفحك وفوّض الحساب:")
                print(auth_url)
                print("\n⚠️ بعد التفويض سيعيدك المتصفح إلى http://127.0.0.1:8080/?code=...")
                print("   انسخ قيمة `code` كاملة من شريط العنوان والصقها هنا.")
                print("=" * 60)
                code = input("🔑 الصق الكود: ").strip()
                flow.fetch_token(code=code)
                creds = flow.credentials
            else:
                creds = flow.run_local_server(
                    host="localhost",
                    port=0,
                    authorization_prompt_message="🔐 يرجى زيارة هذا الرابط في المتصفح وتفويض الحساب:",
                    success_message="✅ تم التفويض بنجاح! يمكنك إغلاق هذه النافذة.",
                    open_browser=True,
                )
            logging.info("✅ تم تسجيل الدخول بنجاح عبر OAuth")

        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
        logging.info(f"💾 تم حفظ token.json في: {TOKEN_FILE}")

    return creds


def get_authenticated_youtube():
    from googleapiclient.discovery import build
    creds = get_google_credentials()
    youtube = build('youtube', 'v3', credentials=creds)
    logging.info("🎬 YouTube API client جاهز")
    return youtube


if __name__ == "__main__":
    print("🔐 اختبار المصادقة مع Google...")
    try:
        youtube = get_authenticated_youtube()
        response = youtube.channels().list(part='snippet', mine=True).execute()

        if response.get('items'):
            channel = response['items'][0]['snippet']
            print(f"✅ تم تسجيل الدخول بنجاح")
            print(f"📺 اسم القناة: {channel.get('title', 'غير معروف')}")
        else:
            print("⚠️ تم تسجيل الدخول لكن لم يتم العثور على قناة YouTube مرتبطة بهذا الحساب")

    except Exception as e:
        print(f"❌ خطأ: {e}")