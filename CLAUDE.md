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
title: "포스팅 제목 (35자 이내)"
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

## CSS 스타일 적용 현황
| 마크다운 요소 | 변환 결과 |
|-------------|----------|
| ## 소제목 | 주황 왼쪽 바 + 그라디언트 배경 |
| ### 소제목 | 슬레이트 왼쪽 바 |
| 요약: 내용 | 주황 TL;DR 박스 (📌 라벨 자동 삽입) |
| 코드블록 | 다크 테마 (#0d1117) + 언어 라벨 |
| 표 | 다크 헤더 + 홀짝 행 배경 + 호버 효과 |
| 인용구 | 파란 왼쪽 선 + 하늘색 배경 |
| 추천 해시태그: | 주황 칩 박스 |

## Selenium CSS 셀렉터 목록
| 대상 | 셀렉터 |
|------|--------|
| 카카오 로그인 버튼 | a.btn_login.link_kakao_id |
| 카카오 이메일 입력 | input#loginId |
| 카카오 비밀번호 입력 | input#password |
| 카카오 로그인 제출 | button.btn_g.highlight.submit |
| 포스트 제목 입력 | input#post-title-inp |
| HTML 모드 전환 | button.editor-mode-html |
| 에디터 (CodeMirror) | .CodeMirror |
| 태그 입력 | input#tagText |
| 카테고리 버튼 | button.btn-category |
| 카테고리 목록 | ul.category-list li |
| 임시저장 버튼 | button.btn-save |
| 발행 버튼 | button.btn-publish |

셀렉터가 깨지면 error_screenshot.png 를 먼저 확인할 것.

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
"이 대화 내용으로 posts/post.md 포스팅 원고 작성해줘. 카테고리: DB 기술"
    ↓
posts/post.md 자동 생성 (추가 비용 없음)
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
- 새 스타일은 STYLE 변수(파일 상단)에만 추가
- 에러 발생 시 항상 error_screenshot.png 저장 로직 유지

### 포스팅 원고 작성 규칙
- 구조: 문제 상황 → 원인 분석 → 해결 가이드 → 추가 팁/FAQ → 마무리
- 소제목: ## 또는 ### 사용
- 요약: 글 최상단 "요약: 내용" 형태
- 해시태그: 글 최하단 "추천 해시태그: #태그1 #태그2" 형태
- 코드블록: 언어명 반드시 명시
- 목표 글자 수: 2,000~3,000자

---

## Step 3. 포스팅 원고 작성 프롬프트

글 작성이 필요할 때 쓰는 프롬프트예요.
```
posts/post.md 파일에 아래 조건으로 포스팅 원고를 작성해줘.

주요 키워드: [키워드 입력]
필수 형태소: [형태소1, 형태소2, 형태소3]
카테고리: [DB 기술 / AI Agent / 웹 개발 / 일상]
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
