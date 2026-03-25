"""
01_login_test.py
카카오 소셜 로그인 테스트 스크립트
최초 1회 실행해서 로그인이 정상 동작하는지 확인하세요.
"""

import os
import json
import time
import platform
import keyring
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ── 설정 로드 ──────────────────────────────────────
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

KAKAO_EMAIL    = config["kakao_email"]
KAKAO_PASSWORD = keyring.get_password("tistory-auto", KAKAO_EMAIL)
if not KAKAO_PASSWORD:
    raise SystemExit("[오류] 비밀번호가 키체인에 없습니다. setup_credentials.py를 먼저 실행하세요.")

# ── 브라우저 실행 ───────────────────────────────────
def get_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # 화면 없이 실행할 때 주석 해제
    if platform.system() != "Darwin":  # Mac이 아닐 때만 no-sandbox 적용
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-blink-features=AutomationControlled")  # 봇 탐지 우회
    options.add_argument("--disable-features=PasswordLeakDetection")       # 비밀번호 유출 팝업 비활성화
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")

    # 프로필 저장 → 2FA 완료 후 세션 유지 (2회차부터 자동화)
    profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile")
    options.add_argument(f"--user-data-dir={profile_dir}")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        })
    except Exception:
        pass
    return driver

# ── 카카오 로그인 ───────────────────────────────────
def kakao_login(driver):
    print("[1] 티스토리 로그인 페이지 접속 중...")
    driver.get("https://www.tistory.com/auth/login")
    time.sleep(2)

    print("[2] 카카오 로그인 버튼 클릭 중...")
    wait = WebDriverWait(driver, 10)
    kakao_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn_login.link_kakao_id"))
    )
    kakao_btn.click()
    time.sleep(2)

    print("[3] 카카오 로그인 페이지 로딩 대기 중...")
    time.sleep(3)
    driver.save_screenshot("debug_kakao_page.png")
    print(f"  현재 URL: {driver.current_url}")
    print(f"  현재 페이지 제목: {driver.title}")
    print("  [디버그] debug_kakao_page.png 저장됨")

    # 이메일 입력 필드 - 여러 셀렉터 시도
    email_selectors = [
        "input#loginId",
        "input[name='loginId']",
        "input[type='email']",
        "input[autocomplete='username']",
        "input[name='email']",
        "input[placeholder*='이메일']",
        "input[placeholder*='아이디']",
    ]
    email_input = None
    for sel in email_selectors:
        try:
            email_input = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sel))
            )
            print(f"  이메일 셀렉터 발견: {sel}")
            break
        except Exception:
            continue

    if email_input is None:
        driver.save_screenshot("debug_email_not_found.png")
        raise Exception("이메일 입력 필드를 찾을 수 없습니다. debug_kakao_page.png / debug_email_not_found.png 확인 필요")

    print("[3] 카카오 이메일 입력 중...")
    email_input.clear()
    email_input.send_keys(KAKAO_EMAIL)

    print("[4] 카카오 비밀번호 입력 중...")
    pw_selectors = [
        "input#password",
        "input[name='password']",
        "input[type='password']",
        "input[autocomplete='current-password']",
    ]
    pw_input = None
    for sel in pw_selectors:
        try:
            pw_input = driver.find_element(By.CSS_SELECTOR, sel)
            print(f"  비밀번호 셀렉터 발견: {sel}")
            break
        except Exception:
            continue

    if pw_input is None:
        raise Exception("비밀번호 입력 필드를 찾을 수 없습니다.")

    pw_input.clear()
    pw_input.send_keys(KAKAO_PASSWORD)

    print("[5] 로그인 버튼 클릭 중...")
    login_btn_selectors = [
        "button.btn_g.highlight.submit",
        "button[type='submit']",
        "input[type='submit']",
        "button.submit",
    ]
    login_btn = None
    for sel in login_btn_selectors:
        try:
            login_btn = driver.find_element(By.CSS_SELECTOR, sel)
            print(f"  로그인 버튼 셀렉터 발견: {sel}")
            break
        except Exception:
            continue

    if login_btn is None:
        raise Exception("로그인 버튼을 찾을 수 없습니다.")

    login_btn.click()

    # 2FA / 추가 인증 대기 (최대 120초)
    print("[6] 로그인 결과 확인 중... (2FA 인증번호가 왔다면 지금 입력하세요)")
    for i in range(120):
        time.sleep(1)
        current_url = driver.current_url
        if "tistory.com" in current_url and "auth/login" not in current_url and "kakao" not in current_url:
            print(f"[✓] 로그인 성공! 현재 URL: {current_url}")
            return True
        # 2FA 화면 감지
        if i == 3:
            page_src = driver.page_source
            if any(kw in page_src for kw in ["인증번호", "본인인증", "2단계", "OTP", "verification"]):
                print("\n" + "="*55)
                print("  [2FA 감지] 핸드폰으로 인증번호가 전송됐습니다.")
                print("  Chrome 창에서 인증번호를 입력하고 로그인을 완료하세요.")
                print("  '이 브라우저에서 2단계 인증 사용 안 함'을 체크하면")
                print("  다음부터는 자동으로 건너뜁니다.")
                print("="*55)
        if i % 10 == 9:
            print(f"  대기 중... ({i+1}초 경과, 현재: {current_url})")

    print(f"[✗] 로그인 시간 초과. 현재 URL: {driver.current_url}")
    return False

# ── 메인 실행 ───────────────────────────────────────
if __name__ == "__main__":
    driver = get_driver()
    try:
        success = kakao_login(driver)
        if success:
            print("\n[완료] 로그인 테스트 성공! 02_post.py를 실행할 수 있습니다.")
            time.sleep(3)
        else:
            print("\n[실패] config.json의 이메일/비밀번호를 확인해주세요.")
            time.sleep(5)
    except Exception as e:
        print(f"\n[오류] {e}")
        try:
            driver.save_screenshot("error_login.png")
            print("[디버그] error_login.png 저장됨 - 현재 화면 확인하세요")
        except Exception:
            pass
        time.sleep(5)
    finally:
        driver.quit()
