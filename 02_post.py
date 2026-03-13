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
import html as _html
import pyperclip
import pyautogui
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

# ── 인라인 스타일 상수 (TinyMCE class 기반 CSS 제거 문제 우회) ──
_IS_POST    = "font-family:'Noto Sans KR','Apple SD Gothic Neo',sans-serif;font-size:16px;line-height:1.85;color:#1f2328;word-break:keep-all;"
_IS_H2      = "font-size:20px;font-weight:700;color:#111827;margin:40px 0 14px;padding:8px 0 8px 16px;border-left:4px solid #f97316;background:linear-gradient(90deg,rgba(249,115,22,0.07) 0%,transparent 80%);border-radius:0 6px 6px 0;"
_IS_H3      = "font-size:17px;font-weight:600;color:#374151;margin:30px 0 10px;padding:4px 0 4px 12px;border-left:3px solid #94a3b8;"
_IS_TABLE   = "width:100%;border-collapse:collapse;margin:22px 0;font-size:14px;"
_IS_THEAD   = "background:#f3f4f6;"
_IS_TH      = "padding:12px 16px;text-align:left;font-weight:600;font-size:13px;color:#374151;border:1px solid #e5e7eb;"
_IS_TD      = "padding:11px 16px;border:1px solid #e5e7eb;color:#374151;vertical-align:top;"
_IS_BQ      = "margin:20px 0;padding:14px 20px;background:#f0f9ff;border-left:4px solid #0ea5e9;border-radius:0 8px 8px 0;color:#374151;font-size:16px;font-family:inherit;line-height:1.75;word-break:keep-all;text-align:left;"
_IS_PRE     = "background:#0d1117;border:1px solid #30363d;border-radius:10px;padding:32px 22px 20px;margin:18px 0;overflow-x:auto;position:relative;"
_IS_PRECODE = "font-family:'JetBrains Mono','Fira Code','Consolas',monospace;font-size:13.5px;line-height:1.7;color:#e6edf3;background:none;padding:0;border:none;border-radius:0;"
_IS_CODE    = "font-family:'JetBrains Mono','Consolas',monospace;font-size:13px;background:#f1f5f9;color:#e11d48;padding:2px 6px;border-radius:4px;border:1px solid #e2e8f0;"
_IS_SUMMARY = "background:linear-gradient(135deg,#fff7ed 0%,#fffbf7 100%);border:1px solid #fed7aa;border-left:5px solid #f97316;border-radius:0 10px 10px 0;padding:16px 20px;margin:16px 0 28px;font-size:15px;color:#7c2d12;line-height:1.75;"
_IS_SLABEL  = "display:block;font-weight:700;font-size:11px;letter-spacing:1.2px;color:#f97316;margin-bottom:8px;text-transform:uppercase;"
_IS_HTAREA  = "margin-top:40px;padding:16px 18px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;font-size:13px;color:#64748b;line-height:2.2;"
_IS_HTCHIP  = "display:inline-block;background:#fff7ed;border:1px solid #fed7aa;color:#f97316;padding:3px 10px;border-radius:20px;margin:3px 2px;font-size:12px;font-weight:500;"
_IS_LANLABEL = "position:absolute;top:9px;right:14px;font-size:10px;font-family:Consolas,monospace;color:#6e7681;text-transform:uppercase;letter-spacing:1px;"


