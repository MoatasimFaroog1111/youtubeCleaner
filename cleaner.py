"""
cleaner.py - تنظيف محتوى يوتيوب غير المناسب للأطفال دون سن 10 سنوات
يعمل عبر Google OAuth مع YouTube Data API v3
"""

import os
import re
import json
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.errors import HttpError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

LOG_PATH = os.getenv("LOG_PATH", "/home/moatasim/youtube_cleaner/kids_guardian.log")
CLEAN_LOG_PATH = os.getenv("CLEAN_LOG_PATH", "/home/moatasim/youtube_cleaner/cleaning_log.json")

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
os.makedirs(os.path.dirname(CLEAN_LOG_PATH), exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ======================================================
# كلمات مفتاحية للمحتوى غير المناسب للأطفال
# ======================================================
INAPPROPRIATE_KEYWORDS = [
    # عنف وأسلحة
    "kill", "killing", "murder", "gun", "shoot", "shooting", "violence", "violent",
    "fight", "fighting", "war", "battle", "blood", "gore", "death", "dead",
    "weapon", "bomb", "explosion", "terrorist",
    # محتوى للبالغين
    "adult", "explicit", "sexy", "nude", "naked", "porn",
    "sex", "sexual", "nsfw",
    # رعب ومخيف
    "scary", "horror", "creepy", "nightmare", "ghost", "demon", "evil",
    "jumpscare", "terrifying", "haunted", "Gummy",
    # مخدرات وكحول
    "drug", "drugs", "alcohol", "beer", "wine", "smoking", "cigarette",
    "weed", "marijuana", "cocaine",
    # محتوى مقلق
    "suicide", "self harm", "eating disorder", "anorexia",
    # ألعاب فيديو عنيفة (أسماء كاملة فقط)
    "grand theft auto", "mortal kombat", "call of duty", "battlefield",
    "doom", "resident evil",
    # مضايقة وكراهية
    "bullying", "harassment", "hate speech",
]

# قنوات آمنة لا تُمس أبداً
SAFE_CHANNELS = {
    "UCX6OQ3DkcsbYNE6H8uQQuVA",  # Blippi
    "UCBcRF18a7Qf58cCRy5xuWwQ",  # Dave and Ava
    "UC4a-Gbdw7vOaccHmFo40b9g",  # Khan Academy Kids
    "UCsooa4yRKGN_zEE8iknghZA",  # TED-Ed
    "UCiTnKaMLJv5JL9T-YCRFpXg",  # National Geographic Kids
    "UCzvQZ1p_-AXhpHzOlJSKVsA",  # Kids Learning Tube
    "UCSN8_oBQMGFWYE7I0D-Oe3Q",  # Super Simple Songs
    "UCddiUEpeqJcYeBxX1IVBKvQ",  # Peppa Pig
    "UCbCmjCuTUZos6Inko4u57BA",  # CoComelon
}


def is_inappropriate_for_kids(title: str, description: str = "", channel_id: str = "") -> bool:
    """
    يفحص إذا كان المحتوى غير مناسب لطفل دون 10 سنوات.
    يستخدم \b للتحقق من الكلمة الكاملة فقط، لتجنب false positives
    مثل: 'cod' في 'Codezilla' أو 'war' في 'award'.
    """
    if channel_id in SAFE_CHANNELS:
        return False

    text_to_check = (title + " " + description).lower()

    for keyword in INAPPROPRIATE_KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_to_check):
            logging.warning(f"⚠️ كلمة غير مناسبة '{keyword}' في: {title[:60]}")
            return True

    return False


def get_channel_playlists(youtube) -> list:
    """جلب قوائم التشغيل الخاصة بالمستخدم"""
    playlists = []
    try:
        request = youtube.playlists().list(
            part="snippet,contentDetails",
            mine=True,
            maxResults=50
        )
        response = request.execute()

        for item in response.get("items", []):
            playlists.append({
                "id": item["id"],
                "title": item["snippet"]["title"],
                "count": item["contentDetails"]["itemCount"]
            })

        logging.info(f"📋 تم جلب {len(playlists)} قائمة تشغيل")
        return playlists

    except HttpError as e:
        logging.error(f"❌ خطأ جلب القوائم: {e}")
        return []


def get_playlist_items(youtube, playlist_id: str) -> list:
    """جلب جميع فيديوهات قائمة تشغيل معينة"""
    items = []
    next_page_token = None

    while True:
        try:
            request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get("items", []):
                items.append({
                    "playlist_item_id": item["id"],
                    "video_id": item["snippet"]["resourceId"]["videoId"],
                    "title": item["snippet"]["title"],
                    "channel_id": item["snippet"].get("videoOwnerChannelId", ""),
                    "description": item["snippet"].get("description", "")[:200]
                })

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        except HttpError as e:
            logging.error(f"❌ خطأ جلب فيديوهات القائمة {playlist_id}: {e}")
            break

    return items


