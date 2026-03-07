"""
02_post.py  (v2 - 모던 스타일 적용)
티스토리 자동 포스팅 스크립트 (카카오 소셜 로그인)

적용 스타일:
  - 소제목(h2/h3): 왼쪽 컬러 바 + 굵은 폰트
  - 코드블록: 다크 배경 + 언어 라벨
  - 표(table): 헤더 다크 + 홀짝 행 배경
  - 요약 박스(TL;DR): 주황 강조 블록
  - 인용구(blockquote): 왼쪽 파란 선 + 배경색
  - 해시태그: 하단 태그 칩 박스
  - 이모지: 별도 처리 없이 그대로 유지

post.md 상단 메타 포맷:
---
title: "[Oracle] 제목"
tags: Oracle,DBA,ADG
category: DB 기술
visibility: 0
---
본문 내용...
"""

import os
import json
import time
import re
import socket
import frontmatter
import markdown2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# ── 설정 로드 ──────────────────────────────────────
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

KAKAO_EMAIL    = config["kakao_email"]
KAKAO_PASSWORD = config["kakao_password"]
BLOG_NAME      = config["blog_name"]
DEF_CATEGORY   = config.get("default_category", "")
DEF_VISIBILITY = config.get("default_visibility", "0")

POST_FILE = "posts/post.md"
REMOTE_DEBUG_PORT = 9222  # Chrome Remote Debugging Port

# ── 모던 CSS 스타일 ─────────────────────────────────
STYLE = """<style>
.dbai-post {
  font-family: 'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif;
  font-size: 16px;
  line-height: 1.85;
  color: #1f2328;
  word-break: keep-all;
  max-width: 800px;
}

/* 소제목 h2: 주황 왼쪽 바 */
.dbai-post h2 {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  margin: 40px 0 14px;
  padding: 8px 0 8px 16px;
  border-left: 4px solid #f97316;
  background: linear-gradient(90deg, rgba(249,115,22,0.07) 0%, transparent 80%);
  border-radius: 0 6px 6px 0;
}

/* 소제목 h3: 슬레이트 왼쪽 바 */
.dbai-post h3 {
  font-size: 17px;
  font-weight: 600;
  color: #374151;
  margin: 30px 0 10px;
  padding: 4px 0 4px 12px;
  border-left: 3px solid #94a3b8;
}

/* 요약 박스 */
.dbai-post .summary-box {
  background: linear-gradient(135deg, #fff7ed 0%, #fffbf7 100%);
  border: 1px solid #fed7aa;
  border-left: 5px solid #f97316;
  border-radius: 0 10px 10px 0;
  padding: 16px 20px 16px 20px;
  margin: 16px 0 28px;
  font-size: 15px;
  color: #7c2d12;
  line-height: 1.75;
}
.dbai-post .summary-box::before {
  content: "📌  TL;DR";
  display: block;
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 1.2px;
  color: #f97316;
  margin-bottom: 8px;
  text-transform: uppercase;
}

/* 코드블록 다크 테마 */
.dbai-post pre {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 20px 22px 20px 22px;
  margin: 18px 0;
  overflow-x: auto;
  position: relative;
}
.dbai-post pre::before {
  content: attr(data-lang);
  position: absolute;
  top: 9px;
  right: 14px;
  font-size: 10px;
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  color: #6e7681;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.dbai-post pre code {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 13.5px;
  line-height: 1.7;
  color: #e6edf3;
  background: none !important;
  padding: 0 !important;
  border: none !important;
  border-radius: 0 !important;
}

/* 인라인 코드 */
.dbai-post code {
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  font-size: 13px;
  background: #f1f5f9;
  color: #e11d48;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
}

/* 표 */
.dbai-post table {
  width: 100%;
  border-collapse: collapse;
  margin: 22px 0;
  font-size: 14px;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 6px rgba(0,0,0,0.08);
}
.dbai-post thead tr {
  background: #1f2937;
  color: #f9fafb;
}
.dbai-post th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0.3px;
}
.dbai-post td {
  padding: 11px 16px;
  border-bottom: 1px solid #e5e7eb;
  color: #374151;
}
.dbai-post tbody tr:nth-child(even) td {
  background: #f8fafc;
}
.dbai-post tbody tr:hover td {
  background: #fff7ed;
}

/* 인용구 */
.dbai-post blockquote {
  margin: 20px 0;
  padding: 14px 20px;
  background: #f0f9ff;
  border-left: 4px solid #0ea5e9;
  border-radius: 0 8px 8px 0;
  color: #0c4a6e;
  font-size: 15px;
  line-height: 1.75;
}
.dbai-post blockquote p { margin: 0; }

/* 단락 */
.dbai-post p {
  margin: 0 0 14px;
  color: #374151;
}

/* 강조 */
.dbai-post strong { font-weight: 700; color: #111827; }

/* 구분선 */
.dbai-post hr {
  border: none;
  border-top: 2px dashed #e5e7eb;
  margin: 32px 0;
}

/* 리스트 */
.dbai-post ul, .dbai-post ol {
  padding-left: 24px;
  margin: 10px 0 18px;
}
.dbai-post li {
  margin-bottom: 6px;
  color: #374151;
  line-height: 1.75;
}

/* 해시태그 박스 */
.dbai-post .hashtag-area {
  margin-top: 40px;
  padding: 16px 18px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 13px;
  color: #64748b;
  line-height: 2.2;
}
.dbai-post .ht-chip {
  display: inline-block;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  color: #f97316;
  padding: 3px 10px;
  border-radius: 20px;
  margin: 3px 2px;
  font-size: 12px;
  font-weight: 500;
}
</style>"""


