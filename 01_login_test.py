"""
01_login_test.py
카카오 소셜 로그인 테스트 스크립트
최초 1회 실행해서 로그인이 정상 동작하는지 확인하세요.
"""

import json
import time
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
KAKAO_PASSWORD = config["kakao_password"]

# ── 브라우저 실행 ───────────────────────────────────
def get_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # 화면 없이 실행할 때 주석 해제
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
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

    print("[3] 카카오 이메일 입력 중...")
    email_input = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input#loginId"))
    )
    email_input.clear()
    email_input.send_keys(KAKAO_EMAIL)

    print("[4] 카카오 비밀번호 입력 중...")
    pw_input = driver.find_element(By.CSS_SELECTOR, "input#password")
    pw_input.clear()
    pw_input.send_keys(KAKAO_PASSWORD)

    print("[5] 로그인 버튼 클릭 중...")
    login_btn = driver.find_element(By.CSS_SELECTOR, "button.btn_g.highlight.submit")
    login_btn.click()
    time.sleep(3)

    # 로그인 성공 확인
    current_url = driver.current_url
    if "tistory.com" in current_url and "auth/login" not in current_url:
        print(f"[✓] 로그인 성공! 현재 URL: {current_url}")
        return True
    else:
        print(f"[✗] 로그인 실패. 현재 URL: {current_url}")
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
        time.sleep(5)
    finally:
        driver.quit()
