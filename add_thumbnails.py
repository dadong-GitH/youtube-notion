"""기존 Notion 페이지에 YouTube 썸네일을 커버로 일괄 추가하는 스크립트."""
from __future__ import annotations
import os, time, warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
load_dotenv()
from notion_client import Client

notion    = Client(auth=os.getenv("NOTION_TOKEN"))
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

def main():
    print("페이지 목록 조회 중...")
    pages = fetch_all_pages()
    print(f"총 {len(pages)}개 페이지")

    updated, skipped = 0, 0
    for p in pages:
        if p.get("cover"):
            skipped += 1
            continue
        url = p["properties"].get("유튜브 링크", {}).get("url", "")
        if not url or "v=" not in url:
            skipped += 1
            continue
        vid   = url.split("v=")[-1].split("&")[0]
        thumb = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
        notion.pages.update(
            page_id=p["id"],
            cover={"type": "external", "external": {"url": thumb}},
        )
        updated += 1
        if updated % 50 == 0:
            print(f"  {updated}개 완료...")
            time.sleep(0.3)

    print(f"\n완료: {updated}개 썸네일 추가 / {skipped}개 스킵")

if __name__ == "__main__":
    main()