# ── 마크다운 → 모던 스타일 HTML 변환 ──────────────
def md_to_styled_html(md_text):

    # 1) 요약: 줄 → summary-box div 변환
    lines = md_text.split('\n')
    processed = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('요약:') or stripped.startswith('요약：'):
            content = stripped[3:].strip()
            processed.append(f'<div class="summary-box">{content}</div>\n')
        else:
            processed.append(line)
    md_text = '\n'.join(processed)

    # 2) 해시태그 줄 → 태그 칩 박스 변환
    ht_pattern = r'추천 해시태그[:：]\s*(.+)'
    ht_match = re.search(ht_pattern, md_text)
    hashtag_html = ""
    if ht_match:
        tags = re.findall(r'#[\w가-힣]+', ht_match.group(1))
        chips = ''.join(f'<span class="ht-chip">{t}</span>' for t in tags)
        hashtag_html = (
            f'<div class="hashtag-area">'
            f'<strong style="color:#374151;display:block;margin-bottom:6px;">🏷️ 태그</strong>'
            f'{chips}</div>'
        )
        md_text = md_text[:ht_match.start()].rstrip()

    # 3) markdown → HTML
    html_body = markdown2.markdown(
        md_text,
        extras=[
            "fenced-code-blocks",
            "tables",
            "strike",
            "break-on-newline",
            "code-friendly",
        ]
    )

    # 4) 코드블록 언어 라벨 주입
    html_body = re.sub(
        r'<pre><code class="language-([^"]+)">',
        lambda m: f'<pre data-lang="{m.group(1)}"><code class="language-{m.group(1)}">',
        html_body
    )
    html_body = html_body.replace('<pre><code>', '<pre data-lang="code"><code>')

    # 5) 조립
    full_html = (
        f"{STYLE}\n"
        f'<div class="dbai-post">\n'
        f'{html_body}\n'
        f'{hashtag_html}\n'
        f'</div>'
    )
    return full_html