# ── SQL 문법 하이라이팅 ─────────────────────────────
def _highlight_sql_content(text):
    """SQL 코드블록 내부에 기본 문법 하이라이팅 적용 (겹침 방지 방식)"""
    spans = []  # (start, end, replacement_html)

    # 1) 줄 주석 -- ... (최우선)
    for m in re.finditer(r'--[^\n]*', text):
        repl = f'<span style="color:#8b949e;font-style:italic">{m.group()}</span>'
        spans.append((m.start(), m.end(), repl))

    # 2) 문자열 리터럴 '...'
    for m in re.finditer(r"'[^'\n]*'", text):
        repl = f'<span style="color:#a5d6ff">{m.group()}</span>'
        spans.append((m.start(), m.end(), repl))

    # 3) SQL 함수명 (키워드보다 먼저 처리)
    func_pat = (
        r'(?<![a-zA-Z_$])(COUNT|SUM|AVG|MAX|MIN|COALESCE|NVL|NVL2|DECODE|'
        r'TO_DATE|TO_CHAR|TO_NUMBER|SYSDATE|TRUNC|ROUND|'
        r'RANK|DENSE_RANK|ROW_NUMBER|LEAD|LAG)(?=\s*\()'
    )
    for m in re.finditer(func_pat, text, re.IGNORECASE):
        repl = f'<span style="color:#ffa657;font-weight:bold">{m.group(1).upper()}</span>'
        spans.append((m.start(1), m.end(1), repl))

    # 4) SQL 키워드 (다중 단어 먼저)
    kw_pat = (
        r'(?<![a-zA-Z_$#])'
        r'(GROUP\s+BY|ORDER\s+BY|PARTITION\s+BY|'
        r'LEFT\s+(?:OUTER\s+)?JOIN|RIGHT\s+(?:OUTER\s+)?JOIN|INNER\s+JOIN|FULL\s+(?:OUTER\s+)?JOIN|CROSS\s+JOIN|'
        r'ALTER\s+SYSTEM|ALTER\s+SESSION|'
        r'INSERT\s+INTO|UNION\s+ALL|'
        r'SELECT|FROM|WHERE|HAVING|DISTINCT|WITH|JOIN|'
        r'UNION|INTERSECT|MINUS|INTO|VALUES|UPDATE|'
        r'CREATE|ALTER|DROP|DELETE|'
        r'AND|OR|NOT|IS\s+NOT\s+NULL|IS\s+NULL|IN|IS|AS|ON|USING|'
        r'CASE|WHEN|THEN|ELSE|END|ALL|ANY|EXISTS|BETWEEN|LIKE|'
        r'DESC|ASC|OVER|ROWNUM|DUAL|'
        r'SHOW|SET|SCOPE|BOTH|PARAMETER|'
        r'NULL)'
        r'(?![a-zA-Z_$#])'
    )
    for m in re.finditer(kw_pat, text, re.IGNORECASE):
        kw = re.sub(r'\s+', ' ', m.group(1).upper())
        repl = f'<span style="color:#79c0ff;font-weight:bold">{kw}</span>'
        spans.append((m.start(1), m.end(1), repl))

    # 겹치는 span 제거 (앞에서 추가된 순서가 높은 우선순위)
    spans.sort(key=lambda x: x[0])
    non_overlapping = []
    last_end = 0
    for s, e, r in spans:
        if s >= last_end:
            non_overlapping.append((s, e, r))
            last_end = e

    # 역방향으로 텍스트에 적용 (위치 밀림 방지)
    result = text
    for s, e, r in reversed(non_overlapping):
        result = result[:s] + r + result[e:]
    return result


def _sql_block_to_div(code_raw):
    """SQL 코드를 div 기반 하이라이팅 블록으로 변환.
    <pre><code> 대신 <div>를 사용해 TinyMCE가 span을 텍스트로 이스케이프하는 문제 우회.
    줄 번호 + white-space:pre 로 들여쓰기 보존.
    """
    highlighted = _highlight_sql_content(code_raw.strip())
    lines = highlighted.split('\n')
    rows = []
    for i, line in enumerate(lines, 1):
        line_num = (
            f'<span style="display:inline-block;width:2em;text-align:right;'
            f'color:#484f58;margin-right:1.2em;user-select:none;font-size:11px;'
            f'border-right:1px solid #30363d;padding-right:0.6em;flex-shrink:0">{i}</span>'
        )
        code_part = line if line else ' '
        rows.append(
            f'<span style="display:flex;align-items:baseline;min-height:1.6em;'
            f'white-space:pre">{line_num}'
            f'<span style="flex:1;white-space:pre">{code_part}</span></span>'
        )
    content = ''.join(rows)
    return (
        '<div class="dbai-sql-block" style="'
        'background:#0d1117;border:1px solid #30363d;border-left:3px solid #388bfd;'
        'border-radius:0 10px 10px 0;'
        'padding:16px 18px 16px 14px;margin:18px 0;overflow-x:auto;'
        'font-family:JetBrains Mono,Fira Code,Consolas,monospace;'
        'font-size:13px;line-height:1.7;color:#e6edf3;position:relative">'
        '<span style="position:absolute;top:9px;right:14px;font-size:10px;'
        'color:#388bfd;text-transform:uppercase;letter-spacing:1.5px;'
        'font-family:Consolas,monospace;font-weight:600">SQL</span>'
        f'{content}'
        '</div>'
    )