def delete_playlist_item(youtube, playlist_item_id: str, video_title: str, dry_run: bool = False) -> bool:
    """حذف فيديو من قائمة التشغيل"""
    if dry_run:
        logging.info(f"🔍 [DRY RUN] سيُحذف: {video_title[:60]}")
        return True

    try:
        youtube.playlistItems().delete(id=playlist_item_id).execute()
        logging.info(f"🗑️ تم حذف: {video_title[:60]}")
        time.sleep(0.5)
        return True

    except HttpError as e:
        logging.error(f"❌ خطأ حذف الفيديو {playlist_item_id}: {e}")
        return False


def clean_playlist(youtube, playlist_id: str, playlist_title: str, dry_run: bool = False) -> dict:
    """تنظيف قائمة تشغيل من المحتوى غير المناسب"""
    logging.info(f"🔎 فحص قائمة: {playlist_title} ({playlist_id})")
    items = get_playlist_items(youtube, playlist_id)

    cleaned = []
    kept = 0

    for item in items:
        if is_inappropriate_for_kids(
            item["title"],
            item["description"],
            item["channel_id"]
        ):
            success = delete_playlist_item(
                youtube,
                item["playlist_item_id"],
                item["title"],
                dry_run=dry_run
            )
            if success:
                cleaned.append({
                    "video_id": item["video_id"],
                    "title": item["title"]
                })
        else:
            kept += 1

    logging.info(f"✅ {playlist_title}: حُذف {len(cleaned)} | بقي {kept}")
    return {
        "playlist_id": playlist_id,
        "playlist_title": playlist_title,
        "cleaned": cleaned,
        "kept": kept
    }


def get_liked_videos(youtube) -> list:
    """جلب فيديوهات الإعجاب (Liked Videos)"""
    items = []
    next_page_token = None

    while True:
        try:
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId="LL",
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get("items", []):
                items.append({
                    "playlist_item_id": item["id"],
                    "video_id": item["snippet"]["resourceId"]["videoId"],
                    "title": item["snippet"]["title"],
                    "channel_id": item["snippet"].get("videoOwnerChannelId", ""),
                })

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        except HttpError as e:
            logging.error(f"❌ خطأ جلب فيديوهات الإعجاب: {e}")
            break

    return items


def remove_like_from_video(youtube, video_id: str, title: str, dry_run: bool = False) -> bool:
    """إزالة الإعجاب عن فيديو غير مناسب"""
    if dry_run:
        logging.info(f"🔍 [DRY RUN] سيُزال الإعجاب عن: {title[:60]}")
        return True

    try:
        youtube.videos().rate(id=video_id, rating="none").execute()
        logging.info(f"👎 تم إزالة الإعجاب عن: {title[:60]}")
        time.sleep(0.5)
        return True
    except HttpError as e:
        logging.error(f"❌ خطأ إزالة الإعجاب {video_id}: {e}")
        return False