# ── post.md 파싱 ────────────────────────────────────
def load_post(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        post = frontmatter.load(f)

    title        = post.get("title", "제목 없음")
    tags         = post.get("tags", "")
    category     = post.get("category", DEF_CATEGORY)
    visibility   = str(post.get("visibility", DEF_VISIBILITY))
    content_html = md_to_styled_html(post.content)

    print(f"\n[포스트 정보]")
    print(f"  제목      : {title}")
    print(f"  태그      : {tags}")
    print(f"  카테고리  : {category}")
    print(f"  공개 여부 : {'임시저장' if visibility == '0' else '발행'}")
    print(f"  HTML 길이 : {len(content_html)}자\n")

    return {
        "title": title, "tags": tags,
        "category": category, "visibility": visibility,
        "content_html": content_html,
    }


# ── 포트 열려있는지 확인 ────────────────────────────
def _is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


# ── 브라우저 실행 ───────────────────────────────────
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    service = Service(ChromeDriverManager().install())

    if _is_port_open(REMOTE_DEBUG_PORT):
        # 이미 실행 중인 Chrome에 연결 (Remote Debugging)
        print(f"[*] 기존 Chrome 감지 → 포트 {REMOTE_DEBUG_PORT} 연결")
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{REMOTE_DEBUG_PORT}")
        driver = webdriver.Chrome(service=service, options=options)
        driver._keep_alive = True   # Chrome 프로세스 유지
    else:
        # 새 Chrome 실행 (프로필 + 리모트 디버깅 포트 오픈)
        print("[*] 새 Chrome 실행...")
        profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile")
        options.add_argument(f"--user-data-dir={profile_dir}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--remote-debugging-port={REMOTE_DEBUG_PORT}")
        driver = webdriver.Chrome(service=service, options=options)
        driver._keep_alive = False  # 스크립트가 띄운 Chrome → 종료

    return driver


# ── 카카오 로그인 ───────────────────────────────────
def kakao_login(driver):
    print("[1] 로그인 상태 확인 중 (관리 페이지 접근 테스트)...")
    driver.get(f"https://{BLOG_NAME}.tistory.com/manage")
    time.sleep(2)

    # 관리 페이지에 실제 접근 가능하면 세션 유효
    if f"{BLOG_NAME}.tistory.com/manage" in driver.current_url:
        print("[OK] 기존 세션으로 로그인됨!")
        return

    print("[!] 세션 없음 또는 만료 → 카카오 로그인 필요")
    driver.get("https://www.tistory.com/auth/login")
    time.sleep(2)

    print("\n" + "=" * 54)
    print("  브라우저에서 카카오 로그인을 직접 진행해주세요.")
    print("  >> '이 브라우저에서 2단계 인증 사용 안 함' 체크 권장")
    print("  로그인 완료 후 자동으로 포스팅이 진행됩니다.")
    print("  (최대 120초 대기)")
    print("=" * 54 + "\n")

    try:
        WebDriverWait(driver, 120).until(
            lambda d: f"{BLOG_NAME}.tistory.com" in d.current_url
                      and "auth/login" not in d.current_url
                      and "kakao" not in d.current_url
        )
    except Exception:
        raise Exception("로그인 대기 시간 초과 (120초). 다시 실행해주세요.")

    print("[OK] 로그인 성공!")


# ── 글쓰기 이동 ─────────────────────────────────────
def go_to_write(driver):
    url = f"https://{BLOG_NAME}.tistory.com/manage/post/write"
    print(f"\n[5] 글쓰기 이동: {url}")
    driver.get(url)
    time.sleep(3)
    # 새 탭/창이 열렸으면 최신 창으로 전환
    handles = driver.window_handles
    if len(handles) > 1:
        print(f"  [창 전환] {len(handles)}개 창 감지 → 최신 창으로 전환")
        driver.switch_to.window(handles[-1])
        time.sleep(1)


# ── 제목 입력 ───────────────────────────────────────
def input_title(driver, title):
    print(f"[6] 제목 입력: {title}")
    wait = WebDriverWait(driver, 15)
    inp = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#post-title-inp")))
    driver.execute_script(
        "arguments[0].focus();"
        "var nv = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
        "nv.call(arguments[0], arguments[1]);"
        "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
        "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
        inp, title
    )
    time.sleep(1)


# ── 본문 HTML 주입 ──────────────────────────────────
def input_content_html(driver, html_content):
    print("[7] HTML 모드 전환 중...")
    wait = WebDriverWait(driver, 15)
    try:
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.editor-mode-html")
        )).click()
        time.sleep(1)
    except Exception:
        print("  (HTML 모드 버튼 스킵)")

    print("[8] 본문 HTML 주입 중...")
    injected = driver.execute_script("""
        var cm = document.querySelector('.CodeMirror');
        if (cm && cm.CodeMirror) {
            cm.CodeMirror.setValue(arguments[0]);
            return true;
        }
        return false;
    """, html_content)

    if not injected:
        driver.execute_script("""
            var el = document.querySelector('[contenteditable="true"]');
            if (el) el.innerHTML = arguments[0];
        """, html_content)

    time.sleep(1)
    print("[OK] 본문 주입 완료")


