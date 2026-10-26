"""
educator.py - اكتشاف محتوى تعليمي آمن وتوجيه الحساب نحوه
نسخة مصححة ومتوافقة مع Google OAuth وتدعم تعلّم الأطفال تحت 10 سنوات
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.errors import HttpError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

LOG_PATH = os.getenv("LOG_PATH", "/home/moatasim/youtube_cleaner/kids_guardian.log")
EDU_LOG_PATH = os.getenv("EDU_LOG_PATH", "/home/moatasim/youtube_cleaner/educational_log.json")
PLAYLIST_ID = os.getenv("YT_PLAYLIST_ID", "").strip()

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
os.makedirs(os.path.dirname(EDU_LOG_PATH), exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

TRUSTED_EDUCATIONAL_CHANNELS = {
    "UCtlcIZVBdFPSAtCoNZsTusg": "Learn with Zakaria - تعلم مع زكريا",
    "UCmK69Z1mH_74G-hF-R1533A": "51Talk",
    "UCWIdqSQekeGmUWlSFeCiEnA": "Osratouna TV - قناة أسرتنا",
    "UCk1E19G6dM6tS3n7i51876g": "One 4 Kids (Zaky)",
    "UC9T7P4WqY57b32wR31v0rOg": "Numberblocks",
    "UC_s74qN3wR9g7-18Z7nN7-g": "Alphablocks",
    "UCxS359o7e18146FmQe1yKMA": "Siraj - سراج",
    "UC4a-Gbdw7vOaccHmFo40b9g": "Khan Academy Kids",
    "UCsooa4yRKGN_zEE8iknghZA": "TED-Ed",
}

EDUCATIONAL_QUERIES = {
    "english_for_arabic_speakers": [
        "تعلم اللغة الانجليزية للاطفال زكريا",
        "english alphabets for arabic speaking children",
        "تعليم الانجليزية للمبتدئين الاطفال كرتون"
    ],
    "arabic_language": [
        "تعليم الحروف العربية للأطفال زكريا",
        "تعليم اللغة العربية للاطفال كرتون براعم",
        "قصص الحروف العربية للاطفال"
    ],
    "mathematics": [
        "تعليم الحساب والارقام للاطفال زكريا",
        "Numberblocks counting and math for kids",
        "الجمع والطرح للاطفال كرتون"
    ],
    "general_morals": [
        "الاداب العامة والاخلاق للاطفال كرتون",
        "good manners and healthy habits for kids cartoon",
        "الاخلاق الحميدة والامانة للاطفال"
    ],
    "islamic_morals": [
        "الاداب الاسلامية والاذكار للاطفال زكريا",
        "قصص الانبياء والقران الكريم للاطفال كرتون",
        "تعليم الصلاة والوضوء للاطفال كرتون"
    ],
    "modern_skills_and_knowledge": [
        "العلوم المبسطة للاطفال كرتون زكريا",
        "solar system and space for kids cartoon",
        "coding scratch for kids animation"
    ]
}

HARMFUL_KEYWORDS = [
    "scary", "horror", "violence", "fight", "gun", "killing", "adult",
    "spooky", "creepy", "ghost", "death", "blood", "monster", "prank",
    "kiss", "boyfriend", "girlfriend", "crying", "police", "jail", "thief",
    "bad word", "مخيف", "رعب", "عنف", "قتال", "سلاح", "موت", "دم", "وحش", "شرطة"
]


def search_educational_videos(youtube, query: str, max_results: int = 3) -> list:
    try:
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            safeSearch="strict",
            videoEmbeddable="true",
            videoDuration="medium",
            maxResults=max_results,
            order="relevance",
            videoCaption="closedCaption",
        )
        response = request.execute()

        videos = []
        for item in response.get("items", []):
            title = item["snippet"]["title"]
            title_lower = title.lower()

            if any(word in title_lower for word in HARMFUL_KEYWORDS):
                logging.warning(f"⚠️ تم تجاهل فيديو مشبوه: {title}")
                continue

            videos.append({
                "video_id": item["id"]["videoId"],
                "title": title,
                "channel": item["snippet"]["channelTitle"],
                "url": f"https://youtu.be/{item['id']['videoId']}"
            })

        return videos

    except HttpError as e:
        logging.error(f"❌ خطأ بحث YouTube API: {e}")
        return []
    except Exception as e:
        logging.error(f"❌ خطأ عام في search_educational_videos: {e}")
        return []


def get_trusted_channel_videos(youtube, channel_id: str, max_results: int = 2) -> list:
    try:
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            type="video",
            order="date",
            maxResults=max_results,
            safeSearch="strict",
        )
        response = request.execute()

        return [
            {
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "url": f"https://youtu.be/{item['id']['videoId']}"
            }
            for item in response.get("items", [])
        ]

    except HttpError as e:
        logging.error(f"❌ خطأ قناة موثوقة {channel_id}: {e}")
        return []
    except Exception as e:
        logging.error(f"❌ خطأ عام في get_trusted_channel_videos: {e}")
        return []


def rate_educational_video(youtube, video_id: str) -> bool:
    try:
        youtube.videos().rate(id=video_id, rating="like").execute()
        logging.info(f"👍 تم عمل Like للفيديو: {video_id}")
        return True
    except HttpError as e:
        logging.error(f"❌ خطأ تقييم الفيديو {video_id}: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ خطأ عام في rate_educational_video: {e}")
        return False


def add_to_child_playlist(youtube, video_id: str) -> bool:
    if not PLAYLIST_ID or PLAYLIST_ID == "YOUR_CHILD_PLAYLIST_ID":
        logging.info("ℹ️ لم يتم تحديد PLAYLIST_ID، تم تخطي الإضافة إلى قائمة التشغيل.")
        return False

    try:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": PLAYLIST_ID,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        ).execute()
        logging.info(f"➕ تم إضافة الفيديو إلى القائمة: {video_id}")
        return True
    except HttpError as e:
        logging.error(f"❌ خطأ إضافة الفيديو للقائمة {video_id}: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ خطأ عام في add_to_child_playlist: {e}")
        return False


def log_educational_session(videos: list, category: str):
    try:
        if os.path.exists(EDU_LOG_PATH):
            with open(EDU_LOG_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []
    except (json.JSONDecodeError, OSError):
        history = []

    history.append({
        "date": datetime.now().isoformat(),
        "category": category,
        "videos": videos,
    })

    history = history[-30:]

    with open(EDU_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def run_educational_discovery():
    from auth_google import get_authenticated_youtube

    youtube = get_authenticated_youtube()
    all_videos = []

    logging.info("=== بدء اكتشاف المحتوى التعليمي ===")

    for category, queries in EDUCATIONAL_QUERIES.items():
        for query in queries:
            videos = search_educational_videos(youtube, query, max_results=3)

            for video in videos:
                rate_educational_video(youtube, video["video_id"])
                add_to_child_playlist(youtube, video["video_id"])

            all_videos.extend(videos)
            log_educational_session(videos, category)
            logging.info(f"✅ {category}: {len(videos)} فيديو لـ '{query}'")

    for channel_id, channel_name in list(TRUSTED_EDUCATIONAL_CHANNELS.items())[:4]:
        videos = get_trusted_channel_videos(youtube, channel_id, max_results=2)

        for video in videos:
            rate_educational_video(youtube, video["video_id"])
            add_to_child_playlist(youtube, video["video_id"])

        all_videos.extend(videos)
        logging.info(f"📺 {channel_name}: {len(videos)} فيديو")

    logging.info(f"=== إجمالي الفيديوهات التعليمية المكتشفة: {len(all_videos)} ===")
    return all_videos


if __name__ == "__main__":
    videos = run_educational_discovery()
    print(f"تم اكتشاف {len(videos)} فيديو تعليمي")
    for video in videos[:5]:
        print(f"- {video['title']} ({video['channel']})")