# ── markdown2 HTML에 인라인 스타일 적용 ──────────────
def _apply_inline_styles(html):
    """class 기반 CSS 없이도 스타일이 유지되도록 모든 요소에 인라인 스타일 적용"""
    # h2, h3
    html = html.replace('<h2>', f'<h2 style="{_IS_H2}">')
    html = html.replace('<h3>', f'<h3 style="{_IS_H3}">')
    # table
    html = html.replace('<table>', f'<table style="{_IS_TABLE}">')
    html = html.replace('<thead>', f'<thead style="{_IS_THEAD}">')
    html = html.replace('<th>', f'<th style="{_IS_TH}">')
    html = html.replace('<td>', f'<td style="{_IS_TD}">')
    # blockquote: md_to_styled_html 1단계에서 이미 <div>로 변환됨 → 여기서 처리 불필요
    # pre 코드블록 (data-lang 속성 + 인라인 스타일 + 언어 라벨 span 주입)
    html = re.sub(
        r'<pre data-lang="([^"]+)"><code[^>]*>',
        lambda m: (
            f'<pre data-lang="{m.group(1)}" style="{_IS_PRE}">'
            f'<span style="{_IS_LANLABEL}">{m.group(1).upper()}</span>'
            f'<code style="{_IS_PRECODE}">'
        ),
        html
    )
    # 인라인 code (<code> 태그, style 없는 것만)
    html = html.replace('<code>', f'<code style="{_IS_CODE}">')
    # ORA-NNNNN 에러코드: 하이픈을 non-breaking hyphen(U+2011)으로 교체 → CSS 무관하게 줄바꿈 방지
    html = re.sub(
        r'\bORA-(\d+)',
        'ORA\u2011\\1',
        html
    )
    return html


# ── 마크다운 → 모던 스타일 HTML 변환 ──────────────
def md_to_styled_html(md_text):

    # 1) 요약: / blockquote(>) 줄 → 인라인 스타일 div로 선변환 (markdown2 전에 처리해야 TinyMCE 스타일 보존)
    lines = md_text.split('\n')
    processed = []
    bq_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('요약:') or stripped.startswith('요약：'):
            content = stripped[3:].strip()
            processed.append(
                f'<div style="{_IS_SUMMARY}">'
                f'<span style="{_IS_SLABEL}">📌  요약</span>'
                f'{content}</div>\n'
            )
        elif stripped.startswith('> '):
            bq_lines.append(stripped[2:])
        else:
            if bq_lines:
                content = ' '.join(bq_lines)
                processed.append(f'<div style="{_IS_BQ}">{content}</div>\n')
                bq_lines = []
            processed.append(line)
    if bq_lines:
        content = ' '.join(bq_lines)
        processed.append(f'<div style="{_IS_BQ}">{content}</div>\n')
    md_text = '\n'.join(processed)

    # 2) SQL 코드블록 선추출 (markdown2가 언어 클래스를 제거하므로 먼저 처리)
    sql_blocks = {}
    sql_counter = [0]

    def _extract_sql_block(m):
        idx = sql_counter[0]
        sql_counter[0] += 1
        sql_blocks[idx] = m.group(1)
        return f'\n\n<div id="dbai-sqlph-{idx}"></div>\n\n'

    md_text = re.sub(
        r'```[Ss][Qq][Ll]\n(.*?)```',
        _extract_sql_block,
        md_text,
        flags=re.DOTALL
    )

    # 3) 해시태그 줄 → 인라인 스타일 태그 칩 박스 변환
    ht_pattern = r'추천 해시태그[:：]\s*(.+)'
    ht_match = re.search(ht_pattern, md_text)
    hashtag_html = ""
    if ht_match:
        tags = re.findall(r'#[\w가-힣]+', ht_match.group(1))
        chips = ''.join(f'<span style="{_IS_HTCHIP}">{t}</span>' for t in tags)
        hashtag_html = (
            f'<div style="{_IS_HTAREA}">'
            f'<strong style="color:#374151;display:block;margin-bottom:6px;">🏷️ 태그</strong>'
            f'{chips}</div>'
        )
        md_text = md_text[:ht_match.start()].rstrip()

    # 4) markdown → HTML
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

    # 5) SQL placeholder → 하이라이팅 div로 교체
    for idx, code_raw in sql_blocks.items():
        placeholder = f'<div id="dbai-sqlph-{idx}"></div>'
        html_body = html_body.replace(placeholder, _sql_block_to_div(code_raw))

    # 6) 나머지 코드블록 data-lang 속성 추가
    html_body = re.sub(
        r'<pre><code class="language-([^"]+)">',
        lambda m: f'<pre data-lang="{m.group(1)}"><code class="language-{m.group(1)}">',
        html_body
    )
    html_body = html_body.replace('<pre><code>', '<pre data-lang="code"><code>')

    # (하위 호환) 혹시 남은 SQL pre 블록 처리
    def _sql_block_replace(m):
        code_raw = _html.unescape(m.group(1))
        return _sql_block_to_div(code_raw)

    html_body = re.sub(
        r'<pre data-lang="sql"><code[^>]*>(.*?)</code></pre>',
        _sql_block_replace,
        html_body,
        flags=re.DOTALL
    )

    # 7) 전체 요소에 인라인 스타일 적용
    html_body = _apply_inline_styles(html_body)

    # 8) 조립 (외부 wrapper에도 기본 폰트/색상 인라인 적용)
    full_html = (
        f'<div style="{_IS_POST}">\n'
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


# ── Chrome bar 높이 추정 (coordinate 계산용) ────────
def _find_chrome_bar_height(driver, rect):
    """Chrome UI 높이(주소창 등) 추정. execute_script 가능한 페이지에서 호출해야 함."""
    try:
        bar_h = driver.execute_script(
            "return window.outerHeight - window.innerHeight;"
        )
        if bar_h and 50 < bar_h < 200:
            return int(bar_h)
    except Exception:
        pass
    return 95  # 기본값


# ── 브라우저 실행 ───────────────────────────────────
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    # 자동화 감지 플래그 숨기기 (Kakao 안티봇 우회)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
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

    # navigator.webdriver 숨기기 (Kakao JS 탐지 우회 - 클릭 이벤트 차단 방지)
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        })
    except Exception:
        pass

    return driver


