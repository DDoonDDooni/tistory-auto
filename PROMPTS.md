# Claude Code 프롬프트 모음

Claude Code 채팅에 복사해서 사용하세요.

---

## [STEP 1] 포스팅 원고 작성

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

## [STEP 2] 포스팅 실행

```
posts/post.md 내용 확인하고 이상 없으면
터미널에서 python 02_post.py 실행해줘.

실행 중 오류나면 error_screenshot.png 보고
CLAUDE.md의 셀렉터 목록 참고해서 바로 수정 후 재실행해줘.
```

---

## [STEP 3] 셀렉터 오류 수정

```
python 02_post.py 실행 중 오류가 발생했어.
오류 내용: [오류 메시지 붙여넣기]

error_screenshot.png 확인하고
CLAUDE.md 셀렉터 목록 참고해서
02_post.py에서 해당 셀렉터 찾아 수정해줘.
수정 후 바로 재실행해줘.
```

---

## [STEP 4] Claude 대화 → 포스팅 원고 변환

```
아래 대화 내용으로 posts/post.md 포스팅 원고 작성해줘.

[대화 내용 붙여넣기]

frontmatter 포함, 요약: 박스와 추천 해시태그: 줄 반드시 포함해줘.
카테고리는 작성 전에 물어봐줘.
```

---

## [STEP 5] 스타일 수정

```
02_post.py의 STYLE 변수에서 아래 항목을 수정해줘.

변경 내용: [예: 코드블록 배경색을 #1e1e1e로 변경]
추가 내용: [예: h2 소제목 폰트 사이즈 22px로 변경]

수정 후 변경된 CSS 부분만 요약해서 알려줘.
```

---

## [STEP 6] Git commit & push

```
현재 변경사항 git commit하고 origin/main으로 push해줘.
```

---

## [STEP 7] 전체 현행화

```
PROJECT_STATUS.md, PROMPTS.md, CLAUDE.md 를 현재 코드 상태에 맞게 전체 현행화해줘.
```

---

## 일상 포스팅 루틴

1. Claude Code 채팅에서 STEP 1 프롬프트로 원고 작성 요청
2. `posts/post.md` 내용 확인
3. `python 02_post.py` 실행
4. 티스토리 관리자에서 임시저장 확인 후 발행
