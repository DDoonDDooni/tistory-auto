# DBA&I 티스토리 자동 포스팅 프로젝트

## 프로젝트 개요
Python + Selenium으로 티스토리에 자동 포스팅하는 자동화 도구입니다.
Tistory Open API는 2024년 2월 종료되어 브라우저 자동화 방식을 사용합니다.

## 환경 정보
- OS: Windows
- 프로젝트 경로: D:\DoubleD\tistory_auto
- Python: 로컬 설치
- 로그인 방식: 카카오 소셜 로그인 (2단계 인증 없음)
- 에디터: VSCode + Claude Code

## 블로그 정보
- 블로그명: DBA&I (DBA + AI)
- 플랫폼: 티스토리
- 주제: DB 기술(Oracle/PostgreSQL/MySQL/MariaDB/EDB/ExaCC), AI Agent/MCP/RAG, 웹 개발, 일상
- 수익 모델: 구글 애드센스
- 운영자: Oracle/PostgreSQL 전문 DBA (Oracle-PG 마이그레이션, 성능 최적화, HA/DR, RMAN, ExaCC)

## 포스팅 카테고리 목록
제목 prefix `[카테고리]`에 사용하는 값 목록:
- **DB**: `Oracle` / `ExaCC` / `PostgreSQL` / `EDB` / `MySQL` / `MariaDB` / `Altibase`
- **AWS**: `Aurora MySQL` / `Aurora PostgreSQL`
- **AI**: `AI개발` / `AI자동화`

> **제목 형식**: `[카테고리] 제목 내용` — 전체 45자 이내 (`[카테고리]` 포함 기준)
> 예시: `[Oracle] ORA-1000 예방을 위한 핵심 가이드`

## 디렉토리 구조
```
D:\DoubleD\tistory_auto\
├── CLAUDE.md                    ← Claude Code 컨텍스트 (이 파일)
├── SETUP_GUIDE.md               ← 초기 설정 가이드
├── tistory_auto.code-workspace  ← VSCode 워크스페이스 (posts\ 폴더 연동 포함)
├── config.json                  ← 카카오 계정, 블로그명 설정
├── 01_login_test.py             ← 카카오 로그인 동작 테스트
├── 02_post.py                   ← 메인: post.md → HTML 변환 → 티스토리 포스팅
└── posts\
    └── post.md                  ← 포스팅 원고 (마크다운 + frontmatter)
```

> **주의:** `02_post.py`는 `posts/post.md` 경로를 읽습니다 (47번 줄 `POST_FILE = "posts/post.md"`).
> 원고는 반드시 `posts/post.md`에 작성할 것. 루트의 `post.md`는 사용되지 않음.

## config.json 구조
```json
{
  "kakao_email": "카카오 이메일",
  "kakao_password": "카카오 비밀번호",
  "blog_name": "블로그명 (xxxx.tistory.com의 xxxx 부분)",
  "default_category": "DB 기술",
  "default_visibility": "0"
}
```

## posts/post.md frontmatter 포맷
```markdown
---
title: "[Oracle] 포스팅 제목"
tags: 태그1,태그2,태그3
category: DB 기술
visibility: 0
---
요약: 핵심 내용 1~2문장 요약

## 소제목

본문 내용...

추천 해시태그: #태그1 #태그2 #태그3
```
- visibility: 0 = 임시저장, 3 = 발행
- tags: 쉼표 구분, 공백 없이
- 요약: 으로 시작하는 줄 → 주황 TL;DR 박스로 자동 변환
- 추천 해시태그: 줄 → 주황 칩 박스로 자동 변환

## 02_post.py 처리 흐름
```
post.md 읽기 (frontmatter 파싱)
    ↓
마크다운 → 모던 스타일 HTML 변환 (markdown2)
    ↓
Chrome 실행 (Selenium + webdriver-manager)
    ↓
티스토리 카카오 소셜 로그인
    ↓
글쓰기 에디터 HTML 모드 전환
    ↓
제목 / 본문(HTML) / 태그 / 카테고리 자동 입력
    ↓
임시저장(0) 또는 발행(3)
```

## 스타일 구현 방식
**모든 스타일은 인라인 스타일(`style=""`)로 적용** — TinyMCE가 `<style>` 블록의 class 기반 CSS를 저장 시 제거하기 때문.