# ── 카카오 로그인 ───────────────────────────────────
def kakao_login(driver):
    print("[1] 로그인 상태 확인 중...")
    # 블로그 전용 /manage 접근 (로그인 필요 → 오탐 없는 정확한 체크)
    driver.get(f"https://{BLOG_NAME}.tistory.com/manage")
    time.sleep(5)  # 리다이렉트 완료까지 대기
    current = driver.current_url
    print(f"  현재 URL: {current}")

    # 세션 유효 체크: 블로그 /manage에 실제로 도달했는지 확인
    if f"{BLOG_NAME}.tistory.com/manage" in current:
        print("[OK] 기존 세션 유효 → 자동 진행")
        return

    print("[*] 세션 없음 → 카카오 자동 로그인 시도...")

    # 이미 로그인 페이지로 리다이렉트된 경우 → 그대로 사용
    # 다른 페이지로 갔으면 → 로그인 페이지로 이동
    if "auth/login" not in current:
        driver.get("https://www.tistory.com/auth/login")
        time.sleep(2)

    # [1단계] 카카오 로그인 버튼 클릭
    # querySelector 방식으로 직접 처리 (WebElement 인자 전달 X → Chrome crash 방지)
    print("  [1단계] 카카오 로그인 버튼 클릭...")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(1)
    # Tistory 도메인에서 Chrome bar 높이 측정 (Kakao 이동 전에 실행)
    _chrome_bar_h_measured = _find_chrome_bar_height(driver, driver.get_window_rect())

    clicked = driver.execute_script("""
        var selectors = [
            'a.btn_login.link_kakao_id',
            'a[data-kakao-id]',
            'a[href*="kakao"]',
            'button[class*="kakao"]'
        ];
        for (var i = 0; i < selectors.length; i++) {
            var el = document.querySelector(selectors[i]);
            if (el) { el.click(); return selectors[i]; }
        }
        var all = document.querySelectorAll('a, button');
        for (var j = 0; j < all.length; j++) {
            if (all[j].textContent.trim().includes('\uce74\uce74\uc624')) {
                all[j].click();
                return 'text:' + all[j].textContent.trim().substring(0, 20);
            }
        }
        return null;
    """)

    if not clicked:
        raise Exception("카카오 로그인 버튼을 찾을 수 없음 (셀렉터 확인 필요)")
    print(f"  카카오 버튼 클릭됨: {clicked}")
    time.sleep(3)

    current = driver.current_url
    print(f"  클릭 후 URL: {current}")
    driver.save_screenshot("debug_kakao_page.png")

    # 이미 로그인 완료 (Kakao 세션으로 자동 처리)
    if "tistory.com" in current and "auth/login" not in current and "kakao" not in current:
        print("[OK] 카카오 세션으로 자동 로그인 완료")
        return

    # ──────────────────────────────────────────────────────────
    # ⚠️  Kakao 도메인에서 execute_script / find_elements 금지
    #     Kakao 안티봇이 DOM 쿼리 감지 시 Chrome 강제 종료시킴
    #     URL 분석 + pyautogui 로만 상호작용
    # ──────────────────────────────────────────────────────────

    # ── Kakao 페이지 단계별 처리 ────────────────────────────
    # get_window_rect/current_url 은 안전, execute_script/find_elements 금지
    kakao_page_type = current  # 현재 URL 상태 저장

    # [2단계] 계정 선택 페이지 (simple login / select_account)
    if "simple" in current or "select_account" in current:
        print("  [2단계] 카카오 계정 선택 페이지 → 프로필 클릭...")
        time.sleep(2)

        rect = driver.get_window_rect()
        # Kakao 도메인에서는 execute_script 금지 → Tistory에서 측정한 값 사용
        chrome_bar_h = _chrome_bar_h_measured
        print(f"  Chrome UI 높이: {chrome_bar_h}px, 창 위치: ({rect['x']}, {rect['y']})")

        # 프로필 사진 위치 (viewport 기준): x≈435, y≈307 (1280px 창 레이아웃)
        # 계정 행 텍스트 (fallback): x≈617, y≈307
        # 먼저 Chrome 창에 포커스 → 이후 계정 클릭
        safe_focus_x = rect['x'] + 640
        safe_focus_y = rect['y'] + chrome_bar_h + 50  # 카드 위 빈 영역
        pyautogui.click(safe_focus_x, safe_focus_y)
        time.sleep(0.5)

        for vp_x, vp_y, desc in [
            (435, 307, "프로필 사진"),
            (617, 307, "계정 이메일"),
            (500, 307, "계정 행 중앙"),
        ]:
            click_x = rect['x'] + vp_x
            click_y = rect['y'] + chrome_bar_h + vp_y
            print(f"  {desc} 클릭: ({click_x}, {click_y})")
            pyautogui.moveTo(click_x, click_y, duration=0.3)
            time.sleep(0.2)
            pyautogui.click()
            time.sleep(0.5)
            pyautogui.press("enter")
            time.sleep(4)
            current = driver.current_url
            if "tistory.com" in current and "auth/login" not in current and "kakao" not in current:
                print(f"[OK] {desc} 클릭 → 로그인 완료")
                return
            if "simple" not in current and "select_account" not in current:
                break  # 다른 Kakao 페이지로 전환됨

        # 계정 선택 후 비밀번호 확인 페이지가 뜬 경우
        current = driver.current_url
        if "tistory.com" not in current and ("check" in current or "password" in current):
            print(f"  비밀번호 확인 페이지 → 비밀번호 입력...")
            time.sleep(1)
            pyperclip.copy(KAKAO_PASSWORD)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.3)
            pyautogui.press("enter")
            time.sleep(3)
            current = driver.current_url
            if "tistory.com" in current and "auth/login" not in current:
                print("[OK] 비밀번호 확인 → 로그인 완료")
                return

        current = driver.current_url
        print(f"  계정 선택 처리 후 URL: {current[:80]}")
        print("  → 추가 인증 필요 시 아래 180초 대기 중 처리하세요")
        # ID/PW 입력은 하지 않음 (계정 선택 페이지에서는 무의미)

    # [3단계] 카카오 로그인 폼 처리 (신규 로그인 / ID·PW 입력)
    # 계정 선택 화면이 아닌 경우에만 실행
    elif "kakao" in current:
        print("  [3단계] 카카오 로그인 폼 → ID/PW 입력 (pyautogui)...")
        time.sleep(2)
        pyperclip.copy(KAKAO_EMAIL)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.5)
        pyautogui.press("tab")   # 비밀번호 필드로 이동
        time.sleep(0.3)
        pyperclip.copy(KAKAO_PASSWORD)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(2)
        print("[OK] ID/PW 입력 완료")

    # 2FA 또는 로그인 완료 대기
    print("\n" + "=" * 54)
    print("  2FA 인증번호(문자)가 왔으면 입력해주세요.")
    print("  >> '이 브라우저에서 2단계 인증 사용 안 함' 반드시 체크")
    print("  >> 한 번 체크하면 이후 실행부터 완전 자동화됩니다.")
    print("  (최대 180초 대기)")
    print("=" * 54 + "\n")

    try:
        WebDriverWait(driver, 180).until(
            lambda d: "auth/login" not in d.current_url
                      and "kakao" not in d.current_url
                      and "tistory.com" in d.current_url
        )
    except Exception:
        raise Exception("로그인 대기 시간 초과 (180초). 다시 실행해주세요.")

    print("[OK] 로그인 성공! (다음 실행부터 완전 자동)")


