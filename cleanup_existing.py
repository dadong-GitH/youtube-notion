"""기존 Notion 페이지를 최신 필터/분류 기준으로 일괄 정리.

동작:
  1. 비브랜드 콘텐츠(뮤직비디오·팬캠·예능 등) → 아카이브(삭제)
  2. 산업군이 바뀐 페이지 → select 속성 업데이트
  3. seen_videos.json에서 삭제된 video_id 제거
"""
from __future__ import annotations
import os, json, time, warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
load_dotenv()
from notion_client import Client
from main import is_brand_content, classify_industry, SEEN_FILE

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

    deleted_ids: set[str] = set()
    reclassified = 0
    deleted_count = 0

    for i, p in enumerate(pages, 1):
        props      = p["properties"]
        title      = get_text(props.get("영상 제목", {}))
        channel    = get_text(props.get("채널명", {}))
        url        = props.get("유튜브 링크", {}).get("url", "") or ""
        current_ind = (props.get("산업군", {}).get("select") or {}).get("name", "")

        vid = url.split("v=")[-1].split("&")[0] if "v=" in url else ""

        # ── 비브랜드 콘텐츠 → 삭제 ──
        if not is_brand_content(title, [], channel):
            try:
                notion.pages.update(page_id=p["id"], archived=True)
                deleted_count += 1
                if vid:
                    deleted_ids.add(vid)
                print(f"  [삭제] [{channel}] {title[:55]}")
            except Exception as e:
                print(f"  [오류] 삭제 실패 ({title[:30]}): {e}")
            time.sleep(0.05)
            continue

        # ── 산업군 재분류 ──
        if title:
            new_ind = classify_industry(title, channel, [], current_ind)
            if new_ind != current_ind and new_ind:
                try:
                    notion.pages.update(
                        page_id=p["id"],
                        properties={"산업군": {"select": {"name": new_ind}}},
                    )
                    reclassified += 1
                    print(f"  [재분류] {current_ind} → {new_ind} | {title[:45]}")
                except Exception as e:
                    print(f"  [오류] 재분류 실패 ({title[:30]}): {e}")
                time.sleep(0.05)

        if i % 50 == 0:
            print(f"  ... {i}/{len(pages)} 처리 중")

    # ── seen_videos.json 정리 ──
    if deleted_ids and SEEN_FILE.exists():
        seen = set(json.loads(SEEN_FILE.read_text("utf-8")))
        before = len(seen)
        seen -= deleted_ids
        SEEN_FILE.write_text(json.dumps(sorted(seen), ensure_ascii=False), "utf-8")
        print(f"\n  seen_videos.json: {before} → {len(seen)}개 ({len(deleted_ids)}개 제거)")

    print(f"\n{'='*54}")
    print(f"  삭제: {deleted_count}개  |  산업군 재분류: {reclassified}개")
    print(f"{'='*54}\n")


if __name__ == "__main__":
    main()
