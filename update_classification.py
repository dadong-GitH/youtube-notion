"""산업군·주제·포맷 분류 일괄 업데이트.

1. Notion DB에 '주제/컨셉' select 컬럼 생성
2. 금융 → 금융/핀테크 통합
3. 모든 페이지에 주제/컨셉 추가
4. '기타' 포맷 페이지 재분류 시도
"""
from __future__ import annotations
import os, time, warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
load_dotenv()
from notion_client import Client
from main import classify_topic, classify_format

notion = Client(auth=os.getenv("NOTION_TOKEN"))
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

TOPIC_COLORS = {
    "사회공헌/ESG":   "green",
    "제품/서비스":    "yellow",
    "브랜드/기업":    "blue",
    "캠페인/이벤트":  "orange",
    "트렌드/라이프":  "pink",
    "정보/교육":      "purple",
    "뉴스/이슈":      "red",
    "엔터테인먼트":   "brown",
    "기타":           "gray",
}


def create_topic_property():
    """Notion DB에 주제/컨셉 select 속성 추가."""
    try:
        notion.databases.update(
            database_id=DATABASE_ID,
            properties={
                "주제/컨셉": {
                    "select": {
                        "options": [
                            {"name": name, "color": color}
                            for name, color in TOPIC_COLORS.items()
                        ]
                    }
                }
            },
        )
        print("  ✓ '주제/컨셉' 컬럼 생성 완료")
    except Exception as e:
        if "already exists" in str(e).lower() or "existing" in str(e).lower():
            print("  ✓ '주제/컨셉' 컬럼 이미 존재")
        else:
            print(f"  [경고] 컬럼 생성 실패: {e}")


def fetch_all_pages() -> list:
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
    return pages


def get_text(prop) -> str:
    items = prop.get("title") or prop.get("rich_text") or []
    return "".join(t.get("plain_text", "") for t in items).strip()


def main():
    print("\n── 1. 주제/컨셉 컬럼 생성 ──")
    create_topic_property()

    print("\n── 2. 기존 페이지 조회 ──")
    pages = fetch_all_pages()
    print(f"  총 {len(pages)}개\n")

    industry_fixed = 0
    topic_added = 0
    fmt_reclassified = 0
    topic_counts: dict[str, int] = {}

    for i, p in enumerate(pages, 1):
        props       = p["properties"]
        title       = get_text(props.get("영상 제목", {}))
        duration    = get_text(props.get("영상 길이", {}))
        cur_industry = (props.get("산업군", {}).get("select") or {}).get("name", "")
        cur_topic    = (props.get("주제/컨셉", {}).get("select") or {}).get("name", "")
        cur_fmt      = (props.get("콘텐츠 포맷", {}).get("select") or {}).get("name", "")

        if not title:
            continue

        updates: dict = {}

        # 금융 → 금융/핀테크 통합
        if cur_industry == "금융":
            updates["산업군"] = {"select": {"name": "금융/핀테크"}}
            industry_fixed += 1

        # 주제/컨셉 미분류 → 분류
        if not cur_topic:
            topic = classify_topic(title, [])
            updates["주제/컨셉"] = {"select": {"name": topic}}
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
            topic_added += 1

        # 포맷 '기타' → 재분류 시도
        if cur_fmt == "기타":
            new_fmt = classify_format(title, [], duration)
            if new_fmt != "기타":
                updates["콘텐츠 포맷"] = {"select": {"name": new_fmt}}
                fmt_reclassified += 1

        if updates:
            try:
                notion.pages.update(page_id=p["id"], properties=updates)
                time.sleep(0.05)
            except Exception as e:
                print(f"  [오류] {title[:40]}: {e}")

        if i % 50 == 0:
            print(f"  {i}/{len(pages)} 처리 중...")

    print(f"\n{'='*54}")
    print(f"  금융→금융/핀테크 통합: {industry_fixed}개")
    print(f"  주제/컨셉 추가:       {topic_added}개")
    print(f"  포맷 '기타' 재분류:  {fmt_reclassified}개")
    print(f"\n  주제별 분포:")
    for topic, cnt in sorted(topic_counts.items(), key=lambda x: -x[1]):
        print(f"    {topic:<18} {cnt:>4}개")
    print(f"{'='*54}\n")


if __name__ == "__main__":
    main()