# ── 글쓰기 이동 ─────────────────────────────────────
def go_to_write(driver):
    url = f"https://{BLOG_NAME}.tistory.com/manage/newpost"
    print(f"\n[5] 글쓰기 이동: {url}")
    driver.get(url)
    # 이전 임시저장 글 이어쓰기 알림 처리 → WebDriverWait으로 대기 후 닫기
    try:
        WebDriverWait(driver, 6).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        print(f"  [알림] {alert.text[:30]}... → 닫기")
        alert.dismiss()
        time.sleep(1)
    except Exception:
        time.sleep(3)  # 알림 없으면 일반 대기
    # 새 탭/창이 열렸으면 최신 창으로 전환
    handles = driver.window_handles
    if len(handles) > 1:
        print(f"  [창 전환] {len(handles)}개 창 감지 → 최신 창으로 전환")
        driver.switch_to.window(handles[-1])
        time.sleep(1)


# ── 제목 입력 (TinyMCE 에디터) ──────────────────────
def input_title(driver, title):
    print(f"[6] 제목 입력: {title}")
    time.sleep(3)  # 에디터 로딩 대기 (wait.until 폴링 → 크래시 우회)

    rect = driver.get_window_rect()
    bar_h = _find_chrome_bar_height(driver, rect)

    # 제목 영역 pyautogui 클릭 (viewport y≈185, 1280px 창 기준)
    title_x = rect['x'] + 300
    title_y = rect['y'] + bar_h + 185
    print(f"  제목 클릭: ({title_x}, {title_y})")
    pyautogui.click(title_x, title_y)
    time.sleep(0.5)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.2)
    pyperclip.copy(title)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)
    print("[OK] 제목 입력 완료")


