"""
유튜브 채널 모니터링 → Notion 저장

실행 방법:
  python3 main.py            # 일반 실행 (resolved 채널 플레이리스트 수집)
  python3 main.py --search   # 미탐색 채널도 브랜드명 영상 검색 포함
  python3 main.py --setup    # 채널 ID 최초 탐색 (1회)
  python3 main.py --days 7   # 수집 기간 조정 (기본 1일)

API 할당량 (일일 10,000 units):
  resolved 채널  → playlistItems.list = 1 unit/채널
  unresolved 채널 → search.list       = 100 units/채널  (--search 시)
  영상 상세      → videos.list        = 1 unit/50개 (배치)
"""

from __future__ import annotations

import os
import json
import re
import sys
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path

warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv()

from googleapiclient.discovery import build
from notion_client import Client

from config import (
    MIN_VIEWS, MAX_SEARCH, MAX_PER_CHANNEL,
    PRIORITY_CHANNELS, MOTION_STUDIOS,
    ARTIST_LABEL_CHANNELS, BRAND_SIGNAL_KEYWORDS,
    EXCLUDE_PATTERNS, EXCLUDE_TAG_KEYWORDS,
    INDUSTRY_KEYWORDS, FORMAT_KEYWORDS, PURPOSE_KEYWORDS, TOPIC_KEYWORDS,
    SCORE_BASE, SCORE_PRIORITY_CHANNEL, SCORE_MOTION_STUDIO,
    SCORE_HIGH_QUALITY_FMT, SCORE_VIEWS_1M, SCORE_VIEWS_100K, SCORE_VIEWS_10K,
    SCORE_LIKES_RATIO_HIGH, SCORE_COMMENTS_RATIO, SCORE_RECENT,
    HIGH_QUALITY_FORMATS,
)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
NOTION_TOKEN    = os.getenv("NOTION_TOKEN")
DATABASE_ID     = os.getenv("NOTION_DATABASE_ID")

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
notion  = Client(auth=NOTION_TOKEN)

BASE_DIR    = Path(__file__).parent
CACHE_FILE  = BASE_DIR / "channel_cache.json"
SEEN_FILE   = BASE_DIR / "seen_videos.json"
CURSOR_FILE = BASE_DIR / "search_cursor.json"


# ─────────────────────────────────────────────
# 로컬 파일 캐시
# ─────────────────────────────────────────────

def load_cache() -> dict:
    return json.loads(CACHE_FILE.read_text("utf-8")) if CACHE_FILE.exists() else {}

def save_cache(cache: dict):
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), "utf-8")

def load_seen() -> set:
    return set(json.loads(SEEN_FILE.read_text("utf-8"))) if SEEN_FILE.exists() else set()

def save_seen(seen: set):
    SEEN_FILE.write_text(json.dumps(sorted(seen), ensure_ascii=False), "utf-8")

def load_cursor() -> int:
    return json.loads(CURSOR_FILE.read_text("utf-8")).get("index", 0) if CURSOR_FILE.exists() else 0

def save_cursor(index: int):
    CURSOR_FILE.write_text(json.dumps({"index": index}), "utf-8")


# ─────────────────────────────────────────────
# 채널 ID 탐색 (최초 1회)
# ─────────────────────────────────────────────

def resolve_channel_id(ch: dict, cache: dict) -> str | None:
    name = ch["name"]
    if name in cache:
        return cache[name]

    channel_id = None

    if "handle" in ch:
        try:
            res = youtube.channels().list(part="id", forHandle=ch["handle"]).execute()
            items = res.get("items", [])
            if items:
                channel_id = items[0]["id"]
        except Exception:
            pass

    if not channel_id:
        query = ch.get("search", ch["name"])
        try:
            res = youtube.search().list(
                part="snippet", q=query, type="channel", maxResults=5
            ).execute()
            best_id, best_subs = None, -1
            for item in res.get("items", []):
                cid = item["id"]["channelId"]
                detail = youtube.channels().list(
                    part="statistics", id=cid
                ).execute().get("items", [])
                if detail:
                    subs = int(detail[0]["statistics"].get("subscriberCount", 0))
                    if subs > best_subs:
                        best_subs, best_id = subs, cid
            channel_id = best_id
        except Exception:
            pass

    if channel_id:
        cache[name] = channel_id
        save_cache(cache)
    else:
        print(f"  [경고] 채널 ID 탐색 실패: {name}")

    return channel_id


