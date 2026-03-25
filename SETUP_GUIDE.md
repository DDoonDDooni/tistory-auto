# DBA&I 티스토리 자동화 - 전체 세팅 가이드

## Mac 세팅

### STEP 1. 레포 클론

```bash
cd ~/Documents/DoubleD
git clone https://github.com/DDoonDDooni/tistory-auto.git
cd tistory-auto
```

---

### STEP 2. Python 3.12 + 가상환경 설치

```bash
# Homebrew 설치 (없는 경우)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Apple Silicon(M1/M2/M3) PATH 등록
echo >> ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Python 3.12 설치
brew install python@3.12

# 가상환경 생성 및 패키지 설치
python3.12 -m venv .venv
source .venv/bin/activate
pip install selenium webdriver-manager markdown2 python-frontmatter pyperclip pyautogui keyring

# Google Chrome 설치 (없는 경우)
brew install --cask google-chrome
```

---

### STEP 3. config.json 설정

```json
{
  "kakao_email": "본인카카오이메일@kakao.com",
  "blog_name": "블로그주소앞부분",
  "default_category": "DB 기술",
  "default_visibility": "0"
}
```

`blog_name` 예시: `https://dbai.tistory.com` → `"dbai"`

> **비밀번호는 config.json에 넣지 않습니다.** 다음 단계에서 키체인에 저장합니다.

---

### STEP 4. 비밀번호 키체인 등록 (최초 1회)

```bash
python setup_credentials.py
```

macOS Keychain Access에 안전하게 저장됩니다. 비밀번호 변경 시 재실행합니다.

---

### STEP 5. 워크스페이스 열기

VSCode에서 파일 → 워크스페이스 열기 → `tistory_auto.code-workspace` 선택
또는:

```bash
code tistory_auto.code-workspace
```

---

### STEP 6. 로그인 테스트

```bash
source .venv/bin/activate
python 01_login_test.py
```

Chrome이 자동으로 열리고 로그인이 완료되면 성공.
- 첫 실행 시 2FA(카카오 인증번호)가 요구될 수 있음
- **"이 브라우저에서 2단계 인증 사용 안 함"** 체크 필수 → 이후 완전 자동화

---

### STEP 7. 포스팅 테스트

`posts/post.md` 작성 후:

```bash
python 02_post.py
```

---

## Windows 세팅

### STEP 1. 레포 클론

```cmd
cd D:\DoubleD
git clone https://github.com/DDoonDDooni/tistory-auto.git
cd tistory-auto
```

---

### STEP 2. Python 3.12 + 가상환경 설치

1. [python.org](https://www.python.org/downloads/) 에서 Python 3.12 설치
   - **"Add Python to PATH"** 반드시 체크
2. 가상환경 생성 및 패키지 설치:

```cmd
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install selenium webdriver-manager markdown2 python-frontmatter pyperclip pyautogui keyring
```

---

### STEP 3. config.json 설정

Mac과 동일 (위 참조)

---

### STEP 4. 비밀번호 키체인 등록 (최초 1회)

```cmd
python setup_credentials.py
```

Windows Credential Manager에 저장됩니다.

---

### STEP 5~7.

Mac과 동일 (명령어만 `.venv\Scripts\activate` 으로 변경)

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
| 셀렉터 오류 | `debug/error_screenshot.png` | CLAUDE.md 셀렉터 목록 |
| 저장 직전 오류 | `debug/debug_before_save.png` | CLAUDE.md 셀렉터 목록 |
| 카카오 로그인 오류 | `debug/debug_kakao_page.png` | — |
| 비밀번호 키체인 오류 | — | `python setup_credentials.py` 재실행 |