# ── 본문 HTML 주입 (TinyMCE contenteditable 모드 대응) ─
def input_content_html(driver, html_content):
    print("[7] 본문 HTML 주입 중...")
    time.sleep(2)  # 에디터 완전 초기화 대기
    driver.execute_script("window.__postHtml = arguments[0];", html_content)

    result = driver.execute_script("""
        // ① Tistory TinyMCE iframe 직접 주입 (ID: editor-tistory_ifr)
        // <style>을 head에, 본문을 body에 분리 주입해야 CSS 클래스가 적용됨
        var iframe = document.querySelector('#editor-tistory_ifr');
        if (!iframe) iframe = document.querySelector('.tox-edit-area__iframe');
        if (iframe && iframe.contentDocument && iframe.contentDocument.body) {
            iframe.contentDocument.body.innerHTML = window.__postHtml;
            if (window.tinymce && tinymce.activeEditor) {
                tinymce.activeEditor.setDirty(true);
                try { tinymce.activeEditor.nodeChanged(); } catch(e) {}
            }
            return 'iframe:' + iframe.id;
        }
        // ② contenteditable 폴백
        var ceEl = document.querySelector('[contenteditable="true"]');
        if (ceEl) {
            ceEl.innerHTML = window.__postHtml;
            ceEl.dispatchEvent(new Event('input', {bubbles: true}));
            if (window.tinymce && tinymce.activeEditor) {
                tinymce.activeEditor.setDirty(true);
                try { tinymce.activeEditor.nodeChanged(); } catch(e) {}
            }
            return 'contenteditable';
        }
        // ③ TinyMCE setContent raw 모드
        if (window.tinymce && tinymce.activeEditor) {
            try {
                tinymce.activeEditor.setContent(window.__postHtml, {format: 'raw'});
                return 'tinymce-raw';
            } catch(e) {
                tinymce.activeEditor.setContent(window.__postHtml);
                return 'tinymce';
            }
        }
        return null;
    """)

    # 주입 후 실제 content 길이 검증
    time.sleep(1)
    content_len = driver.execute_script("""
        var iframe = document.querySelector('#editor-tistory_ifr');
        if (!iframe) iframe = document.querySelector('.tox-edit-area__iframe');
        if (iframe && iframe.contentDocument && iframe.contentDocument.body)
            return iframe.contentDocument.body.innerHTML.length;
        if (window.tinymce && tinymce.activeEditor)
            return tinymce.activeEditor.getContent().length;
        return -1;
    """)
    print(f"[OK] 본문 주입 완료: {result} (HTML 길이: {content_len}자)")


# ── 태그 입력 ───────────────────────────────────────
def input_tags(driver, tags):
    if not tags:
        return
    print(f"[9] 태그 입력: {tags}")
    time.sleep(1)
    try:
        for tag in [t.strip() for t in tags.split(",") if t.strip()]:
            driver.execute_script("""
                var el = document.querySelector('input#tagText');
                if (!el) return;
                el.focus();
                var nv = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nv.call(el, arguments[0]);
                el.dispatchEvent(new Event('input', {bubbles:true}));
                el.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter',keyCode:13,bubbles:true}));
                el.dispatchEvent(new KeyboardEvent('keyup',  {key:'Enter',keyCode:13,bubbles:true}));
            """, tag)
            time.sleep(0.4)
        print(f"[OK] 태그 완료")
    except Exception as e:
        print(f"  [경고] 태그 스킵: {e}")