| 마크다운 요소 | 변환 결과 |
|-------------|----------|
| ## 소제목 | 주황 왼쪽 바 + 그라디언트 배경 (인라인 스타일) |
| ### 소제목 | 슬레이트 왼쪽 바 (인라인 스타일) |
| 요약: 내용 | 주황 요약 박스 — `📌  요약` 라벨 포함 span 직접 생성 |
| 코드블록 (일반) | 다크 테마 (#0d1117) + 언어 라벨 span 직접 삽입 |
| 코드블록 (SQL) | `<div>` 기반 하이라이팅 — 줄 번호 + `white-space:pre` |
| 표 | 다크 헤더(`#1f2937`) + 셀 border (인라인 스타일) |
| 인용구 | 파란 왼쪽 선 + 하늘색 배경 (인라인 스타일) |
| 추천 해시태그: | 주황 칩 박스 (인라인 스타일) |

> **스타일 적용 함수**: `_apply_inline_styles(html)` — markdown2 변환 후 h2/h3/table/th/td/blockquote/pre/code 태그에 인라인 스타일 일괄 적용
>
> **SQL 코드블록 구현 방식**:
> 1. `markdown2` 2.5.5 버그 → ` ```sql ` 블록을 markdown2 실행 **전에 선추출** (placeholder 방식)
> 2. TinyMCE `<pre><code>` 내부 `<span>` 이스케이프 문제 → `<div>` + `display:flex` + `white-space:pre` 구조로 우회
> 3. 언어 라벨: pseudo-element 대신 `<span style="position:absolute">` 직접 삽입

## 글쓰기 페이지 이동
- **확인된 URL**: `https://{BLOG_NAME}.tistory.com/manage/newpost`
- `manage/post/write` 는 잘못된 URL (권한 오류 발생)

## Selenium 셀렉터 목록 (TinyMCE 새 에디터 기준)
| 대상 | 방식 | 비고 |
|------|------|------|
| 카카오 로그인 버튼 | `a.btn_login.link_kakao_id` | JS click |
| 카카오 이메일 입력 | `input#loginId` | |
| 카카오 비밀번호 입력 | `input#password` | |
| 카카오 로그인 제출 | `button.btn_g.highlight.submit` | |
| 포스트 제목 입력 | pyautogui viewport (300, 185) | wait.until 금지 |
| 본문 주입 | `#editor-tistory_ifr` iframe body.innerHTML 직접 주입 | |
| 태그 입력 | `input#tagText` + JS KeyboardEvent | |
| 카테고리 버튼 | 텍스트 매칭 `카테고리` | JS click |
| 카테고리 항목 | `[role="option"]` + button 텍스트 폴백 | li 없음 |
| 임시저장 | pyautogui (x≈1047, 하단 -34px) | |
| 발행(완료) | pyautogui (x≈1163, 하단 -34px) | |

셀렉터가 깨지면 `error_screenshot.png` → `debug_before_save.png` 먼저 확인할 것.

## 실행 명령어
```bash
cd D:\DoubleD\tistory_auto
pip install selenium webdriver-manager markdown2 python-frontmatter
python 01_login_test.py
python 02_post.py
```

## 전체 워크플로우

### A. 직접 원고 작성
```
Claude Code에서 Step 3 프롬프트로 원고 작성 요청
    ↓
posts/post.md 생성 확인
    ↓
python 02_post.py
    ↓
티스토리 관리자에서 발행
```

### B. Claude 앱 대화 → 포스팅 원고 변환
```
Claude 앱에서 기술 대화 내용 복사
    ↓
Claude Code 채팅에 붙여넣으며 아래 요청:
"이 대화 내용으로 posts/post.md 포스팅 원고 작성해줘."
    ↓
Claude Code가 카테고리 선택 질문:
"어떤 카테고리로 작성할까요?
 Oracle / ExaCC / PostgreSQL / EDB / MySQL / MariaDB / Altibase
 Aurora MySQL / Aurora PostgreSQL / AI개발 / AI자동화"
    ↓
카테고리 선택 답변 → posts/post.md 자동 생성 (제목: [카테고리] 제목)
    ↓
python 02_post.py
    ↓
티스토리 관리자에서 발행
```

## Claude Code 작업 가이드

### 자주 쓰는 작업 유형
1. 셀렉터 수정: 티스토리 에디터 업데이트로 CSS 셀렉터가 바뀐 경우
2. 스타일 추가: STYLE 변수에 CSS 추가
3. 변환 규칙 추가: md_to_styled_html() 함수 내에 전처리 로직 추가
4. 포스팅 원고 작성: posts/post.md에 마크다운 형식으로 작성

### 코드 수정 원칙
- 각 기능은 독립 함수로 분리 (로그인/제목/본문/태그/카테고리/저장)
- 셀렉터 변경 시 해당 함수만 수정
- 새 스타일은 파일 상단 `_IS_*` 인라인 스타일 상수에만 추가 (`STYLE` 블록 없음)
- 에러 발생 시 항상 error_screenshot.png 저장 로직 유지

### 포스팅 원고 작성 규칙
- **제목 형식**: `[카테고리] 제목 내용` 형식으로 시작 (전체 45자 이내, `[카테고리]` 포함 기준)
  - 카테고리 목록에서 반드시 1개 선택하여 prefix로 사용
  - 예: `[Oracle] ORA-1000 예방을 위한 핵심 가이드`
- **원고 작성 요청 시**: 카테고리를 먼저 물어볼 것
  - "어떤 카테고리로 작성할까요? (Oracle / ExaCC / PostgreSQL / EDB / MySQL / MariaDB / Altibase / Aurora MySQL / Aurora PostgreSQL / AI개발 / AI자동화)"
- 구조: 문제 상황 → 원인 분석 → 해결 가이드 → 추가 팁/FAQ → 마무리
- 소제목: ## 또는 ### 사용
- 요약: 글 최상단 "요약: 내용" 형태
- 해시태그: 글 최하단 "추천 해시태그: #태그1 #태그2" 형태
- 코드블록: 언어명 반드시 명시
- **기술 전문 용어는 영어로 작성**: DB 오브젝트명, 파라미터, 명령어, 에러코드 등은 영어 원문 사용
  - 예: 테이블스페이스 → tablespace, 인덱스 → index, 파티션 → partition
  - 예: 아카이브 로그 → archive log, 리두 로그 → redo log
  - 예: 세그먼트 → segment, 익스텐트 → extent, 블록 → block
  - 단, 일반 설명 문장은 한국어로 작성 (전문 용어만 영어 유지)
- 목표 글자 수: 2,000~3,000자

---

## Step 3. 포스팅 원고 작성 프롬프트

글 작성이 필요할 때 쓰는 프롬프트예요.
```
posts/post.md 파일에 아래 조건으로 포스팅 원고를 작성해줘.

작성 전에 아래 카테고리 중 하나를 선택해줘:
[DB] Oracle / ExaCC / PostgreSQL / EDB / MySQL / MariaDB / Altibase
[AWS] Aurora MySQL / Aurora PostgreSQL
[AI] AI개발 / AI자동화

선택한 카테고리를 제목 맨 앞에 [카테고리] 형식으로 붙여줘.
예: [Oracle] ORA-1000 예방을 위한 핵심 가이드

주요 키워드: [키워드 입력]
필수 형태소: [형태소1, 형태소2, 형태소3]
티스토리 카테고리: [DB 기술 / AI / 웹 개발 / 일상]
목표 글자 수: 2500자
추가 내용: [실무 경험, 명령어, 수치 등 선택 입력]

frontmatter 포함해서 작성하고,
요약: 으로 시작하는 TL;DR 박스와
추천 해시태그: 로 끝나는 태그 줄도 반드시 포함해줘.
```

---

## Step 4. 포스팅 실행 프롬프트

원고 확인 후 올릴 때 쓰는 프롬프트예요.
```
posts/post.md 내용 확인하고 이상 없으면
터미널에서 python 02_post.py 실행해줘.

실행 중 오류나면 error_screenshot.png 보고
CLAUDE.md의 셀렉터 목록 참고해서 바로 수정 후 재실행해줘.
```

---

## Step 5. 오류 수정 프롬프트

셀렉터가 깨졌을 때 쓰는 프롬프트예요.
```
python 02_post.py 실행 중 오류가 발생했어.
오류 내용: [오류 메시지 붙여넣기]

error_screenshot.png 확인하고
CLAUDE.md 셀렉터 목록 참고해서
02_post.py에서 해당 셀렉터 찾아 수정해줘.
수정 후 바로 재실행해줘.
```

---

## Step 6. 스타일 수정 프롬프트

디자인 바꾸고 싶을 때 쓰는 프롬프트예요.
```
02_post.py의 STYLE 변수에서 아래 항목을 수정해줘.

변경 내용: [예: 코드블록 배경색을 #1e1e1e로 변경]
추가 내용: [예: h2 소제목 폰트 사이즈 22px로 변경]

수정 후 변경된 CSS 부분만 요약해서 알려줘.
```