# ── 태그 입력 ───────────────────────────────────────
def input_tags(driver, tags):
    if not tags:
        return
    print(f"[9] 태그 입력: {tags}")
    try:
        wait = WebDriverWait(driver, 10)
        inp = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#tagText")))
        for tag in [t.strip() for t in tags.split(",") if t.strip()]:
            driver.execute_script(
                "var nv = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
                "nv.call(arguments[0], arguments[1]);"
                "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));",
                inp, tag
            )
            time.sleep(0.2)
            driver.execute_script(
                "arguments[0].dispatchEvent(new KeyboardEvent('keydown', {key:'Enter',keyCode:13,bubbles:true}));"
                "arguments[0].dispatchEvent(new KeyboardEvent('keyup', {key:'Enter',keyCode:13,bubbles:true}));",
                inp
            )
            time.sleep(0.4)
        print(f"[OK] 태그 완료")
    except Exception as e:
        print(f"  [경고] 태그 스킵: {e}")


# ── 카테고리 선택 ───────────────────────────────────
def select_category(driver, category):
    if not category:
        return
    print(f"[10] 카테고리: {category}")
    try:
        wait = WebDriverWait(driver, 10)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-category"))).click()
        time.sleep(1)
        for item in driver.find_elements(By.CSS_SELECTOR, "ul.category-list li"):
            if category in item.text:
                item.click()
                print(f"[OK] 카테고리 선택: {item.text}")
                break
        time.sleep(1)
    except Exception as e:
        print(f"  [경고] 카테고리 스킵: {e}")


# ── 임시저장 / 발행 ─────────────────────────────────
def save_post(driver, visibility):
    wait = WebDriverWait(driver, 15)
    if visibility == "0":
        print("\n[11] 임시저장 중...")
        try:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-save"))).click()
            time.sleep(2)
            print("[OK] 임시저장 완료!")
        except Exception as e:
            print(f"  [경고] 임시저장 실패: {e}")
    else:
        print("\n[11] 발행 중...")
        try:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-publish"))).click()
            time.sleep(2)
            print("[OK] 발행 완료!")
        except Exception as e:
            print(f"  [경고] 발행 실패: {e}")


# ── 메인 ────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 54)
    print("   DBA&I 티스토리 자동 포스팅  v2 (모던 스타일)")
    print("=" * 54)

    try:
        post = load_post(POST_FILE)
    except FileNotFoundError:
        print(f"[오류] {POST_FILE} 없음. posts/post.md 를 만들어주세요.")
        exit(1)

    driver = get_driver()
    try:
        kakao_login(driver)
        go_to_write(driver)
        input_title(driver, post["title"])
        input_content_html(driver, post["content_html"])
        input_tags(driver, post["tags"])
        select_category(driver, post["category"])
        save_post(driver, post["visibility"])

        print("\n" + "=" * 54)
        print("   [완료] 포스팅 성공! ")
        print(f"   관리자: https://{BLOG_NAME}.tistory.com/manage")
        print("=" * 54)
        time.sleep(3)

    except Exception as e:
        print(f"\n[오류] {e}")
        try:
            driver.save_screenshot("error_screenshot.png")
            print("error_screenshot.png 저장됨")
        except Exception:
            pass
        time.sleep(5)

    finally:
        if getattr(driver, "_keep_alive", False):
            # 기존 Chrome에 연결한 경우: ChromeDriver만 종료, 브라우저 유지
            try:
                driver.service.stop()
            except Exception:
                pass
            print("[*] Chrome 세션 유지 중 (다음 실행 시 재사용 가능)")
        else:
            # 스크립트가 직접 띄운 Chrome: 종료
            driver.quit()
