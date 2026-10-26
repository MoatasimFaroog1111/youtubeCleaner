"""
main_guardian.py - المحرك الرئيسي لنظام Kids Guardian
نسخة متوافقة مع Google OAuth + cleaner.py + educator.py
"""

import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

LOG_PATH = os.getenv("LOG_PATH", "/home/moatasim/youtube_cleaner/kids_guardian.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def check_required_files():
    """
    التحقق من وجود الملفات الأساسية قبل التشغيل
    """
    required_files = [
        os.path.join(BASE_DIR, ".env"),
        os.path.join(BASE_DIR, "auth_google.py"),
        os.path.join(BASE_DIR, "cleaner.py"),
        os.path.join(BASE_DIR, "educator.py"),
    ]

    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        for file_path in missing:
            logging.error(f"❌ ملف مفقود: {file_path}")
        return False
    return True


def run_daily_protection():
    """
    تشغيل دورة الحماية اليومية
    """
    logging.info("=" * 60)
    logging.info(f"🚀 بدء الدورة اليومية: {datetime.now()}")
    logging.info("=" * 60)

    # 1) طبقة التنظيف / التحقق من الاتصال
    try:
        from cleaner import clear_watch_history_oauth
        ok = clear_watch_history_oauth()
        logging.info(f"🧹 نتيجة cleaner: {'نجح ✅' if ok else 'فشل ❌'}")
    except Exception as e:
        logging.error(f"❌ Cleaner error: {e}")

    # 2) اكتشاف المحتوى التعليمي
    try:
        from educator import run_educational_discovery
        videos = run_educational_discovery()
        logging.info(f"🎓 عدد الفيديوهات التعليمية المكتشفة: {len(videos)}")
    except Exception as e:
        logging.error(f"❌ Educator error: {e}")

    logging.info(f"✅ انتهاء الدورة: {datetime.now()}")
    logging.info("=" * 60)


if __name__ == "__main__":
    print("🛡️ Kids Guardian v3 — Google OAuth 2.0")

    if not check_required_files():
        print("❌ هناك ملفات ناقصة. راجع kids_guardian.log")
        raise SystemExit(1)

    # تشغيل مباشر مرة واحدة ثم الانتظار 24 ساعة
    run_daily_protection()
    print(f"💤 الدورة التالية بعد 24 ساعة [{datetime.now().strftime('%H:%M')}]")

    while True:
        time.sleep(86400)
        run_daily_protection()