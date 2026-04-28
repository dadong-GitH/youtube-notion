"""기존 Notion 페이지에 '콘텐츠 포맷' 속성을 일괄 추가."""
from __future__ import annotations
import os, time, warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
load_dotenv()
from notion_client import Client
from main import classify_format

notion = Client(auth=os.getenv("NOTION_TOKEN"))
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")


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
    print("페이지 목록 조회 중...")
    pages = fetch_all_pages()
    print(f"총 {len(pages)}개 페이지\n")

    updated, skipped = 0, 0
    fmt_counts: dict[str, int] = {}

    for i, p in enumerate(pages, 1):
        props   = p["properties"]
        title   = get_text(props.get("영상 제목", {}))
        dur_raw = get_text(props.get("영상 길이", {}))

        # 이미 포맷이 설정된 페이지는 스킵
        if props.get("콘텐츠 포맷", {}).get("select"):
            skipped += 1
            continue

        if not title:
            skipped += 1
            continue

        fmt = classify_format(title, [], dur_raw)
        fmt_counts[fmt] = fmt_counts.get(fmt, 0) + 1

        try:
            notion.pages.update(
                page_id=p["id"],
                properties={"콘텐츠 포맷": {"select": {"name": fmt}}},
            )
            updated += 1
            if updated % 30 == 0:
                print(f"  {updated}개 완료...")
            time.sleep(0.05)
        except Exception as e:
            print(f"  [오류] {title[:40]}: {e}")
            skipped += 1

    print(f"\n{'='*54}")
    print(f"  완료: {updated}개 업데이트  |  스킵: {skipped}개")
    print(f"\n  포맷별 분포:")
    for fmt, cnt in sorted(fmt_counts.items(), key=lambda x: -x[1]):
        print(f"    {fmt:<18} {cnt:>4}개")
    print(f"{'='*54}\n")


if __name__ == "__main__":
    main()