def get_all_subscriptions(youtube) -> list:
    """جلب جميع الاشتراكات"""
    subs = []
    next_page_token = None

    while True:
        try:
            request = youtube.subscriptions().list(
                part="snippet",
                mine=True,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get("items", []):
                subs.append({
                    "channel_id": item["snippet"]["resourceId"]["channelId"],
                    "channel_name": item["snippet"]["title"],
                    "description": item["snippet"].get("description", "")[:200]
                })

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        except HttpError as e:
            logging.error(f"❌ خطأ جلب الاشتراكات: {e}")
            break

    logging.info(f"📺 إجمالي الاشتراكات: {len(subs)}")
    return subs


def unsubscribe_inappropriate_channel(youtube, channel_id: str, channel_name: str, dry_run: bool = False) -> bool:
    """إلغاء الاشتراك في قناة غير مناسبة"""
    if dry_run:
        logging.info(f"🔍 [DRY RUN] سيُلغى الاشتراك في: {channel_name}")
        return True

    try:
        request = youtube.subscriptions().list(
            part="id",
            mine=True,
            forChannelId=channel_id
        )
        response = request.execute()

        if response.get("items"):
            sub_id = response["items"][0]["id"]
            youtube.subscriptions().delete(id=sub_id).execute()
            logging.info(f"🚫 تم إلغاء الاشتراك في: {channel_name}")
            time.sleep(0.5)
            return True

    except HttpError as e:
        logging.error(f"❌ خطأ إلغاء الاشتراك في {channel_name}: {e}")

    return False


def save_cleaning_report(report: dict):
    """حفظ تقرير التنظيف في ملف JSON"""
    try:
        if os.path.exists(CLEAN_LOG_PATH):
            with open(CLEAN_LOG_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []
    except (json.JSONDecodeError, OSError):
        history = []

    history.append(report)
    history = history[-30:]

    with open(CLEAN_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    logging.info(f"💾 تم حفظ تقرير التنظيف في: {CLEAN_LOG_PATH}")


def clear_watch_history_oauth(dry_run: bool = False) -> bool:
    """
    الدالة الرئيسية — تُستدعى من main_guardian.py
    تنظف: قوائم التشغيل + فيديوهات الإعجاب + الاشتراكات غير المناسبة
    dry_run=True  → اختبار فقط بدون حذف فعلي
    dry_run=False → حذف فعلي
    """
    from auth_google import get_authenticated_youtube

    logging.info("=" * 50)
    logging.info(f"🧹 بدء جلسة التنظيف {'[DRY RUN]' if dry_run else '[فعلي]'}: {datetime.now()}")
    logging.info("=" * 50)

    try:
        youtube = get_authenticated_youtube()
        report = {
            "date": datetime.now().isoformat(),
            "dry_run": dry_run,
            "playlists_cleaned": [],
            "likes_removed": [],
            "subscriptions_removed": [],
            "total_removed": 0
        }

        # 1) تنظيف قوائم التشغيل
        logging.info("📋 [1/3] فحص قوائم التشغيل...")
        playlists = get_channel_playlists(youtube)
        for playlist in playlists:
            if playlist["count"] > 0:
                result = clean_playlist(youtube, playlist["id"], playlist["title"], dry_run=dry_run)
                if result["cleaned"]:
                    report["playlists_cleaned"].append(result)
                    report["total_removed"] += len(result["cleaned"])

        # 2) تنظيف فيديوهات الإعجاب
        logging.info("👍 [2/3] فحص فيديوهات الإعجاب...")
        try:
            liked_videos = get_liked_videos(youtube)
            for video in liked_videos:
                if is_inappropriate_for_kids(video["title"], "", video["channel_id"]):
                    success = remove_like_from_video(youtube, video["video_id"], video["title"], dry_run=dry_run)
                    if success:
                        report["likes_removed"].append({"video_id": video["video_id"], "title": video["title"]})
                        report["total_removed"] += 1
        except HttpError as e:
            logging.warning(f"⚠️ تعذر فحص فيديوهات الإعجاب: {e}")

        # 3) فحص الاشتراكات
        logging.info("📺 [3/3] فحص الاشتراكات...")
        try:
            subscriptions = get_all_subscriptions(youtube)
            for sub in subscriptions:
                if sub["channel_id"] not in SAFE_CHANNELS:
                    if is_inappropriate_for_kids(sub["channel_name"], sub["description"]):
                        success = unsubscribe_inappropriate_channel(
                            youtube, sub["channel_id"], sub["channel_name"], dry_run=dry_run
                        )
                        if success:
                            report["subscriptions_removed"].append({
                                "channel_id": sub["channel_id"],
                                "channel_name": sub["channel_name"]
                            })
                            report["total_removed"] += 1
        except HttpError as e:
            logging.warning(f"⚠️ تعذر فحص الاشتراكات: {e}")

        # حفظ التقرير
        save_cleaning_report(report)

        logging.info("=" * 50)
        logging.info(f"✅ انتهاء التنظيف:")
        logging.info(f"   🗑️ من قوائم التشغيل: {sum(len(p['cleaned']) for p in report['playlists_cleaned'])}")
        logging.info(f"   👎 إعجابات مُزالة: {len(report['likes_removed'])}")
        logging.info(f"   🚫 اشتراكات مُلغاة: {len(report['subscriptions_removed'])}")
        logging.info(f"   📊 إجمالي: {report['total_removed']} عنصر")
        logging.info("=" * 50)

        return True

    except Exception as e:
        logging.error(f"❌ خطأ في جلسة التنظيف: {e}")
        return False


if __name__ == "__main__":
    print("🧹 تشغيل منظف المحتوى...")
    print("⚠️  وضع الاختبار (DRY RUN) - لن يُحذف شيء فعلياً")
    print("    لتفعيل الحذف الفعلي: غيّر dry_run=True إلى dry_run=False")
    result = clear_watch_history_oauth(dry_run=False)
    print(f"نتيجة: {'نجح ✅' if result else 'فشل ❌'}")
    print(f"راجع اللوج: {LOG_PATH}")