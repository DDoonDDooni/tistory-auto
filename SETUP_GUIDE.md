# DBA&I 티스토리 자동화 - 전체 세팅 가이드

## STEP 1. 폴더 생성 (VSCode 터미널)

```cmd
mkdir D:\DoubleD\tistory_auto
mkdir D:\DoubleD\tistory_auto\posts
cd D:\DoubleD\tistory_auto
```

---

## STEP 2. 파일 배치

아래 5개 파일을 D:\DoubleD\tistory_auto\ 에 복사합니다.

```
D:\DoubleD\tistory_auto\
├── CLAUDE.md
├── tistory_auto.code-workspace
├── config.json
├── 01_login_test.py
├── 02_post.py
└── posts\
    └── post.md
```

---

## STEP 3. config.json 수정

config.json 열어서 본인 정보로 수정합니다.

```json
{
  "kakao_email": "본인카카오이메일@kakao.com",
  "kakao_password": "본인카카오비밀번호",
  "blog_name": "블로그주소앞부분",
  "default_category": "DB 기술",
  "default_visibility": "0"
}
```

blog_name 예시: https://dbai.tistory.com 이면 "dbai" 만 입력

---

## STEP 4. 워크스페이스 열기

VSCode에서 파일 → 워크스페이스 열기 → tistory_auto.code-workspace 선택
또는 터미널에서:

```cmd
code D:\DoubleD\tistory_auto\tistory_auto.code-workspace
```

---

## STEP 5. 패키지 설치

VSCode 터미널 (Ctrl + `) 에서 실행:

```cmd
cd D:\DoubleD\tistory_auto
pip install selenium webdriver-manager markdown2 python-frontmatter
```

---

## STEP 6. 로그인 테스트

```cmd
python 01_login_test.py
```

Chrome이 자동으로 열리고 티스토리에 로그인되면 성공.
실패 시 error_screenshot.png 확인.

---

## STEP 7. 포스팅 테스트

posts\post.md 파일이 준비되면:

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

Claude Code가 시작되면 CLAUDE.md를 자동으로 읽고 프로젝트 전체를 파악합니다.

---

## Claude Code 활용 프롬프트 모음

### 로그인 오류 수정
```
01_login_test.py 실행했는데 카카오 로그인 버튼을 못 찾는 오류가 났어.
error_screenshot.png 보고 셀렉터 수정해줘.
```

### 포스팅 오류 수정
```
02_post.py 실행 중 [단계명]에서 오류가 났어.
error_screenshot.png 확인하고 해당 셀렉터 고쳐줘.
```

### 포스팅 원고 작성 요청
```
posts/post.md에 아래 조건으로 포스팅 원고 작성해줘.

주요 키워드: [키워드]
필수 형태소: [형태소1, 형태소2]
목표 글자 수: 2500자
카테고리: DB 기술
추가 내용: [실무 경험이나 명령어 등]
```

### 스타일 수정
```
02_post.py의 코드블록 배경색을 #1e1e1e 로 바꾸고
인라인 코드 색상도 파란색 계열로 변경해줘.
```

### 새 기능 추가
```
02_post.py에 포스팅 완료 후
"완료: [제목] 임시저장됨" 메시지를 윈도우 알림으로 띄워주는 기능 추가해줘.
```

### 전체 워크플로우 점검
```
CLAUDE.md 읽고 현재 프로젝트 구조 파악한 다음
02_post.py에서 개선할 수 있는 부분 있으면 알려줘.
```

---

## 일상 포스팅 루틴 (완성형)

1. Claude.ai에서 포스팅 원고 생성
2. posts\post.md 에 붙여넣기 (frontmatter 포함)
3. VSCode 터미널에서 python 02_post.py 실행
4. 티스토리 관리자에서 임시저장 확인 후 발행