def setup_channels():
    """최초 1회: 전체 채널 ID 탐색."""
    from channels import CHANNELS
    cache = load_cache()
    resolved = sum(1 for ch in CHANNELS if ch["name"] in cache)
    total = len(CHANNELS)
    print(f"\n채널 ID 탐색 시작 ({resolved}/{total}개 이미 캐시됨)\n")
    for i, ch in enumerate(CHANNELS, 1):
        if ch["name"] in cache:
            continue
        method = "handle" if "handle" in ch else "search"
        print(f"  [{i:03d}/{total}] {ch['name']} ({method})...", end=" ", flush=True)
        cid = resolve_channel_id(ch, cache)
        print(cid if cid else "실패")
    cached = sum(1 for ch in CHANNELS if ch["name"] in cache)
    print(f"\n완료: {cached}/{total}개 캐시됨 → {CACHE_FILE}\n")


# ─────────────────────────────────────────────
# 영상 수집
# ─────────────────────────────────────────────

def parse_duration(iso: str) -> str:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return iso
    h, mi, s = (int(x or 0) for x in m.groups())
    return f"{h}:{mi:02d}:{s:02d}" if h else f"{mi}:{s:02d}"


def is_brand_content(title: str, tags: list[str], channel_name: str = "") -> bool:
    """우선 채널·모션 스튜디오는 무조건 통과. 아티스트 레이블은 브랜드 신호 필요."""
    if channel_name in PRIORITY_CHANNELS or channel_name in MOTION_STUDIOS:
        return True
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return False
    tag_text = " ".join(tags).lower()
    if any(kw in tag_text for kw in EXCLUDE_TAG_KEYWORDS):
        return False
    if channel_name in ARTIST_LABEL_CHANNELS:
        title_lower = title.lower()
        if not any(kw in title_lower for kw in BRAND_SIGNAL_KEYWORDS):
            return False
    return True


