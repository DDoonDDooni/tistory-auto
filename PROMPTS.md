# Cursor 명령 프롬프트 모음

이 파일의 프롬프트를 Cursor 채팅에 복사해서 사용하세요.

---

## [STEP 1] 포스팅 실행 (다음 단계)

```
PROJECT_STATUS.md와 CLAUDE.md를 먼저 읽고 현재 상태를 파악해줘.

⚠️ 로그인은 이미 완료된 상태야. chrome_profile에 세션이 저장되어 있어.
로그인 테스트나 로그인 재시도는 하지 마. 포스팅 실행만 해줘.

아래 순서로 진행해줘:

1. posts/post.md 내용 확인 (frontmatter 포함)
2. 터미널에서 python 02_post.py 실행
3. 실행 중 오류 발생 시:
   - error_screenshot.png 확인
   - CLAUDE.md의 셀렉터 목록 참고
   - 02_post.py에서 해당 셀렉터 찾아 수정 후 재실행
   - 로그인 오류가 아닌 경우 로그인 재시도 하지 말 것
4. 성공 시 PROJECT_STATUS.md의 미완료 항목 체크 업데이트
```

---

## [STEP 2] 원고 작성

```
PROJECT_STATUS.md와 CLAUDE.md를 먼저 읽어줘.

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

## [STEP 3] 셀렉터 오류 수정

```
PROJECT_STATUS.md와 CLAUDE.md를 먼저 읽어줘.

python 02_post.py 실행 중 오류가 발생했어.
오류 내용: [오류 메시지 붙여넣기]

error_screenshot.png 확인하고
CLAUDE.md 셀렉터 목록 참고해서
02_post.py에서 해당 셀렉터 찾아 수정해줘.
수정 후 바로 재실행해줘.
수정된 셀렉터는 CLAUDE.md에도 반영해줘.
```

---

## [STEP 4] GitHub Push

```
PROJECT_STATUS.md와 CLAUDE.md를 먼저 읽어줘.

D:\DoubleD\tistory_auto 프로젝트를 GitHub 신규 repo로 push해줘.

순서:
1. .gitignore 생성 (config.json, chrome_profile/, error_screenshot.png, __pycache__/, *.pyc)
2. GitHub에 신규 public repo 생성: 이름 tistory-auto
3. git init → git add . → git status로 config.json 미포함 확인 → commit → push

push 전에 반드시 config.json이 staged에 없는지 검증 후 진행해줘.
```

---

## [STEP 5] 스타일 수정

```
PROJECT_STATUS.md와 CLAUDE.md를 먼저 읽어줘.

02_post.py의 STYLE 변수에서 아래 항목을 수정해줘.

변경 내용: [예: 코드블록 배경색을 #1e1e1e로 변경]
추가 내용: [예: h2 소제목 폰트 사이즈 22px로 변경]

수정 후 변경된 CSS 부분만 요약해서 알려줘.
```

---

## [STEP 6] 진행 상황 업데이트

```
PROJECT_STATUS.md를 현재 상태에 맞게 업데이트해줘.

완료된 항목: [항목 입력]
새로 발견된 이슈: [이슈 입력]
다음 단계: [단계 입력]
```

---

## [STEP 7] Claude 대화 → 포스팅 원고 변환

```
PROJECT_STATUS.md와 CLAUDE.md를 먼저 읽어줘.

아래 대화 내용으로 posts/post.md 포스팅 원고 작성해줘.
카테고리: [DB 기술 / AI Agent / 웹 개발 / 일상]

[대화 내용 붙여넣기]

frontmatter 포함, 요약: 박스와 추천 해시태그: 줄 반드시 포함해줘.
```
