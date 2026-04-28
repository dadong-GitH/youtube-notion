# 한국 주요 기업/브랜드 공식 유튜브 채널 + 우선 크리에이터/스튜디오
# handle: YouTube @handle (우선 사용)
# search: handle 없을 때 YouTube 검색어로 채널 ID 탐색

CHANNELS = [
    # ────────────────────────────────
    # IT/테크 (20)
    # ────────────────────────────────
    {"name": "삼성전자",       "industry": "IT/테크", "handle": "SamsungKorea"},
    {"name": "LG전자",         "industry": "IT/테크", "handle": "LGElectronics"},
    {"name": "SK텔레콤",       "industry": "IT/테크", "handle": "SKTelecom"},
    {"name": "KT",             "industry": "IT/테크", "search": "KT 공식 유튜브 채널"},
    {"name": "LG유플러스",     "industry": "IT/테크", "search": "LG유플러스 공식"},
    {"name": "네이버",         "industry": "IT/테크", "handle": "NAVER"},
    {"name": "카카오",         "industry": "IT/테크", "search": "카카오 Kakao 공식채널"},
    {"name": "SK하이닉스",     "industry": "IT/테크", "handle": "SKhynix"},
    {"name": "삼성SDS",        "industry": "IT/테크", "search": "삼성SDS 공식"},
    {"name": "LG CNS",         "industry": "IT/테크", "search": "LG CNS 공식"},
    {"name": "토스",           "industry": "IT/테크", "search": "토스 Toss 공식"},
    {"name": "카카오뱅크",     "industry": "IT/테크", "search": "카카오뱅크 공식"},
    {"name": "카카오페이",     "industry": "IT/테크", "search": "카카오페이 공식"},
    {"name": "배달의민족",     "industry": "IT/테크", "search": "배달의민족 baemin 공식"},
    {"name": "당근마켓",       "industry": "IT/테크", "search": "당근 공식 채널"},
    {"name": "삼성전기",       "industry": "IT/테크", "search": "삼성전기 공식"},
    {"name": "LG이노텍",       "industry": "IT/테크", "search": "LG이노텍 공식"},
    {"name": "현대오토에버",   "industry": "IT/테크", "search": "현대오토에버 공식"},
    {"name": "네이버클라우드", "industry": "IT/테크", "search": "네이버클라우드 공식"},
    {"name": "SK C&C",         "industry": "IT/테크", "search": "SK C&C 공식"},

    # ────────────────────────────────
    # 금융/핀테크 (20)
    # ────────────────────────────────
    {"name": "KB국민은행",   "industry": "금융/핀테크", "search": "KB국민은행 공식"},
    {"name": "신한은행",     "industry": "금융/핀테크", "search": "신한은행 공식"},
    {"name": "하나은행",     "industry": "금융/핀테크", "search": "하나은행 공식"},
    {"name": "우리은행",     "industry": "금융/핀테크", "search": "우리은행 공식"},
    {"name": "NH농협은행",   "industry": "금융/핀테크", "search": "NH농협은행 공식"},
    {"name": "IBK기업은행",  "industry": "금융/핀테크", "search": "IBK기업은행 공식"},
    {"name": "삼성생명",     "industry": "금융/핀테크", "search": "삼성생명 공식"},
    {"name": "교보생명",     "industry": "금융/핀테크", "search": "교보생명 공식"},
    {"name": "한화생명",     "industry": "금융/핀테크", "search": "한화생명 공식"},
    {"name": "미래에셋증권", "industry": "금융/핀테크", "search": "미래에셋증권 공식"},
    {"name": "한국투자증권", "industry": "금융/핀테크", "search": "한국투자증권 공식"},
    {"name": "NH투자증권",   "industry": "금융/핀테크", "search": "NH투자증권 공식"},
    {"name": "KB증권",       "industry": "금융/핀테크", "search": "KB증권 공식"},
    {"name": "삼성화재",     "industry": "금융/핀테크", "search": "삼성화재 공식"},
    {"name": "DB손해보험",   "industry": "금융/핀테크", "search": "DB손해보험 공식"},
    {"name": "현대해상",     "industry": "금융/핀테크", "search": "현대해상 공식"},
    {"name": "키움증권",     "industry": "금융/핀테크", "search": "키움증권 공식"},
    {"name": "메리츠화재",   "industry": "금융/핀테크", "search": "메리츠화재 공식"},
    {"name": "신한금융그룹", "industry": "금융/핀테크", "search": "신한금융그룹 공식"},
    {"name": "KB금융그룹",   "industry": "금융/핀테크", "search": "KB금융그룹 공식"},

    # ────────────────────────────────
    # 유통/리테일 (20)
    # ────────────────────────────────
    {"name": "롯데쇼핑",            "industry": "유통/리테일", "search": "롯데쇼핑 공식"},
    {"name": "신세계백화점",         "industry": "유통/리테일", "search": "신세계백화점 공식"},
    {"name": "현대백화점",           "industry": "유통/리테일", "search": "현대백화점 공식"},
    {"name": "GS리테일",             "industry": "유통/리테일", "search": "GS리테일 GS25 공식"},
    {"name": "이마트",               "industry": "유통/리테일", "search": "이마트 공식"},
    {"name": "CJ온스타일",           "industry": "유통/리테일", "search": "CJ온스타일 공식"},
    {"name": "SSG닷컴",              "industry": "유통/리테일", "search": "SSG닷컴 공식"},
    {"name": "11번가",               "industry": "유통/리테일", "search": "11번가 공식"},
    {"name": "G마켓",                "industry": "유통/리테일", "search": "G마켓 공식"},
    {"name": "무신사",               "industry": "유통/리테일", "search": "무신사 공식"},
    {"name": "올리브영",             "industry": "유통/리테일", "search": "올리브영 CJ올리브영 공식"},
    {"name": "홈플러스",             "industry": "유통/리테일", "search": "홈플러스 공식"},
    {"name": "롯데마트",             "industry": "유통/리테일", "search": "롯데마트 공식"},
    {"name": "스타벅스코리아",       "industry": "유통/리테일", "search": "스타벅스코리아 공식"},
    {"name": "맥도날드코리아",       "industry": "유통/리테일", "search": "맥도날드코리아 공식"},
    {"name": "롯데ON",               "industry": "유통/리테일", "search": "롯데온 롯데ON 공식"},
    {"name": "카카오스타일(지그재그)","industry": "유통/리테일", "search": "지그재그 카카오스타일 공식"},
    {"name": "컬리",                 "industry": "유통/리테일", "search": "마켓컬리 공식"},
    {"name": "오아시스마켓",         "industry": "유통/리테일", "search": "오아시스마켓 공식"},
    {"name": "BGF리테일(CU)",        "industry": "유통/리테일", "search": "CU BGF리테일 공식"},

    # ────────────────────────────────
    # F&B (20)
    # ────────────────────────────────
    {"name": "CJ제일제당",   "industry": "F&B", "search": "CJ제일제당 공식"},
    {"name": "오뚜기",       "industry": "F&B", "search": "오뚜기 공식"},
    {"name": "농심",         "industry": "F&B", "search": "농심 공식"},
    {"name": "오리온",       "industry": "F&B", "search": "오리온 공식"},
    {"name": "롯데칠성음료", "industry": "F&B", "search": "롯데칠성음료 공식"},
    {"name": "빙그레",       "industry": "F&B", "search": "빙그레 공식"},
    {"name": "하이트진로",   "industry": "F&B", "search": "하이트진로 공식"},
    {"name": "오비맥주",     "industry": "F&B", "search": "OB 오비맥주 공식"},
    {"name": "매일유업",     "industry": "F&B", "search": "매일유업 공식"},
    {"name": "동원F&B",      "industry": "F&B", "search": "동원F&B 공식"},
    {"name": "대상",         "industry": "F&B", "search": "대상 청정원 공식"},
    {"name": "풀무원",       "industry": "F&B", "search": "풀무원 공식"},
    {"name": "삼양식품",     "industry": "F&B", "search": "삼양식품 불닭 공식"},
    {"name": "해태제과",     "industry": "F&B", "search": "해태제과 공식"},
    {"name": "롯데웰푸드",   "industry": "F&B", "search": "롯데웰푸드 롯데제과 공식"},
    {"name": "SPC그룹",      "industry": "F&B", "search": "파리바게뜨 SPC 공식"},
    {"name": "남양유업",     "industry": "F&B", "search": "남양유업 공식"},
    {"name": "서울우유",     "industry": "F&B", "search": "서울우유 공식"},
    {"name": "동서식품",     "industry": "F&B", "search": "동서식품 공식"},
    {"name": "코카콜라코리아","industry": "F&B", "search": "코카콜라 코리아 공식"},

    # ────────────────────────────────
    # 엔터테인먼트 (20)
    # ────────────────────────────────
    {"name": "HYBE",                   "industry": "엔터테인먼트", "handle": "HYBE_official"},
    {"name": "SM엔터테인먼트",          "industry": "엔터테인먼트", "handle": "smtown"},
    {"name": "YG엔터테인먼트",          "industry": "엔터테인먼트", "handle": "YGEntertainment"},
    {"name": "JYP엔터테인먼트",         "industry": "엔터테인먼트", "handle": "officialjyp"},
    {"name": "CJ ENM",                 "industry": "엔터테인먼트", "search": "CJ ENM 공식"},
    {"name": "카카오엔터테인먼트",      "industry": "엔터테인먼트", "search": "카카오엔터테인먼트 공식"},
    {"name": "넷플릭스 코리아",         "industry": "엔터테인먼트", "handle": "NetflixKorea"},
    {"name": "스튜디오드래곤",          "industry": "엔터테인먼트", "search": "스튜디오드래곤 공식"},
    {"name": "빅히트뮤직",              "industry": "엔터테인먼트", "search": "빅히트뮤직 공식"},
    {"name": "어도어(ADOR)",            "industry": "엔터테인먼트", "search": "ADOR 어도어 공식"},
    {"name": "플레디스엔터테인먼트",    "industry": "엔터테인먼트", "search": "플레디스 PLEDIS 공식"},
    {"name": "FNC엔터테인먼트",         "industry": "엔터테인먼트", "search": "FNC엔터테인먼트 공식"},
    {"name": "큐브엔터테인먼트",        "industry": "엔터테인먼트", "search": "큐브엔터테인먼트 CUBE 공식"},
    {"name": "스타쉽엔터테인먼트",      "industry": "엔터테인먼트", "search": "스타쉽엔터테인먼트 공식"},
    {"name": "위에화엔터테인먼트",      "industry": "엔터테인먼트", "search": "위에화엔터테인먼트 공식"},
    {"name": "쇼박스",                 "industry": "엔터테인먼트", "search": "쇼박스 Showbox 공식"},
    {"name": "NEW(넥스트엔터테인먼트)", "industry": "엔터테인먼트", "search": "NEW 영화 공식"},
    {"name": "롯데엔터테인먼트",        "industry": "엔터테인먼트", "search": "롯데엔터테인먼트 공식"},
    {"name": "왓챠",                   "industry": "엔터테인먼트", "search": "왓챠 WATCHA 공식"},
    {"name": "웨이브(wavve)",           "industry": "엔터테인먼트", "search": "웨이브 wavve 공식"},

    # ────────────────────────────────
    # 자동차/모빌리티 (20)
    # ────────────────────────────────
    {"name": "현대자동차",    "industry": "자동차/모빌리티", "search": "현대자동차 HMG 공식채널"},
    {"name": "기아",          "industry": "자동차/모빌리티", "search": "기아 Kia 공식"},
    {"name": "제네시스",      "industry": "자동차/모빌리티", "handle": "Genesis"},
    {"name": "한국GM(쉐보레)","industry": "자동차/모빌리티", "search": "쉐보레코리아 한국GM 공식"},
    {"name": "KG모빌리티",    "industry": "자동차/모빌리티", "search": "KG모빌리티 쌍용자동차 공식"},
    {"name": "르노코리아",    "industry": "자동차/모빌리티", "search": "르노코리아자동차 공식"},
    {"name": "현대모비스",    "industry": "자동차/모빌리티", "search": "현대모비스 공식"},
    {"name": "HL만도",        "industry": "자동차/모빌리티", "search": "HL만도 만도 공식"},
    {"name": "한국타이어",    "industry": "자동차/모빌리티", "search": "한국타이어 Hankook 공식"},
    {"name": "금호타이어",    "industry": "자동차/모빌리티", "search": "금호타이어 Kumho 공식"},
    {"name": "넥센타이어",    "industry": "자동차/모빌리티", "search": "넥센타이어 Nexen 공식"},
    {"name": "현대위아",      "industry": "자동차/모빌리티", "search": "현대위아 공식"},
    {"name": "현대트랜시스",  "industry": "자동차/모빌리티", "search": "현대트랜시스 공식"},
    {"name": "한온시스템",    "industry": "자동차/모빌리티", "search": "한온시스템 Hanon 공식"},
    {"name": "현대로템",      "industry": "자동차/모빌리티", "search": "현대로템 공식"},
    {"name": "SK렌터카",      "industry": "자동차/모빌리티", "search": "SK렌터카 공식"},
    {"name": "롯데렌터카",    "industry": "자동차/모빌리티", "search": "롯데렌터카 공식"},
    {"name": "GS칼텍스",      "industry": "자동차/모빌리티", "search": "GS칼텍스 공식"},
    {"name": "SK에너지",      "industry": "자동차/모빌리티", "search": "SK에너지 공식"},
    {"name": "현대오토에버",  "industry": "자동차/모빌리티", "search": "현대오토에버 자동차 공식"},

    # ────────────────────────────────
    # 패션/뷰티 (20)
    # ────────────────────────────────
    {"name": "아모레퍼시픽",         "industry": "패션/뷰티", "search": "아모레퍼시픽 공식"},
    {"name": "LG생활건강",           "industry": "패션/뷰티", "search": "LG생활건강 공식"},
    {"name": "이니스프리",           "industry": "패션/뷰티", "handle": "innisfree"},
    {"name": "설화수",               "industry": "패션/뷰티", "handle": "sulwhasoo"},
    {"name": "라네즈",               "industry": "패션/뷰티", "handle": "laneige"},
    {"name": "마몽드",               "industry": "패션/뷰티", "search": "마몽드 Mamonde 공식"},
    {"name": "헤라",                 "industry": "패션/뷰티", "search": "헤라 HERA 공식"},
    {"name": "닥터자르트",           "industry": "패션/뷰티", "handle": "drjart"},
    {"name": "클리오",               "industry": "패션/뷰티", "search": "CLIO 클리오 공식"},
    {"name": "에이피알(메디큐브)",   "industry": "패션/뷰티", "search": "에이피알 메디큐브 APR 공식"},
    {"name": "VT코스메틱",           "industry": "패션/뷰티", "search": "VT코스메틱 공식"},
    {"name": "토리든",               "industry": "패션/뷰티", "search": "토리든 TORRIDEN 공식"},
    {"name": "애경산업",             "industry": "패션/뷰티", "search": "애경산업 공식"},
    {"name": "코스맥스",             "industry": "패션/뷰티", "search": "코스맥스 공식"},
    {"name": "파마리서치",           "industry": "패션/뷰티", "search": "파마리서치 공식"},
    {"name": "네이처리퍼블릭",       "industry": "패션/뷰티", "search": "네이처리퍼블릭 공식"},
    {"name": "스킨푸드",             "industry": "패션/뷰티", "search": "스킨푸드 SKINFOOD 공식"},
    {"name": "미샤(에이블씨앤씨)",   "industry": "패션/뷰티", "search": "미샤 MISSHA 공식"},
    {"name": "이니스프리(글로벌)",   "industry": "패션/뷰티", "search": "innisfree global 공식"},
    {"name": "조성아뷰티",           "industry": "패션/뷰티", "search": "조성아뷰티 공식"},

    # ────────────────────────────────
    # 미디어/방송 (20)
    # ────────────────────────────────
    {"name": "KBS",       "industry": "미디어/방송", "handle": "KBS"},
    {"name": "MBC",       "industry": "미디어/방송", "search": "MBC 공식 유튜브"},
    {"name": "SBS",       "industry": "미디어/방송", "search": "SBS 공식 유튜브"},
    {"name": "JTBC",      "industry": "미디어/방송", "handle": "jtbc"},
    {"name": "tvN",       "industry": "미디어/방송", "search": "tvN 공식"},
    {"name": "OCN",       "industry": "미디어/방송", "search": "OCN 공식"},
    {"name": "MBN",       "industry": "미디어/방송", "search": "MBN 공식"},
    {"name": "YTN",       "industry": "미디어/방송", "search": "YTN 공식"},
    {"name": "연합뉴스TV","industry": "미디어/방송", "search": "연합뉴스TV 공식"},
    {"name": "채널A",     "industry": "미디어/방송", "search": "채널A Channel A 공식"},
    {"name": "TV조선",    "industry": "미디어/방송", "search": "TV조선 공식"},
    {"name": "EBS",       "industry": "미디어/방송", "search": "EBS 공식"},
    {"name": "아리랑TV",  "industry": "미디어/방송", "search": "아리랑TV Arirang 공식"},
    {"name": "KBS WORLD", "industry": "미디어/방송", "handle": "KBSWorldTV"},
    {"name": "조선일보",  "industry": "미디어/방송", "search": "조선일보 공식 유튜브"},
    {"name": "중앙일보",  "industry": "미디어/방송", "search": "중앙일보 공식"},
    {"name": "한겨레",    "industry": "미디어/방송", "search": "한겨레 공식"},
    {"name": "동아일보",  "industry": "미디어/방송", "search": "동아일보 공식"},
    {"name": "민음사",    "industry": "미디어/방송", "search": "민음사 공식"},
    {"name": "비매거진",  "industry": "미디어/방송", "search": "비매거진 B Magazine 공식"},

    # ────────────────────────────────
    # 게임 (20)
    # ────────────────────────────────
    {"name": "넥슨",                   "industry": "게임", "search": "넥슨 Nexon Korea 공식"},
    {"name": "엔씨소프트",             "industry": "게임", "search": "엔씨소프트 NC 공식"},
    {"name": "크래프톤",               "industry": "게임", "handle": "krafton"},
    {"name": "스마일게이트",           "industry": "게임", "search": "스마일게이트 Smilegate 공식"},
    {"name": "넷마블",                 "industry": "게임", "search": "넷마블 Netmarble 공식"},
    {"name": "카카오게임즈",           "industry": "게임", "search": "카카오게임즈 공식"},
    {"name": "컴투스",                 "industry": "게임", "search": "컴투스 Com2uS 공식"},
    {"name": "데브시스터즈",           "industry": "게임", "search": "데브시스터즈 DevSisters 공식"},
    {"name": "펄어비스",               "industry": "게임", "search": "펄어비스 Pearl Abyss 공식"},
    {"name": "위메이드",               "industry": "게임", "search": "위메이드 Wemade 공식"},
    {"name": "NHN",                   "industry": "게임", "search": "NHN 공식"},
    {"name": "라인게임즈",             "industry": "게임", "search": "라인게임즈 LINE Games 공식"},
    {"name": "엔픽셀",                 "industry": "게임", "search": "엔픽셀 Npixel 공식"},
    {"name": "그라비티",               "industry": "게임", "search": "그라비티 Gravity 공식"},
    {"name": "조이시티",               "industry": "게임", "search": "조이시티 JOYCITY 공식"},
    {"name": "4:33(포세삼)",           "industry": "게임", "search": "4:33 공식 게임"},
    {"name": "선데이토즈",             "industry": "게임", "search": "선데이토즈 SundayToz 공식"},
    {"name": "블루아카이브(넥슨게임즈)","industry": "게임", "search": "블루아카이브 공식"},
    {"name": "배틀그라운드(크래프톤)", "industry": "게임", "search": "PUBG BATTLEGROUNDS 공식"},
    {"name": "로스트아크(스마일게이트)","industry": "게임", "search": "로스트아크 LOSTARK 공식"},

    # ────────────────────────────────
    # 항공/물류 (20)
    # ────────────────────────────────
    {"name": "대한항공",       "industry": "항공/물류", "handle": "KoreanAir"},
    {"name": "아시아나항공",   "industry": "항공/물류", "search": "아시아나항공 공식"},
    {"name": "제주항공",       "industry": "항공/물류", "search": "제주항공 공식"},
    {"name": "진에어",         "industry": "항공/물류", "search": "진에어 공식"},
    {"name": "에어부산",       "industry": "항공/물류", "search": "에어부산 공식"},
    {"name": "티웨이항공",     "industry": "항공/물류", "search": "티웨이항공 공식"},
    {"name": "이스타항공",     "industry": "항공/물류", "search": "이스타항공 공식"},
    {"name": "에어서울",       "industry": "항공/물류", "search": "에어서울 공식"},
    {"name": "CJ대한통운",     "industry": "항공/물류", "search": "CJ대한통운 공식"},
    {"name": "롯데글로벌로지스","industry": "항공/물류", "search": "롯데글로벌로지스 공식"},
    {"name": "한진택배",       "industry": "항공/물류", "search": "한진택배 공식"},
    {"name": "현대글로비스",   "industry": "항공/물류", "search": "현대글로비스 공식"},
    {"name": "쿠팡로지스틱스", "industry": "항공/물류", "search": "쿠팡로지스틱스 공식"},
    {"name": "범한판토스",     "industry": "항공/물류", "search": "범한판토스 공식"},
    {"name": "인천국제공항공사","industry": "항공/물류", "search": "인천국제공항 공식"},
    {"name": "한국공항공사",   "industry": "항공/물류", "search": "한국공항공사 공식"},
    {"name": "우체국물류지원단","industry": "항공/물류", "search": "우체국 EMS 공식"},
    {"name": "롯데택배",       "industry": "항공/물류", "search": "롯데택배 공식"},
    {"name": "로젠택배",       "industry": "항공/물류", "search": "로젠택배 공식"},
    {"name": "쿠팡",           "industry": "항공/물류", "search": "쿠팡 Coupang 공식"},

    # ────────────────────────────────
    # 교육/에듀테크 (10)
    # ────────────────────────────────
    {"name": "메가스터디",   "industry": "교육/에듀테크", "search": "메가스터디 공식"},
    {"name": "이투스",       "industry": "교육/에듀테크", "search": "이투스 공식"},
    {"name": "클래스101",    "industry": "교육/에듀테크", "search": "클래스101 공식"},
    {"name": "패스트캠퍼스", "industry": "교육/에듀테크", "search": "패스트캠퍼스 공식"},
    {"name": "데이원컴퍼니", "industry": "교육/에듀테크", "search": "데이원컴퍼니 공식"},
    {"name": "뤼이드",       "industry": "교육/에듀테크", "search": "뤼이드 Riiid 공식"},
    {"name": "산타토익",     "industry": "교육/에듀테크", "search": "산타토익 공식"},
    {"name": "밀리의서재",   "industry": "교육/에듀테크", "search": "밀리의서재 공식"},
    {"name": "웅진씽크빅",   "industry": "교육/에듀테크", "search": "웅진씽크빅 공식"},
    {"name": "천재교육",     "industry": "교육/에듀테크", "search": "천재교육 공식"},

    # ────────────────────────────────
    # 의료/헬스케어 (10)
    # ────────────────────────────────
    {"name": "셀트리온",     "industry": "의료/헬스케어", "search": "셀트리온 Celltrion 공식"},
    {"name": "한미약품",     "industry": "의료/헬스케어", "search": "한미약품 공식"},
    {"name": "유한양행",     "industry": "의료/헬스케어", "search": "유한양행 공식"},
    {"name": "종근당",       "industry": "의료/헬스케어", "search": "종근당 공식"},
    {"name": "대웅제약",     "industry": "의료/헬스케어", "search": "대웅제약 공식"},
    {"name": "GC녹십자",     "industry": "의료/헬스케어", "search": "GC녹십자 공식"},
    {"name": "일동제약",     "industry": "의료/헬스케어", "search": "일동제약 공식"},
    {"name": "동화약품",     "industry": "의료/헬스케어", "search": "동화약품 공식"},
    {"name": "보령제약",     "industry": "의료/헬스케어", "search": "보령제약 공식"},
    {"name": "에이치앤비",   "industry": "의료/헬스케어", "search": "H&B 헬스앤뷰티 공식"},

    # ────────────────────────────────
    # 크리에이터/1인미디어 — 우선 수집 채널
    # ────────────────────────────────
    {"name": "eo코리아",         "industry": "크리에이터/1인미디어", "search": "eo코리아 공식"},
    {"name": "셜록현준",         "industry": "크리에이터/1인미디어", "search": "셜록현준 공식"},
    {"name": "채널톡",           "industry": "크리에이터/1인미디어", "search": "채널톡 ChannelTalk 공식"},
    {"name": "노희영",           "industry": "크리에이터/1인미디어", "search": "노희영 공식"},
    {"name": "신사임당",         "industry": "크리에이터/1인미디어", "search": "신사임당 공식"},
    {"name": "이청아",           "industry": "크리에이터/1인미디어", "search": "이청아 공식"},
    {"name": "이동진의 영화당",  "industry": "미디어/방송",           "search": "이동진의 영화당 공식"},
    {"name": "의사이상욱",       "industry": "의료/헬스케어",         "search": "의사이상욱 공식"},
    {"name": "앨리스펑크",       "industry": "크리에이터/1인미디어", "search": "앨리스펑크 공식"},
    {"name": "안될과학",         "industry": "교육/에듀테크",         "search": "안될과학 공식"},

    # ────────────────────────────────
    # 모션그래픽 스튜디오 — 필수 수집
    # ────────────────────────────────
    {"name": "하이플리",       "industry": "크리에이터/1인미디어", "search": "하이플리 HiFlly 공식"},
    {"name": "헤이메이트",     "industry": "크리에이터/1인미디어", "search": "헤이메이트 heymate 공식"},
    {"name": "엔돌핀스튜디오", "industry": "크리에이터/1인미디어", "search": "엔돌핀스튜디오 공식"},
]
