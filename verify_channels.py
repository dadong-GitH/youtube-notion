"""채널명 검증 + 데이터 무결성 점검 + 스키마 관리.

기본 동작 (플래그 없음):
  1. 채널명 정확도 검증 — 실제 YouTube 채널 vs 저장된 채널명
  2. 데이터 무결성 점검 — 누락 필드, 이상값, 삭제된 영상 탐지

추가 플래그:
  --fix           MISMATCH 채널명 자동 수정
  --archive       UNKNOWN 채널(미등록) 영상 아카이브
  --setup-schema  '위치' 속성 삭제 + '구독자수' 속성 추가
  --add-subs      기존 페이지에 구독자수 일괄 추가
"""
from __future__ import annotations
import os, json, sys, time, re, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from googleapiclient.discovery import build
from notion_client import Client

notion      = Client(auth=os.getenv("NOTION_TOKEN"))
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
youtube     = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))

BASE_DIR   = Path(__file__).parent
CACHE_FILE = BASE_DIR / "channel_cache.json"

# 데이터 무결성 체크 기준
REQUIRED_TEXT_FIELDS  = ["영상 제목", "채널명"]
REQUIRED_SELECT_FIELDS = ["산업군", "콘텐츠 포맷", "주제/컨셉", "영상 목적"]
REQUIRED_URL_FIELDS   = ["유튜브 링크"]
REQUIRED_DATE_FIELDS  = ["업로드 날짜"]
REQUIRED_NUM_FIELDS   = ["조회수"]
SCORE_MIN, SCORE_MAX  = 0, 100


# ─────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────

def load_cache() -> dict[str, str]:
    return json.loads(CACHE_FILE.read_text("utf-8")) if CACHE_FILE.exists() else {}


def build_reverse_cache(cache: dict[str, str]) -> dict[str, str]:
    return {cid: name for name, cid in cache.items()}