def classify_industry(title: str, channel_name: str, tags: list[str], default: str) -> str:
    """제목·채널명·태그 키워드 점수로 산업군을 분류."""
    from config import INDUSTRY_MIGRATIONS
    if default in INDUSTRY_MIGRATIONS:
        default = INDUSTRY_MIGRATIONS[default]
    text = " ".join([title, channel_name] + tags).lower()
    scores = {
        ind: sum(1 for kw in kws if kw.lower() in text)
        for ind, kws in INDUSTRY_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else default


def classify_format(title: str, tags: list[str], duration: str) -> str:
    """제목·태그·영상 길이로 콘텐츠 포맷을 분류."""
    text = (title + " " + " ".join(tags)).lower()
    secs = _duration_to_seconds(duration)

    if "#shorts" in text or "#Shorts" in title:
        return "숏폼/릴스형"
    if 0 < secs <= 70:
        return "TVC/광고 영상" if any(kw in text for kw in ["광고", "tvc", " cf "]) else "숏폼/릴스형"

    for fmt, keywords in FORMAT_KEYWORDS.items():
        if fmt == "숏폼/릴스형":
            continue
        if any(kw.lower() in text for kw in keywords):
            return fmt

    if secs >= 2400:
        return "팟캐스트/라디오형"
    if secs >= 900:
        return "뉴스/분석"

    return "기타"


def classify_topic(title: str, tags: list[str]) -> str:
    """제목·태그 키워드로 주제/컨셉을 분류."""
    text = (title + " " + " ".join(tags)).lower()
    scores = {
        topic: sum(1 for kw in kws if kw.lower() in text)
        for topic, kws in TOPIC_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "기타"


def classify_purpose(title: str, tags: list[str]) -> str:
    """제목·태그 키워드로 영상 목적을 분류."""
    text = (title + " " + " ".join(tags)).lower()
    scores = {
        purpose: sum(1 for kw in kws if kw.lower() in text)
        for purpose, kws in PURPOSE_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "기타"


def _duration_to_seconds(duration: str) -> int:
    parts = duration.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except ValueError:
        pass
    return 0


def calculate_reference_score(video: dict, channel_name: str, fmt: str) -> int:
    """레퍼런스 품질 점수 계산 (0–100)."""
    score = SCORE_BASE

    if channel_name in MOTION_STUDIOS:
        score += SCORE_MOTION_STUDIO
    elif channel_name in PRIORITY_CHANNELS:
        score += SCORE_PRIORITY_CHANNEL

    if fmt in HIGH_QUALITY_FORMATS:
        score += SCORE_HIGH_QUALITY_FMT

    views = video.get("views", 0)
    if views >= 1_000_000:
        score += SCORE_VIEWS_1M
    elif views >= 100_000:
        score += SCORE_VIEWS_100K
    elif views >= 10_000:
        score += SCORE_VIEWS_10K

    if views > 0:
        likes    = video.get("likes", 0)
        comments = video.get("comments", 0)
        if likes / views > 0.05:
            score += SCORE_LIKES_RATIO_HIGH
        if comments / views > 0.01:
            score += SCORE_COMMENTS_RATIO

    try:
        pub_str = video.get("published", "")
        if pub_str:
            pub = datetime.fromisoformat(pub_str)
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            days_old = (datetime.now(timezone.utc) - pub).days
            if days_old < 30:
                score += SCORE_RECENT
    except Exception:
        pass

    return min(100, score)


def generate_collection_reason(channel_name: str, fmt: str, score: int) -> str:
    """수집 사유 자동 생성."""
    reasons = []
    if channel_name in MOTION_STUDIOS:
        reasons.append(f"모션그래픽 스튜디오")
    elif channel_name in PRIORITY_CHANNELS:
        reasons.append(f"우선 수집 채널")
    if fmt in HIGH_QUALITY_FORMATS:
        reasons.append(f"고품질 포맷 ({fmt})")
    if score >= 80:
        reasons.append("고점수 레퍼런스")
    if not reasons:
        reasons.append(f"채널 모니터링")
    return " · ".join(reasons)


def fetch_playlist_video_ids(channel_id: str, since: datetime, seen: set) -> list[str]:
    """공식 채널 업로드 플레이리스트 조회. 1 unit/채널."""
    playlist_id = "UU" + channel_id[2:]
    new_ids = []
    try:
        res = youtube.playlistItems().list(
            part="contentDetails", playlistId=playlist_id, maxResults=MAX_PER_CHANNEL
        ).execute()
        for item in res.get("items", []):
            cd  = item["contentDetails"]
            vid = cd["videoId"]
            pub = cd.get("videoPublishedAt", "")
            if not pub or vid in seen:
                continue
            pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            if pub_dt >= since:
                new_ids.append(vid)
    except Exception as e:
        print(f"  [오류] 플레이리스트 조회 실패 ({channel_id}): {e}")
    return new_ids


def search_brand_video_ids(brand_name: str, since: datetime, seen: set) -> list[str]:
    """브랜드명으로 영상 검색. 100 units/채널. --search 모드 전용."""
    new_ids = []
    try:
        res = youtube.search().list(
            part="id",
            q=brand_name,
            publishedAfter=since.strftime("%Y-%m-%dT%H:%M:%SZ"),
            order="viewCount",
            type="video",
            maxResults=10,
        ).execute()
        for item in res.get("items", []):
            vid = item["id"]["videoId"]
            if vid not in seen:
                new_ids.append(vid)
    except Exception as e:
        print(f"  [오류] 영상 검색 실패 ({brand_name}): {e}")
    return new_ids


def fetch_video_details_batch(video_ids: list[str]) -> list[dict]:
    """videos.list 배치 조회. 1 unit/50개."""
    results = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        try:
            res = youtube.videos().list(
                part="snippet,statistics,contentDetails", id=",".join(batch)
            ).execute()
            for item in res.get("items", []):
                snip  = item["snippet"]
                stats = item.get("statistics", {})
                results.append({
                    "id":         item["id"],
                    "title":      snip["title"],
                    "channel_id": snip["channelId"],
                    "published":  snip["publishedAt"][:10],
                    "views":      int(stats.get("viewCount", 0)),
                    "likes":      int(stats.get("likeCount", 0)),
                    "comments":   int(stats.get("commentCount", 0)),
                    "duration":   parse_duration(item["contentDetails"]["duration"]),
                    "url":        f"https://www.youtube.com/watch?v={item['id']}",
                    "tags":       snip.get("tags", []),
                })
        except Exception as e:
            print(f"  [오류] 영상 상세 조회 실패: {e}")
    return results


def fetch_channel_subs(channel_ids: list[str]) -> dict[str, int]:
    """channel_id → 구독자수. channels.list 배치 조회. 1 unit/50개."""
    result: dict[str, int] = {}
    unique_ids = list(set(channel_ids))
    for i in range(0, len(unique_ids), 50):
        batch = unique_ids[i : i + 50]
        try:
            res = youtube.channels().list(
                part="statistics", id=",".join(batch)
            ).execute()
            for item in res.get("items", []):
                result[item["id"]] = int(
                    item["statistics"].get("subscriberCount", 0)
                )
        except Exception as e:
            print(f"  [오류] 구독자수 조회 실패: {e}")
    return result


# ─────────────────────────────────────────────
# Notion 저장
# ─────────────────────────────────────────────

def thumbnail_url(video_id: str) -> str:
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"


def create_notion_page(
    video: dict, channel_name: str, industry: str, fmt: str,
    topic: str, purpose: str, score: int, reason: str, subs: int = 0,
):
    thumb = thumbnail_url(video["id"])
    notion.pages.create(
        parent={"database_id": DATABASE_ID},
        cover={"type": "external", "external": {"url": thumb}},
        properties={
            "영상 제목":       {"title":     [{"text": {"content": video["title"]}}]},
            "채널명":          {"rich_text": [{"text": {"content": channel_name}}]},
            "산업군":          {"select":    {"name": industry}},
            "콘텐츠 포맷":     {"select":    {"name": fmt}},
            "주제/컨셉":       {"select":    {"name": topic}},
            "영상 목적":       {"select":    {"name": purpose}},
            "reference_score": {"number":   score},
            "수집 사유":       {"rich_text": [{"text": {"content": reason}}]},
            "업로드 날짜":     {"date":      {"start": video["published"]}},
            "조회수":          {"number":    video["views"]},
            "좋아요 수":       {"number":    video["likes"]},
            "댓글 수":         {"number":    video["comments"]},
            "구독자수":        {"number":    subs},
            "영상 길이":       {"rich_text": [{"text": {"content": video["duration"]}}]},
            "유튜브 링크":     {"url":       video["url"]},
            "기획 인사이트":   {"rich_text": [{"text": {"content": "요약 대기"}}]},
        },
        children=[
            {
                "object": "block",
                "type": "image",
                "image": {"type": "external", "external": {"url": thumb}},
            },
            {
                "object": "block",
                "type": "bookmark",
                "bookmark": {"url": video["url"]},
            },
        ],
    )


# ─────────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────────

def delete_empty_pages():
    """제목·유튜브 링크가 모두 비어있는 빈 페이지를 삭제."""
    pages: list = []
    kwargs: dict = {"database_id": DATABASE_ID, "page_size": 100}
    while True:
        res = notion.databases.query(**kwargs)
        pages.extend(res.get("results", []))
        if not res.get("has_more"):
            break
        kwargs["start_cursor"] = res["next_cursor"]

    deleted = 0
    for p in pages:
        title = ""
        title_prop = p["properties"].get("영상 제목", {}).get("title", [])
        if title_prop:
            title = title_prop[0].get("plain_text", "").strip()
        url = p["properties"].get("유튜브 링크", {}).get("url", "") or ""
        if not title and not url.strip():
            notion.pages.update(page_id=p["id"], archived=True)
            deleted += 1

    if deleted:
        print(f"  [정리] 빈 페이지 {deleted}개 삭제")
    return deleted


def main(days: int = 1, include_search: bool = False):
    from channels import CHANNELS

    cache = load_cache()
    seen  = load_seen()
    since = datetime.now(timezone.utc) - timedelta(days=days)

    resolved   = [ch for ch in CHANNELS if ch["name"] in cache]
    unresolved = [ch for ch in CHANNELS if ch["name"] not in cache]

    print(f"\n{'='*54}")
    print(f"  유튜브 채널 모니터링  ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print(f"  기간: 최근 {days}일  |  조회수 기준: {MIN_VIEWS:,}+")
    print(f"  공식채널: {len(resolved)}개  |  검색대상: {len(unresolved)}개")
    print(f"{'='*54}\n")

    delete_empty_pages()

    all_new_ids: list[str] = []
    vid_to_meta: dict[str, tuple[str, str]] = {}

    for ch in resolved:
        cid = cache[ch["name"]]
        new_ids = fetch_playlist_video_ids(cid, since, seen)
        if new_ids:
            print(f"  [공식] {ch['name']}: 후보 {len(new_ids)}개")
            all_new_ids.extend(new_ids)
            for vid in new_ids:
                vid_to_meta[vid] = (ch["name"], ch["industry"])

    if include_search and unresolved:
        cursor = load_cursor()
        batch  = unresolved[cursor : cursor + MAX_SEARCH]
        next_cursor = (cursor + MAX_SEARCH) % len(unresolved)
        save_cursor(next_cursor)

        print(f"\n  [검색] 미탐색 채널 {len(batch)}개 처리 중...\n")
        for ch in batch:
            new_ids = search_brand_video_ids(ch["name"], since, seen)
            if new_ids:
                print(f"  [검색] {ch['name']}: 후보 {len(new_ids)}개")
                all_new_ids.extend(new_ids)
                for vid in new_ids:
                    if vid not in vid_to_meta:
                        vid_to_meta[vid] = (ch["name"], ch["industry"])

    if not all_new_ids:
        print("  신규 영상 없음.\n")
        return

    print(f"\n  영상 상세 조회 중... ({len(all_new_ids)}개 후보)")
    videos = fetch_video_details_batch(all_new_ids)

    filtered = [v for v in videos if v["views"] >= MIN_VIEWS and v["id"] not in seen]
    print(f"  조회수 {MIN_VIEWS:,} 미만 또는 중복 제외: {len(videos) - len(filtered)}개")

    brand_videos = [
        v for v in filtered
        if is_brand_content(v["title"], v.get("tags", []),
                            vid_to_meta.get(v["id"], ("", ""))[0])
    ]
    excluded = len(filtered) - len(brand_videos)
    if excluded:
        print(f"  비브랜드 콘텐츠 제외: {excluded}개")

    # ── 4-3. 채널 구독자수 배치 조회 ──
    unique_channel_ids = list({v["channel_id"] for v in brand_videos if v.get("channel_id")})
    subs_map: dict[str, int] = {}
    if unique_channel_ids:
        print(f"  구독자수 조회 중... ({len(unique_channel_ids)}개 채널)")
        subs_map = fetch_channel_subs(unique_channel_ids)

    classified = []
    for video in brand_videos:
        channel_name, default_industry = vid_to_meta.get(video["id"], ("Unknown", "IT/테크"))
        tags     = video.get("tags", [])
        industry = classify_industry(video["title"], channel_name, tags, default_industry)
        fmt      = classify_format(video["title"], tags, video["duration"])
        topic    = classify_topic(video["title"], tags)
        purpose  = classify_purpose(video["title"], tags)
        score    = calculate_reference_score(video, channel_name, fmt)
        reason   = generate_collection_reason(channel_name, fmt, score)
        subs     = subs_map.get(video.get("channel_id", ""), 0)
        classified.append((video, channel_name, industry, fmt, topic, purpose, score, reason, subs))

    print(f"  Notion 저장 중... ({len(classified)}개)\n")
    added = 0
    for video, channel_name, industry, fmt, topic, purpose, score, reason, subs in classified:
        try:
            create_notion_page(video, channel_name, industry, fmt, topic, purpose, score, reason, subs)
            seen.add(video["id"])
            added += 1
            views_str = f"{video['views']:,}"
            subs_str  = f"{subs:,}" if subs else "?"
            print(f"  ✓ [{industry}][{fmt}] {channel_name} | {video['title'][:28]} | {views_str}뷰 | 구독:{subs_str}")
        except Exception as e:
            print(f"  [오류] {video['title'][:40]}: {e}")

    save_seen(seen)

    print(f"\n{'='*54}")
    print(f"  완료: {added}개 영상 저장  |  누적 {len(seen)}개")
    print(f"{'='*54}\n")


# ─────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if "--setup" in sys.argv:
        setup_channels()
    else:
        days = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else 1
        include_search = "--search" in sys.argv
        main(days=days, include_search=include_search)
