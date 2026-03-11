# tistory_auto 프로젝트 진행 상황

## 프로젝트 개요
Python + Selenium으로 티스토리에 자동 포스팅하는 스크립트
- 경로: `D:\DoubleD\tistory_auto`
- 메인: `02_post.py`
- 원고: `posts/post.md`
- GitHub: https://github.com/DDoonDDooni/tistory-auto

---

## 현재 상태 (2026-03-11 기준)

**전체 자동화 완성** — 세션 유지 중이면 `python 02_post.py` 한 번으로 끝

---

## 완료된 작업

### v1 - 기초 구성
- [x] 카카오 소셜 로그인 자동화
- [x] `01_login_test.py` 로그인 테스트 스크립트
- [x] `02_post.py` 포스팅 플로우 구성
- [x] 마크다운 → 모던 스타일 HTML 변환 (`md_to_styled_html`)
- [x] CSS 스타일 (h2/h3, 코드블록, 표, 인용구, 요약박스, 해시태그)
- [x] frontmatter 파싱 (title / tags / category / visibility)

### v2 - 안정화
- [x] 카카오 안티봇 우회: `--disable-blink-features=AutomationControlled` + CDP navigator.webdriver 숨기기
- [x] `wait.until()` 폴링 → Chrome crash → `time.sleep` 전환
- [x] `chrome_profile` 세션 유지 (`--user-data-dir`)
- [x] Chrome Remote Debugging Port 9222 도입 (기존 Chrome 재사용)
- [x] 세션 감지 오탐 수정: `www.tistory.com/manage` → `{BLOG_NAME}.tistory.com/manage`

### v3 - 완전 자동화
- [x] `pyperclip` + `pyautogui` 클립보드 방식으로 ID/PW 자동 입력
- [x] 카카오 계정 선택 페이지 pyautogui 클릭 자동화
- [x] `chrome_profile`에 기기 신뢰 저장 → 이후 2FA 불필요

### v4 - TinyMCE 대응 + 스타일 고도화
- [x] 에디터 전환: CodeMirror → **TinyMCE** (전체 셀렉터 재작성)
- [x] 제목 입력: pyautogui viewport 좌표 클릭 (300, 185)
- [x] 본문 주입: `tinymce.activeEditor.setContent()` API
- [x] 태그 입력: `input#tagText` + JS nativeInputValueSetter + KeyboardEvent
- [x] 카테고리 선택: `[role="option"]` 셀렉터 (5단계 폴백)
- [x] 임시저장/발행: pyautogui 하단 바 좌표 폴백 (x≈1047/1163, 하단 -34px)
- [x] 글쓰기 URL 확정: `https://{BLOG_NAME}.tistory.com/manage/newpost`
- [x] 요약 박스 라벨 변경: TL;DR → `📌  요약`
- [x] SQL 코드블록: `<div>` 기반 하이라이팅 (TinyMCE `<pre><code>` span 이스케이프 우회)

### v5 - SQL 하이라이팅 완전 수정
- [x] `markdown2` 2.5.5 버그 우회: ` ```sql ` 블록을 markdown2 실행 전 선추출 (placeholder 방식)
- [x] `white-space:pre` 추가 → SQL 들여쓰기 보존
- [x] 줄 번호 추가 (display:flex + border-right 구분선)
- [x] 파란 왼쪽 테두리 (`border-left: 3px solid #388bfd`)
- [x] 제목 글자 수 35자 → 45자 (`[카테고리]` prefix 포함 기준)
- [x] 기술 전문 용어 영어 작성 규칙 정립 (tablespace, index, partition 등)

---

## 현재 코드 상태

| 항목 | 방식 |
|------|------|
| 에디터 | **TinyMCE** (구 CodeMirror 셀렉터 전부 무효) |
| 로그인 | **완전 자동** (CDP webdriver 숨기기 + pyautogui 계정 클릭) |
| 세션 유지 | `chrome_profile/` 폴더 |
| Chrome 재사용 | Remote Debugging Port 9222 감지 시 기존 Chrome 연결 |
| 제목 입력 | pyautogui viewport (300, 185) — `wait.until` 금지 |
| 본문 주입 | `tinymce.activeEditor.setContent()` |
| 태그 입력 | `input#tagText` + JS KeyboardEvent |
| 카테고리 | `[role="option"]` 셀렉터 (5단계 폴백) |
| 임시저장 | pyautogui (x≈1047, 하단 -34px) |
| 발행 | pyautogui (x≈1163, 하단 -34px) |
| SQL 하이라이팅 | 선추출 placeholder → `_sql_block_to_div()` (줄번호+들여쓰기) |

---

## 미완료

없음 — 전체 자동화 완성

---

## 파일 구조

```
D:\DoubleD\tistory_auto\
├── CLAUDE.md                ← Claude Code 컨텍스트 (주요 참조 파일)
├── PROJECT_STATUS.md        ← 이 파일 (진행 상황)
├── PROMPTS.md               ← 자주 쓰는 프롬프트 모음
├── SETUP_GUIDE.md           ← 초기 설정 가이드
├── config.json              ← 카카오 계정 (gitignore)
├── 01_login_test.py         ← 로그인 단독 테스트
├── 02_post.py               ← 메인 포스팅 스크립트
├── chrome_profile/          ← Chrome 세션 (gitignore)
├── preview.html             ← HTML 변환 미리보기 (gitignore)
└── posts/
    └── post.md              ← 포스팅 원고
```
