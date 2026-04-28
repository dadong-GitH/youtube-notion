"""기존 Notion 페이지 스키마 마이그레이션.

1. 신규 속성 추가: 영상 목적(select), reference_score(number), 수집 사유(rich_text)
2. 산업군 명칭 통합 (구 → 신)
3. 포맷 명칭 통합 (구 → 신)
4. 영상 목적·reference_score 미분류 페이지 일괄 분류
"""
from __future__ import annotations
import os, time, warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
load_dotenv()
from notion_client import Client
from main import (
    classify_format, classify_purpose,
    calculate_reference_score, generate_collection_reason,
    _duration_to_seconds,
)
from config import (
    INDUSTRY_MIGRATIONS, FORMAT_MIGRATIONS,
    PURPOSE_COLORS,
)

notion      = Client(auth=os.getenv("NOTION_TOKEN"))
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")


def ensure_new_properties():
    """신규 Notion 속성을 DB 스키마에 추가 (이미 있으면 무시)."""
    try:
        notion.databases.update(
            database_id=DATABASE_ID,
            properties={
                "영상 목적": {
                    "select": {
                        "options": [
                            {"name": name, "color": color}
                            for name, color in PURPOSE_COLORS.items()
                        ]
                    }
                },
                "reference_score": {"number": {"format": "number"}},
                "수집 사유":       {"rich_text": {}},
            },
        )
        print("  ✓ 신규 속성 추가 완료 (영상 목적 / reference_score / 수집 사유)")
    except Exception as e:
        print(f"  [경고] 속성 추가 실패: {e}")


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


def get_text(prop: dict) -> str:
    items = prop.get("title") or prop.get("rich_text") or []
    return "".join(t.get("plain_text", "") for t in items).strip()


def main():
    print("\n── 1. 신규 속성 생성 ──")
    ensure_new_properties()

    print("\n── 2. 전체 페이지 조회 ──")
    pages = fetch_all_pages()
    print(f"  총 {len(pages)}개\n")

    industry_fixed = 0
    format_fixed   = 0
    purpose_added  = 0
    score_added    = 0

    for i, p in enumerate(pages, 1):
        props = p["properties"]

        title    = get_text(props.get("영상 제목", {}))
        channel  = get_text(props.get("채널명", {}))
        duration = get_text(props.get("영상 길이", {}))
        cur_ind  = (props.get("산업군",    {}).get("select") or {}).get("name", "")
        cur_fmt  = (props.get("콘텐츠 포맷",{}).get("select") or {}).get("name", "")
        cur_purp = (props.get("영상 목적", {}).get("select") or {}).get("name", "")
        cur_score = props.get("reference_score", {}).get("number")
        views    = props.get("조회수",    {}).get("number") or 0
        likes    = props.get("좋아요 수", {}).get("number") or 0
        comments = props.get("댓글 수",  {}).get("number") or 0
        pub_date = (props.get("업로드 날짜", {}).get("date") or {}).get("start", "")

        if not title:
            continue

        updates: dict = {}

        # ── 산업군 명칭 마이그레이션 ──
        if cur_ind in INDUSTRY_MIGRATIONS:
            updates["산업군"] = {"select": {"name": INDUSTRY_MIGRATIONS[cur_ind]}}
            industry_fixed += 1

        # ── 포맷 명칭 마이그레이션 ──
        if cur_fmt in FORMAT_MIGRATIONS:
            updates["콘텐츠 포맷"] = {"select": {"name": FORMAT_MIGRATIONS[cur_fmt]}}
            cur_fmt = FORMAT_MIGRATIONS[cur_fmt]
            format_fixed += 1

        # ── 영상 목적 미분류 → 분류 ──
        if not cur_purp:
            purpose = classify_purpose(title, [])
            updates["영상 목적"] = {"select": {"name": purpose}}
            purpose_added += 1
        else:
            purpose = cur_purp

        # ── reference_score 미설정 → 계산 ──
        if cur_score is None:
            video_proxy = {
                "views":     views,
                "likes":     likes,
                "comments":  comments,
                "published": pub_date,
            }
            # 포맷이 이미 마이그레이션된 값 사용
            effective_fmt = cur_fmt if cur_fmt not in FORMAT_MIGRATIONS else FORMAT_MIGRATIONS[cur_fmt]
            score  = calculate_reference_score(video_proxy, channel, effective_fmt)
            reason = generate_collection_reason(channel, effective_fmt, score)
            updates["reference_score"] = {"number": score}
            updates["수집 사유"]       = {"rich_text": [{"text": {"content": reason}}]}
            score_added += 1

        if updates:
            try:
                notion.pages.update(page_id=p["id"], properties=updates)
                time.sleep(0.05)
            except Exception as e:
                print(f"  [오류] {title[:40]}: {e}")

        if i % 50 == 0:
            print(f"  {i}/{len(pages)} 처리 중...")

    print(f"\n{'='*54}")
    print(f"  산업군 명칭 통합:     {industry_fixed}개")
    print(f"  포맷 명칭 통합:       {format_fixed}개")
    print(f"  영상 목적 분류:       {purpose_added}개")
    print(f"  reference_score 추가: {score_added}개")
    print(f"{'='*54}\n")


if __name__ == "__main__":
    main()