# ── 카테고리 선택 ───────────────────────────────────
def select_category(driver, category):
    if not category:
        return
    print(f"[10] 카테고리: {category}")
    time.sleep(1)
    try:
        rect = driver.get_window_rect()
        bar_h = _find_chrome_bar_height(driver, rect)

        # JS로 카테고리 버튼 찾기
        result = driver.execute_script("""
            var selectors = [
                'button.btn-category', 'button[class*="category"]',
                'select[class*="category"]', '[data-label="카테고리"]',
                '[aria-label*="카테고리"]', 'button[data-id="category"]'
            ];
            for (var i = 0; i < selectors.length; i++) {
                var el = document.querySelector(selectors[i]);
                if (el) { el.click(); return selectors[i]; }
            }
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                var txt = btns[i].textContent.trim();
                if (txt.includes('\uce74\ud14c\uace0\ub9ac') || txt.includes('\ubd84\ub958')) {
                    btns[i].click(); return 'text:' + txt.substring(0, 20);
                }
            }
            return null;
        """)

        if not result:
            # pyautogui 폴백: 카테고리 드롭다운 (viewport ~280, ~132)
            cat_x = rect['x'] + 280
            cat_y = rect['y'] + bar_h + 132
            print(f"  pyautogui 카테고리 클릭: ({cat_x}, {cat_y})")
            pyautogui.click(cat_x, cat_y)
            result = 'pyautogui'
        else:
            print(f"  카테고리 버튼 클릭: {result}")

        time.sleep(1.5)
        driver.save_screenshot("debug_category_open.png")

        # 드롭다운 열린 후 항목 클릭 (li → button → 전체 탐색)
        clicked = driver.execute_script(f"""
            var target = '{category}';

            // 1) li 기반 셀렉터
            var liSelectors = [
                'ul.category-list li', '[class*="category"] li',
                '[class*="Category"] li', '[class*="panel"] li',
                '[class*="popup"] li', '[class*="dropdown"] li'
            ];
            for (var s = 0; s < liSelectors.length; s++) {{
                var items = document.querySelectorAll(liSelectors[s]);
                for (var i = 0; i < items.length; i++) {{
                    var txt = items[i].textContent.trim();
                    if (txt.includes(target)) {{
                        items[i].click();
                        return liSelectors[s] + ':' + txt;
                    }}
                }}
            }}

            // 2) role/class 기반
            var roleSelectors = [
                '[role="option"]', '[class*="category-item"]',
                '[class*="CategoryItem"]', '[class*="category_item"]',
                '[class*="list-item"]', '[class*="listItem"]', 'option'
            ];
            for (var s = 0; s < roleSelectors.length; s++) {{
                var items = document.querySelectorAll(roleSelectors[s]);
                for (var i = 0; i < items.length; i++) {{
                    var txt = items[i].textContent.trim();
                    if (txt.includes(target)) {{
                        items[i].click();
                        return roleSelectors[s] + ':' + txt;
                    }}
                }}
            }}

            // 3) 전체 li 탐색
            var allLi = document.querySelectorAll('li');
            for (var j = 0; j < allLi.length; j++) {{
                var t = allLi[j].textContent.trim();
                if (t === target || t.includes(target)) {{
                    allLi[j].click();
                    return 'li:' + t;
                }}
            }}

            // 4) button 텍스트 탐색 (카테고리 항목이 button인 경우)
            var allBtns = document.querySelectorAll('button');
            for (var k = 0; k < allBtns.length; k++) {{
                var bt = allBtns[k].textContent.trim();
                if (bt.includes(target)) {{
                    allBtns[k].click();
                    return 'button:' + bt;
                }}
            }}

            // 5) 전체 클릭 가능 요소 텍스트 탐색
            var clickable = document.querySelectorAll('a, div, span');
            for (var m = 0; m < clickable.length; m++) {{
                var ct = clickable[m].textContent.trim();
                if (ct === target || (ct.includes(target) && ct.length < 30)) {{
                    clickable[m].click();
                    return clickable[m].tagName + ':' + ct;
                }}
            }}

            // 디버그: 현재 button/li 목록 반환
            var debug = [];
            document.querySelectorAll('button, li').forEach(function(el) {{
                var t = el.textContent.trim();
                if (t) debug.push(el.tagName + '|' + t.substring(0, 25));
            }});
            return 'NOT_FOUND|' + JSON.stringify(debug.slice(0, 15));
        """)

        if clicked and not clicked.startswith('NOT_FOUND'):
            print(f"[OK] 카테고리: {clicked}")
        else:
            print(f"  [경고] 카테고리 항목 '{category}' 없음 → {clicked}")
        time.sleep(0.5)
    except Exception as e:
        print(f"  [경고] 카테고리 스킵: {e}")


