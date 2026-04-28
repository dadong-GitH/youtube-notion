# 프로젝트 구축 세션 기록 요약

> 유튜브 → 노션 자동 모니터링 파이프라인 구축 과정을 기록합니다.
> 작업 기간: 2026년 4월 26일 ~ 28일

---

## 1단계: 요구사항 정의

**목표**
- 한국 기업 공식 유튜브 채널의 신규 영상을 매일 자동 수집
- Notion 데이터베이스에 저장 및 갤러리 뷰로 시각화
- YouTube API 할당량(10,000 units/일) 안에서 효율적으로 운영

**확정된 요구사항**
- 200개 채널 (10개 산업군 × 20개 채널)
- 조회수 100회 이상 영상만 수집
- 매일 정오(12:00) 자동 실행
- 유튜브 썸네일을 Notion 페이지 커버로 설정
- 갤러리 뷰: 📋 전체, 🏢 산업군별

---

## 2단계: 환경 구성

### API 키 발급
- **YouTube Data API v3**: Google Cloud Console에서 발급
- **Notion Integration Token**: notion.so/my-integrations에서 발급 (ntn_ prefix)
- Notion 데이터베이스 페이지에 인테그레이션 연결 (우측 상단 `...` → 연결)

### 패키지 설치
```bash
pip3 install google-api-python-client notion-client==2.2.1 python-dotenv
```

> **주의**: `notion-client` v3는 `databases.query` 메서드를 제거했으므로 반드시 v2.2.1 사용

---

## 3단계: 채널 목록 구성 (channels.py)

10개 산업군, 각 20개 채널:

| 산업군 | 대표 채널 |
|--------|---------|
| IT/테크 | 삼성전자, LG전자, 카카오, 네이버 |
| 금융/핀테크 | 신한은행, KB국민은행, 토스, 카카오페이 |
| 유통/이커머스 | 쿠팡, 이마트, 롯데쇼핑, GS25 |
| 식품/음료 | CJ제일제당, 농심, 오리온, 빙그레 |
| 뷰티/패션 | 아모레퍼시픽, LG생활건강, 올리브영 |
| 자동차/모빌리티 | 현대자동차, 기아, SK에너지 |
| 미디어/엔터 | JTBC, MBC, YG엔터테인먼트, SM엔터 |
| 교육/에듀테크 | 메가스터디, 대교, 웅진씽크빅 |
| 건강/의료 | 유한양행, 삼성서울병원, 정관장 |
| 건설/부동산 | 삼성물산, 현대건설, 두산건설 |

각 채널은 `handle`(공식 핸들) 또는 `name`(브랜드명 검색)으로 지정.

---

## 4단계: 메인 스크립트 구현 (main.py)

### API 할당량 최적화 (핵심 의사결정)

| 방식 | 비용 | 적용 대상 |
|------|------|---------|
| `search.list` | 100 units/채널 | 초기 채널 ID 탐색 (`--setup`, 1회) |
| `playlistItems.list` | 1 unit/채널 | 공식채널 일일 수집 (resolved) |
| `videos.list` | 1 unit/50개 | 영상 상세 정보 배치 조회 |

**핵심 구조**:
1. `--setup`: 전체 채널 ID 탐색 → `channel_cache.json` 저장 (최초 1회)
2. 일반 실행: 캐시된 채널만 `playlistItems.list`로 조회 (약 97 units/일)
3. `--search`: 미탐색 채널을 브랜드명 검색 (하루 최대 90채널, 순환)

**중복 방지**: `seen_videos.json`에 수집된 video_id 저장, 재수집 차단

### 주요 기능
```python
python3 main.py          # 일반 실행 (최근 1일)
python3 main.py --setup  # 채널 ID 최초 탐색
python3 main.py --search # 미탐색 채널 브랜드명 검색 포함
python3 main.py --days 7 # 수집 기간 조정
```

---

## 5단계: Notion 저장 구조

### 데이터베이스 컬럼
```
영상 제목, 채널명, 산업군(select), 업로드 날짜,
조회수, 좋아요 수, 댓글 수, 영상 길이, 유튜브 링크, 기획 인사이트
```

### 썸네일 자동 설정
```python
cover={"type": "external", "external": {
    "url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
}}
```

---

## 6단계: 자동화 (launchd)

**crontab 대신 launchd 선택 이유**:
- crontab: 잠자기 중 스킵, 전원 켜져도 재실행 안 함
- launchd: 잠자기 동안 실행 못 하면 전원 켜진 직후 보상 실행

```bash
# 등록
launchctl load ~/Library/LaunchAgents/com.youtube-notion.monitor.plist

# 즉시 테스트
launchctl start com.youtube-notion.monitor
```

실행 시간: **매일 정오(12:00)**

---

## 7단계: 갤러리 뷰 및 썸네일

- `add_thumbnails.py`: 기존 Notion 페이지에 썸네일 일괄 추가
- 기존 134개 페이지 썸네일 업데이트 완료
- Notion에서 갤러리 뷰 생성 후 "커버" 표시 설정 → 유튜브 썸네일 표시

---

## 트러블슈팅 기록

| 문제 | 원인 | 해결 |
|------|------|------|
| `str \| None` 타입 에러 | Python 3.9 호환성 | `from __future__ import annotations` 추가 |
| YouTube API 403 quotaExceeded | `--setup`으로 9,700 units 소진 | KST 16:00 이후 리셋 대기 |
| Notion 404 오류 | 인테그레이션 미연결 | Notion UI에서 데이터베이스에 연결 |
| notion-client AttributeError | v3에서 `databases.query` 제거 | v2.2.1로 다운그레이드 |
| `seen_videos.json` 없음 | 최초 실행 시 파일 미존재 | `load_seen()` 에서 빈 set 반환 |

---

## 최종 파일 구조

```
~/youtube-notion/
├── main.py                      # 메인 수집 스크립트
├── channels.py                  # 200개 채널 목록
├── add_thumbnails.py            # 기존 페이지 썸네일 일괄 추가
├── run.sh                       # launchd 실행 래퍼
├── requirements.txt             # 패키지 목록
├── .env                         # API 키 (gitignore)
├── channel_cache.json           # 채널 ID 캐시 (gitignore)
├── seen_videos.json             # 수집 완료 목록 (gitignore)
├── search_cursor.json           # 순환 커서 (gitignore)
├── monitor.log                  # 실행 로그 (gitignore)
└── 유튜브_노션_모니터링_설정.md  # 설정 가이드
```

---

*세션 요약 작성: 2026-04-28*