def extract_video_id(url: str) -> str | None:
    if not url:
        return None
    m = re.search(r"[?&]v=([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


def get_text(prop: dict) -> str:
    items = prop.get("title") or prop.get("rich_text") or []
    return "".join(t.get("plain_text", "") for t in items).strip()


def fetch_all_pages() -> list:
    pages: list = []
    kwargs: dict = {"database_id": DATABASE_ID, "page_size": 100}
    while True:
        res = notion.databases.query(**kwargs)
        pages.extend(res.get("results", []))
        if not res.get("has_more"):
            break
        kwargs["start_cursor"] = res["next_cursor"]
    return pages


# ─────────────────────────────────────────────
# YouTube 배치 조회
# ─────────────────────────────────────────────

def fetch_video_channel_info(video_ids: list[str]) -> dict[str, dict]:
    """video_id → {channelId, channelTitle} 반환 (1 unit/50개)."""
    result: dict[str, dict] = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        try:
            res = youtube.videos().list(part="snippet", id=",".join(batch)).execute()
            for item in res.get("items", []):
                vid = item["id"]
                result[vid] = {
                    "channelId":    item["snippet"]["channelId"],
                    "channelTitle": item["snippet"]["channelTitle"],
                }
        except Exception as e:
            print(f"  [오류] YouTube 영상 조회 실패: {e}")
    return result


def fetch_channel_subs(channel_ids: list[str]) -> dict[str, int]:
    """channel_id → subscriberCount 반환 (1 unit/50개)."""
    result: dict[str, int] = {}
    unique_ids = list(set(channel_ids))
    for i in range(0, len(unique_ids), 50):
        batch = unique_ids[i : i + 50]
        try:
            res = youtube.channels().list(
                part="statistics", id=",".join(batch)
            ).execute()
            for item in res.get("items", []):
                cid  = item["id"]
                subs = int(item["statistics"].get("subscriberCount", 0))
                result[cid] = subs
        except Exception as e:
            print(f"  [오류] 구독자수 조회 실패: {e}")
    return result


# ─────────────────────────────────────────────
# 스키마 관리
# ─────────────────────────────────────────────

def setup_schema():
    """'위치' 속성 제거 + '구독자수' 속성 추가."""
    print("── 스키마 업데이트 ──")
    try:
        notion.databases.update(
            database_id=DATABASE_ID,
            properties={
                "위치":    None,          # 속성 삭제
                "구독자수": {"number": {"format": "number"}},
            },
        )
        print("  ✓ '위치' 삭제 + '구독자수' 추가 완료")
    except Exception as e:
        print(f"  [경고] 스키마 업데이트 실패: {e}")
    print()


# ─────────────────────────────────────────────
# 채널명 검증
# ─────────────────────────────────────────────

def verify_channel_names(
    pages: list, fix: bool, archive_unknown: bool, reverse_cache: dict[str, str]
) -> dict:
    print("── 채널명 검증 중 ──")

    vid_to_page: dict[str, dict] = {}
    no_url_count = 0
    for p in pages:
        props = p["properties"]
        url   = props.get("유튜브 링크", {}).get("url", "") or ""
        vid   = extract_video_id(url)
        if vid:
            vid_to_page[vid] = p
        else:
            no_url_count += 1

    print(f"  YouTube 채널 정보 조회 중 ({len(vid_to_page)}개)...")
    channel_info = fetch_video_channel_info(list(vid_to_page.keys()))
    deleted_count = len(vid_to_page) - len(channel_info)

    ok_count       = 0
    mismatch_pages: list[dict] = []
    unknown_pages:  list[dict] = []

    for vid, info in channel_info.items():
        page         = vid_to_page[vid]
        props        = page["properties"]
        stored_name  = get_text(props.get("채널명", {}))
        title        = get_text(props.get("영상 제목", {}))
        actual_cid   = info["channelId"]
        actual_title = info["channelTitle"]
        expected     = reverse_cache.get(actual_cid)

        if expected is None:
            unknown_pages.append({
                "page": page, "title": title, "stored": stored_name,
                "actual_title": actual_title, "actual_cid": actual_cid,
            })
        elif expected != stored_name:
            mismatch_pages.append({
                "page": page, "title": title, "stored": stored_name,
                "correct": expected, "actual_title": actual_title,
            })
        else:
            ok_count += 1

    print(f"  정상: {ok_count}  |  채널명 오류: {len(mismatch_pages)}  |  미등록 채널: {len(unknown_pages)}  |  삭제 영상: {deleted_count}\n")

    if mismatch_pages:
        print("  [MISMATCH] 저장된 채널명 → 실제 채널")
        for row in mismatch_pages:
            print(f"    [{row['stored']:<20}] → [{row['correct']:<20}]  {row['title'][:40]}")
        print()

    if unknown_pages:
        print("  [UNKNOWN] 등록되지 않은 채널의 영상")
        for row in unknown_pages:
            print(f"    실제: {row['actual_title']:<30}  저장: {row['stored']:<15}  {row['title'][:35]}")
        print()

    fixed = archived = 0

    if fix and mismatch_pages:
        print(f"  채널명 수정 중 ({len(mismatch_pages)}개)...")
        for row in mismatch_pages:
            try:
                notion.pages.update(
                    page_id=row["page"]["id"],
                    properties={"채널명": {"rich_text": [{"text": {"content": row["correct"]}}]}},
                )
                fixed += 1
                time.sleep(0.05)
            except Exception as e:
                print(f"    [오류] {row['title'][:40]}: {e}")
        print(f"  ✓ {fixed}개 수정 완료\n")

    if archive_unknown and unknown_pages:
        print(f"  UNKNOWN 영상 아카이브 중 ({len(unknown_pages)}개)...")
        for row in unknown_pages:
            try:
                notion.pages.update(page_id=row["page"]["id"], archived=True)
                archived += 1
                time.sleep(0.05)
            except Exception as e:
                print(f"    [오류] {row['title'][:40]}: {e}")
        print(f"  ✓ {archived}개 아카이브 완료\n")

    return {
        "ok": ok_count, "mismatch": len(mismatch_pages),
        "unknown": len(unknown_pages), "deleted": deleted_count,
        "fixed": fixed, "archived": archived,
    }


# ─────────────────────────────────────────────
# 데이터 무결성 점검
# ─────────────────────────────────────────────

def check_data_integrity(pages: list) -> dict:
    print("── 데이터 무결성 점검 ──")

    issues: list[dict] = []

    for p in pages:
        props  = p["properties"]
        title  = get_text(props.get("영상 제목", {}))
        page_issues: list[str] = []

        # ① 필수 텍스트 필드 누락
        for field in REQUIRED_TEXT_FIELDS:
            if not get_text(props.get(field, {})):
                page_issues.append(f"{field} 비어있음")

        # ② 필수 select 필드 누락
        for field in REQUIRED_SELECT_FIELDS:
            val = (props.get(field, {}).get("select") or {}).get("name", "")
            if not val:
                page_issues.append(f"{field} 미분류")

        # ③ URL 필드 누락/형식 오류
        for field in REQUIRED_URL_FIELDS:
            url = props.get(field, {}).get("url", "") or ""
            if not url:
                page_issues.append(f"{field} 없음")
            elif "youtube.com/watch" not in url and "youtu.be" not in url:
                page_issues.append(f"{field} 형식 오류: {url[:40]}")

        # ④ 날짜 필드 누락
        for field in REQUIRED_DATE_FIELDS:
            date_val = (props.get(field, {}).get("date") or {}).get("start", "")
            if not date_val:
                page_issues.append(f"{field} 없음")

        # ⑤ 숫자 필드 이상값 (음수)
        for field in REQUIRED_NUM_FIELDS:
            num = props.get(field, {}).get("number")
            if num is not None and num < 0:
                page_issues.append(f"{field} 음수값: {num}")

        # ⑥ reference_score 범위 초과
        score = props.get("reference_score", {}).get("number")
        if score is not None and not (SCORE_MIN <= score <= SCORE_MAX):
            page_issues.append(f"reference_score 범위 초과: {score}")

        if page_issues:
            issues.append({"title": title or "(제목없음)", "issues": page_issues})

    clean_count = len(pages) - len(issues)
    print(f"  정상: {clean_count}개  |  문제 발견: {len(issues)}개\n")

    if issues:
        print("  [무결성 오류 목록]")
        for row in issues:
            print(f"    {row['title'][:45]}")
            for iss in row["issues"]:
                print(f"      • {iss}")
        print()

    return {"clean": clean_count, "issues": len(issues)}


# ─────────────────────────────────────────────
# 구독자수 일괄 추가
# ─────────────────────────────────────────────

def add_subscriber_counts(pages: list):
    print("── 구독자수 추가 중 ──")

    # 구독자수가 없는 페이지만 대상
    target_pages = [
        p for p in pages
        if p["properties"].get("구독자수", {}).get("number") is None
    ]
    print(f"  대상: {len(target_pages)}개 (이미 입력된 페이지 제외)\n")

    if not target_pages:
        print("  모든 페이지에 구독자수가 이미 있습니다.\n")
        return

    # 각 페이지의 video_id 수집
    vid_to_page: dict[str, dict] = {}
    for p in target_pages:
        url = p["properties"].get("유튜브 링크", {}).get("url", "") or ""
        vid = extract_video_id(url)
        if vid:
            vid_to_page[vid] = p

    # 영상 → channelId 조회
    print(f"  채널 ID 조회 중 ({len(vid_to_page)}개 영상)...")
    channel_info = fetch_video_channel_info(list(vid_to_page.keys()))

    # channelId → 구독자수 조회
    channel_ids = list({info["channelId"] for info in channel_info.values()})
    print(f"  구독자수 조회 중 ({len(channel_ids)}개 채널)...")
    subs_map = fetch_channel_subs(channel_ids)

    # Notion 업데이트
    updated = 0
    for vid, info in channel_info.items():
        page  = vid_to_page[vid]
        subs  = subs_map.get(info["channelId"], 0)
        try:
            notion.pages.update(
                page_id=page["id"],
                properties={"구독자수": {"number": subs}},
            )
            updated += 1
            time.sleep(0.05)
        except Exception as e:
            title = get_text(page["properties"].get("영상 제목", {}))
            print(f"  [오류] {title[:40]}: {e}")

        if updated % 50 == 0:
            print(f"  {updated}/{len(vid_to_page)} 완료...")

    print(f"  ✓ {updated}개 구독자수 업데이트 완료\n")


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────

def main(
    fix: bool = False,
    archive_unknown: bool = False,
    setup: bool = False,
    add_subs: bool = False,
):
    if setup:
        setup_schema()

    cache         = load_cache()
    reverse_cache = build_reverse_cache(cache)

    print(f"── 전체 페이지 조회 중 ──")
    pages = fetch_all_pages()
    print(f"  총 {len(pages)}개\n")

    # ① 채널명 검증
    ch_result = verify_channel_names(pages, fix, archive_unknown, reverse_cache)

    # ② 데이터 무결성 점검
    integrity_result = check_data_integrity(pages)

    # ③ 구독자수 추가 (--add-subs)
    if add_subs:
        add_subscriber_counts(pages)

    # ── 최종 요약 ──
    print(f"{'='*60}")
    print(f"  [채널명 검증]")
    print(f"    ✅ 정상:         {ch_result['ok']}개")
    print(f"    ⚠️  채널명 오류:  {ch_result['mismatch']}개  (수정: {ch_result['fixed']}개)")
    print(f"    ❌ 미등록 채널:  {ch_result['unknown']}개  (아카이브: {ch_result['archived']}개)")
    print(f"    🗑  유튜브 삭제:  {ch_result['deleted']}개")
    print(f"  [데이터 무결성]")
    print(f"    ✅ 정상:         {integrity_result['clean']}개")
    print(f"    ⚠️  문제 발견:   {integrity_result['issues']}개")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main(
        fix             = "--fix"           in sys.argv,
        archive_unknown = "--archive"       in sys.argv,
        setup           = "--setup-schema"  in sys.argv,
        add_subs        = "--add-subs"      in sys.argv,
    )