# ── 임시저장 / 발행 ─────────────────────────────────
def save_post(driver, visibility):
    time.sleep(1)
    driver.save_screenshot("debug_before_save.png")

    rect = driver.get_window_rect()
    bar_h = _find_chrome_bar_height(driver, rect)
    vp_h = rect['height'] - bar_h  # 뷰포트 높이

    # 버튼 목록 디버그 출력 (셀렉터 진단용)
    try:
        btn_info = driver.execute_script("""
            var result = [];
            document.querySelectorAll('button').forEach(function(b) {
                result.push(b.className.substring(0, 40) + ' | ' + b.textContent.trim().substring(0, 20));
            });
            return result.slice(0, 15);
        """)
        print(f"  [디버그] 버튼 목록: {btn_info}")
    except Exception:
        pass

    if visibility == "0":
        print("\n[11] 임시저장 중...")
        try:
            saved = driver.execute_script("""
                var selectors = ['button.btn-save', 'button[class*="save"]',
                                 'button[class*="draft"]', 'button[class*="temporary"]'];
                for (var i = 0; i < selectors.length; i++) {
                    var el = document.querySelector(selectors[i]);
                    if (el) { el.click(); return selectors[i]; }
                }
                // 텍스트 매칭
                var btns = document.querySelectorAll('button');
                for (var j = 0; j < btns.length; j++) {
                    if (btns[j].textContent.trim().includes('\uc784\uc2dc\uc800\uc7a5')) {
                        btns[j].click();
                        return 'text:' + btns[j].textContent.trim().substring(0, 20);
                    }
                }
                // iframe 내부 탐색
                var frames = document.querySelectorAll('iframe');
                for (var k = 0; k < frames.length; k++) {
                    try {
                        var fb = frames[k].contentDocument.querySelectorAll('button');
                        for (var l = 0; l < fb.length; l++) {
                            if (fb[l].textContent.trim().includes('\uc784\uc2dc\uc800\uc7a5')) {
                                fb[l].click(); return 'iframe:\uc784\uc2dc\uc800\uc7a5';
                            }
                        }
                    } catch(e) {}
                }
                return null;
            """)
            if not saved:
                # pyautogui 폴백: 하단 바 임시저장 버튼 (우하단, 완료 버튼 왼쪽)
                # viewport 기준: x≈1047, 하단에서 ~34px
                save_x = rect['x'] + 1047
                save_y = rect['y'] + bar_h + vp_h - 34
                print(f"  pyautogui 임시저장 클릭: ({save_x}, {save_y})")
                pyautogui.click(save_x, save_y)
                saved = 'pyautogui'
            time.sleep(2)
            print(f"[OK] 임시저장 완료! ({saved})")
        except Exception as e:
            print(f"  [경고] 임시저장 실패: {e}")
    else:
        print("\n[11] 발행(완료) 중...")
        try:
            published = driver.execute_script("""
                var selectors = ['button.btn-publish', 'button[class*="publish"]',
                                 'button[class*="complete"]'];
                for (var i = 0; i < selectors.length; i++) {
                    var el = document.querySelector(selectors[i]);
                    if (el) { el.click(); return selectors[i]; }
                }
                var btns = document.querySelectorAll('button');
                for (var j = 0; j < btns.length; j++) {
                    var txt = btns[j].textContent.trim();
                    if (txt === '\uc644\ub8cc' || txt.includes('\ubc1c\ud589')) {
                        btns[j].click(); return 'text:' + txt.substring(0, 20);
                    }
                }
                return null;
            """)
            if not published:
                # pyautogui 폴백: 하단 바 완료 버튼 (우하단 맨 오른쪽)
                # viewport 기준: x≈1163, 하단에서 ~34px
                pub_x = rect['x'] + 1163
                pub_y = rect['y'] + bar_h + vp_h - 34
                print(f"  pyautogui 완료 클릭: ({pub_x}, {pub_y})")
                pyautogui.click(pub_x, pub_y)
                published = 'pyautogui'
            time.sleep(2)
            print(f"[OK] 발행 완료! ({published})")
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
