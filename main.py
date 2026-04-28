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

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
NOTION_TOKEN    = os.getenv("NOTION_TOKEN")
DATABASE_ID     = os.getenv("NOTION_DATABASE_ID")

MIN_VIEWS  = 100      # 최소 조회수 기준
MAX_SEARCH = 90       # --search 모드에서 하루 최대 처리 채널 수 (할당량 보호)

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
notion  = Client(auth=NOTION_TOKEN)

BASE_DIR     = Path(__file__).parent
CACHE_FILE   = BASE_DIR / "channel_cache.json"    # 채널명 → channel_id
SEEN_FILE    = BASE_DIR / "seen_videos.json"      # 저장된 video_id 집합
CURSOR_FILE  = BASE_DIR / "search_cursor.json"    # unresolved 순환 커서


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

    # handle → channels.list (1 unit)
    if "handle" in ch:
        try:
            res = youtube.channels().list(part="id", forHandle=ch["handle"]).execute()
            items = res.get("items", [])
            if items:
                channel_id = items[0]["id"]
        except Exception:
            pass

    # search → search.list (100 units, 최초 1회만)
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


def fetch_playlist_video_ids(channel_id: str, since: datetime, seen: set) -> list[str]:
    """공식 채널 업로드 플레이리스트 조회. 1 unit/채널."""
    playlist_id = "UU" + channel_id[2:]
    new_ids = []
    try:
        res = youtube.playlistItems().list(
            part="contentDetails", playlistId=playlist_id, maxResults=10
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
                })
        except Exception as e:
            print(f"  [오류] 영상 상세 조회 실패: {e}")
    return results


# ─────────────────────────────────────────────
# Notion 저장
# ─────────────────────────────────────────────

def thumbnail_url(video_id: str) -> str:
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

def create_notion_page(video: dict, channel_name: str, industry: str):
    thumb = thumbnail_url(video["id"])
    notion.pages.create(
        parent={"database_id": DATABASE_ID},
        cover={"type": "external", "external": {"url": thumb}},
        properties={
            "영상 제목":     {"title":     [{"text": {"content": video["title"]}}]},
            "채널명":        {"rich_text": [{"text": {"content": channel_name}}]},
            "산업군":        {"select":    {"name": industry}},
            "업로드 날짜":   {"date":      {"start": video["published"]}},
            "조회수":        {"number":    video["views"]},
            "좋아요 수":     {"number":    video["likes"]},
            "댓글 수":       {"number":    video["comments"]},
            "영상 길이":     {"rich_text": [{"text": {"content": video["duration"]}}]},
            "유튜브 링크":   {"url":       video["url"]},
            "기획 인사이트": {"rich_text": [{"text": {"content": "요약 대기"}}]},
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
    pages, cursor = [], None
    while True:
        kwargs = {"page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        res = notion.databases.query(database_id=DATABASE_ID, **kwargs)
        pages.extend(res.get("results", []))
        if not res.get("has_more"):
            break
        cursor = res["next_cursor"]

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

    # ── 0. 빈 페이지 정리 ──
    delete_empty_pages()

    all_new_ids: list[str] = []
    vid_to_meta: dict[str, tuple[str, str]] = {}

    # ── 1. 공식 채널: 업로드 플레이리스트 (1 unit/채널) ──
    for ch in resolved:
        cid = cache[ch["name"]]
        new_ids = fetch_playlist_video_ids(cid, since, seen)
        if new_ids:
            print(f"  [공식] {ch['name']}: 후보 {len(new_ids)}개")
            all_new_ids.extend(new_ids)
            for vid in new_ids:
                vid_to_meta[vid] = (ch["name"], ch["industry"])

    # ── 2. 미탐색 채널: 브랜드명 영상 검색 (100 units/채널) ──
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

    # ── 3. 영상 상세 배치 조회 (1 unit/50개) ──
    print(f"\n  영상 상세 조회 중... ({len(all_new_ids)}개 후보)")
    videos = fetch_video_details_batch(all_new_ids)

    # ── 4. 조회수 10,000+ 필터 + 중복 제거 ──
    filtered = [v for v in videos if v["views"] >= MIN_VIEWS and v["id"] not in seen]
    skipped  = len(videos) - len(filtered)
    print(f"  조회수 {MIN_VIEWS:,} 미만 또는 중복 제외: {skipped}개")

    # ── 5. Notion 저장 ──
    print(f"  Notion 저장 중... ({len(filtered)}개)\n")
    added = 0
    for video in filtered:
        channel_name, industry = vid_to_meta.get(video["id"], ("Unknown", "IT/테크"))
        create_notion_page(video, channel_name, industry)
        seen.add(video["id"])
        added += 1
        views_str = f"{video['views']:,}"
        print(f"  ✓ [{industry}] {channel_name} | {video['title'][:40]} | 조회 {views_str}")

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
