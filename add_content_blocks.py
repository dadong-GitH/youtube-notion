"""기존 Notion 페이지에 썸네일 이미지 블록 + 유튜브 북마크 블록을 일괄 추가."""
from __future__ import annotations
import os, time, warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
load_dotenv()
from notion_client import Client

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


def has_image_block(page_id: str) -> bool:
    """페이지 첫 블록이 이미지인지 확인."""
    res = notion.blocks.children.list(block_id=page_id, page_size=1)
    blocks = res.get("results", [])
    return bool(blocks) and blocks[0].get("type") == "image"


def add_blocks(page_id: str, thumb_url: str, youtube_url: str):
    notion.blocks.children.append(
        block_id=page_id,
        children=[
            {
                "object": "block",
                "type": "image",
                "image": {"type": "external", "external": {"url": thumb_url}},
            },
            {
                "object": "block",
                "type": "bookmark",
                "bookmark": {"url": youtube_url},
            },
        ],
    )


def main():
    print("페이지 목록 조회 중...")
    pages = fetch_all_pages()
    print(f"총 {len(pages)}개 페이지\n")

    updated, skipped = 0, 0
    for p in pages:
        url = p["properties"].get("유튜브 링크", {}).get("url", "")
        if not url or "v=" not in url:
            skipped += 1
            continue

        if has_image_block(p["id"]):
            skipped += 1
            continue

        vid = url.split("v=")[-1].split("&")[0]
        thumb = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"

        try:
            add_blocks(p["id"], thumb, url)
            updated += 1
            if updated % 10 == 0:
                print(f"  {updated}개 완료...")
                time.sleep(0.3)
        except Exception as e:
            print(f"  [오류] {p['id']}: {e}")
            skipped += 1

    print(f"\n완료: {updated}개 블록 추가 / {skipped}개 스킵")
    print("\n[다음 단계] Notion 갤러리 뷰 설정:")
    print("  갤러리 우측 상단 ··· → Properties → Card preview → Page content")


if __name__ == "__main__":
    main()
