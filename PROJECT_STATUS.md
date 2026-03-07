# tistory_auto 프로젝트 진행 상황

## 프로젝트 개요
Python + Selenium으로 티스토리에 자동 포스팅하는 스크립트
- 경로: `D:\DoubleD\tistory_auto`
- 메인: `02_post.py`
- 원고: `posts/post.md`

---

## 완료된 작업

### v1 - 기초 구성
- [x] 카카오 소셜 로그인 자동화 시도
- [x] `01_login_test.py` 로그인 테스트 스크립트 작성
- [x] `02_post.py` 기본 포스팅 플로우 구성
- [x] 마크다운 → 모던 스타일 HTML 변환 (`md_to_styled_html`)
- [x] CSS 스타일 적용 (h2/h3, 코드블록, 표, 인용구, 요약박스, 해시태그)
- [x] frontmatter 파싱 (title / tags / category / visibility)

### v2 - 안정화
- [x] `send_keys` 카카오 자동화 탐지 crash → JS 입력 방식으로 전환
- [x] `undetected_chromedriver` 시도 → Python 3.14 + Win 조합 불안정 → 제거
- [x] 로그인 방식 수동 전환 (브라우저 열고 직접 로그인, 120초 대기)
- [x] `chrome_profile` 세션 유지 (`--user-data-dir`)
- [x] 세션 만료 오탐 수정: URL 체크 → `/manage` 접근 가능 여부로 판단
- [x] Chrome Remote Debugging Port(9222) 도입: 기존 Chrome 재사용 가능

### v3 - 자동화 완성
- [x] `pyperclip` + `pyautogui` 클립보드 방식으로 ID/PW 자동 입력 (카카오 탐지 우회)
- [x] 카카오 2FA 완료 + "이 브라우저에서 2단계 인증 사용 안 함" 체크 완료
- [x] `chrome_profile`에 세션 + 기기 신뢰 저장됨 → **이후 실행 완전 자동화**

---

## 현재 코드 상태

| 항목 | 방식 |
|------|------|
| 로그인 | **자동** (pyperclip+pyautogui ID/PW 입력, 세션 만료 시에만 동작) |
| 세션 유지 | `chrome_profile/` 폴더 |
| Chrome 재사용 | Remote Debugging Port 9222 감지 시 기존 Chrome에 연결 |
| 제목 입력 | JS `nativeInputValueSetter` |
| 태그 입력 | JS `KeyboardEvent` (Enter) |
| 본문 주입 | `CodeMirror.setValue()` → fallback `contenteditable.innerHTML` |
| 저장/발행 | visibility=0 → 임시저장 / 3 → 발행 |

---

## 미완료 / 미검증

- [ ] **포스팅 end-to-end 실제 성공 미확인** ← 최우선
- [ ] `input#post-title-inp` 셀렉터 현재 티스토리 에디터 유효성 미확인
- [ ] `button.editor-mode-html` 셀렉터 유효성 미확인
- [ ] GitHub repo push

---

## 다음 단계

> **현재 상태 (2026-03-07 기준):**
> 카카오 로그인 + 2FA 완료, `chrome_profile`에 세션 저장됨.
> **로그인은 이미 완료된 상태. 재로그인 불필요.**
> 다음은 포스팅 end-to-end 테스트만 하면 됨.

1. **`python 02_post.py` 실행** → 세션 자동 인식 → 포스팅 자동 진행
2. 오류 시 `error_screenshot.png` + 셀렉터 수정
3. 성공 후 GitHub repo 생성 및 push

### STEP 1 진행 시 수정 사항 (오늘 적용)
- **세션 감지 완화:** `/manage` 접속 시 메인 등으로 리다이렉트돼도 로그인 유효로 판단하도록 `02_post.py` 수정 (리다이렉트 감지 추가).
- **글쓰기 이동 방식:** `BLOG_NAME.tistory.com/manage/` 또는 `/manage/newpost/` 직접 접근 시 "권한이 없거나 존재하지 않는 페이지" 발생 → 현재 페이지에서 "글쓰기" 링크/버튼 클릭 방식으로 변경, 실패 시 `www.tistory.com` 메인 이동 후 여러 XPath로 글쓰기 버튼 재탐색.
- **재실행 권장:** 터미널에서 `python 02_post.py` 다시 실행 후, 메인에서 글쓰기 클릭이 동작하는지 확인.

---

## 파일 구조

```
D:\DoubleD\tistory_auto\
├── CLAUDE.md                ← Claude Code 컨텍스트
├── PROJECT_STATUS.md        ← 이 파일 (진행 상황)
├── PROMPTS.md               ← Cursor 명령 프롬프트 모음
├── SETUP_GUIDE.md           ← 초기 설정 가이드
├── config.json              ← 카카오 계정 (gitignore 필수)
├── 01_login_test.py         ← 로그인 단독 테스트
├── 02_post.py               ← 메인 포스팅 스크립트
├── chrome_profile/          ← Chrome 세션 (gitignore)
└── posts/
    └── post.md              ← 포스팅 원고
```
