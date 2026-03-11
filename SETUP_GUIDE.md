# DBA&I 티스토리 자동화 - 전체 세팅 가이드

## STEP 1. 폴더 생성

```cmd
mkdir D:\DoubleD\tistory_auto
mkdir D:\DoubleD\tistory_auto\posts
cd D:\DoubleD\tistory_auto
```

---

## STEP 2. 파일 구조

```
D:\DoubleD\tistory_auto\
├── CLAUDE.md                    ← Claude Code 컨텍스트
├── PROJECT_STATUS.md            ← 진행 상황
├── PROMPTS.md                   ← 프롬프트 모음
├── SETUP_GUIDE.md               ← 이 파일
├── tistory_auto.code-workspace  ← VSCode 워크스페이스
├── config.json                  ← 카카오 계정 정보
├── 01_login_test.py             ← 로그인 단독 테스트
├── 02_post.py                   ← 메인 포스팅 스크립트
└── posts\
    └── post.md                  ← 포스팅 원고
```

---

## STEP 3. config.json 수정

```json
{
  "kakao_email": "본인카카오이메일@kakao.com",
  "kakao_password": "본인카카오비밀번호",
  "blog_name": "블로그주소앞부분",
  "default_category": "DB 기술",
  "default_visibility": "0"
}
```

`blog_name` 예시: `https://dbai.tistory.com` → `"dbai"`

---

## STEP 4. 워크스페이스 열기

VSCode에서 파일 → 워크스페이스 열기 → `tistory_auto.code-workspace` 선택
또는:

```cmd
code D:\DoubleD\tistory_auto\tistory_auto.code-workspace
```

---

## STEP 5. 패키지 설치

```cmd
cd D:\DoubleD\tistory_auto
pip install selenium webdriver-manager markdown2 python-frontmatter pyperclip pyautogui
```

---

## STEP 6. 로그인 테스트

```cmd
python 01_login_test.py
```

Chrome이 자동으로 열리고 티스토리 관리자 페이지에 접근되면 성공.
첫 실행 시 카카오 계정 선택 또는 2FA가 요구될 수 있음.
→ "이 브라우저에서 2단계 인증 사용 안 함" 체크 시 이후 완전 자동화.

---

## STEP 7. 포스팅 테스트

`posts/post.md` 작성 후:

```cmd
python 02_post.py
```

---

## STEP 8. Claude Code 연동

### 설치
```cmd
npm install -g @anthropic-ai/claude-code
```

### 시작
```cmd
cd D:\DoubleD\tistory_auto
claude
```

Claude Code가 시작되면 `CLAUDE.md`를 자동으로 읽고 프로젝트 컨텍스트를 파악합니다.

---

## 일상 포스팅 루틴

1. Claude Code 채팅에서 원고 작성 요청 (`PROMPTS.md` → STEP 1 참조)
2. `posts/post.md` 내용 확인
3. `python 02_post.py` 실행
4. 티스토리 관리자에서 임시저장 확인 후 발행

---

## 오류 대응

| 오류 상황 | 확인 파일 | 참조 |
|-----------|-----------|------|
| 셀렉터 오류 | `error_screenshot.png` | CLAUDE.md 셀렉터 목록 |
| 저장 직전 오류 | `debug_before_save.png` | CLAUDE.md 셀렉터 목록 |
| 카테고리 오류 | `debug_category_open.png` | — |
| 카카오 로그인 오류 | `debug_kakao_page.png` | — |
