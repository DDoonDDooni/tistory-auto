---
title: "[AI자동화] 맥미니 M1 OpenClaw + 텔레그램 AI 에이전트 구축"
tags: OpenClaw,맥미니M1,AI에이전트,텔레그램봇,GeminiAPI,ClaudeCode,자동화
category: AI
visibility: 0
---
요약: 맥미니 M1에 OpenClaw를 설치하고 Gemini 무료 API와 텔레그램을 연동해 24시간 동작하는 개인 AI 에이전트를 구축했다. Claude Pro 구독을 그대로 활용하면서 추가 비용 없이 나만의 AI 비서를 만드는 전체 과정을 정리한다.

퇴근길 지하철에서 "오늘 AI 트렌드 정리해줘"라고 텔레그램에 보내면 맥미니가 알아서 정리해서 보내준다면 어떨까. 블로그 글감이 생기면 "발행해줘"라고 메시지 하나 보내면 티스토리에 자동으로 올라간다면? 그 꿈을 현실로 만들어준 도구가 OpenClaw다. 오늘은 맥미니 M1에 OpenClaw를 설치하고 텔레그램과 연동하는 전체 과정을 정리해봤다.

## 내가 만들려는 구조

본격적인 설치 전에 전체 구조를 먼저 이해하면 훨씬 수월하다.

텔레그램에서 메시지를 보내면 맥미니에서 24시간 실행 중인 OpenClaw가 메시지를 수신한다. OpenClaw는 Gemini 무료 API를 창구로 활용해 메시지를 처리하고, 실제 작업이 필요한 경우 Claude Code CLI를 subprocess로 호출해서 실행한다. 작업 결과는 다시 텔레그램으로 전달된다.

```
텔레그램 → OpenClaw(Gemini 무료, 창구 역할) → Claude Code CLI(실제 작업 처리) → 결과 → 텔레그램
```

이 구조의 핵심은 **비용**이다. Gemini는 무료 API를 사용하고, Claude Code CLI는 기존 Claude Pro 구독으로 동작한다. 추가로 나가는 비용이 없다.

내가 이 구조로 하고 싶은 업무는 크게 세 가지다.

- 아침마다 AI 트렌드와 이슈를 자동으로 정리해서 텔레그램으로 받기
- 기술 요약을 텔레그램으로 보내면 Claude Code가 블로그 포스팅 작성 후 티스토리에 자동 발행
- 날씨나 DBA 기술 문의 같은 일상적인 질의응답

## 사전 준비

이 포스팅은 아래 두 가지가 이미 설치된 상태를 기준으로 한다.

**Homebrew**는 맥에서 패키지 관리를 담당하는 필수 도구다. 설치되어 있지 않다면 `brew.sh` 공식 사이트에서 먼저 설치하자.

**iTerm2**는 기본 터미널보다 훨씬 편리한 터미널 앱이다. `iterm2.com`에서 무료로 다운로드할 수 있다.

## Node.js 설치

OpenClaw는 Node.js 기반으로 동작하기 때문에 가장 먼저 설치해야 한다. iTerm2를 열고 아래 명령어를 실행한다.

```bash
brew install node
```

설치가 완료되면 정상적으로 설치됐는지 버전을 확인한다.

```bash
node -v
npm -v
```

두 명령어 모두 버전 번호가 출력되면 정상이다.

## Claude Code CLI 설치

여기서 중요한 포인트가 하나 있다. Cursor IDE에 extension으로 설치된 Claude Code와 CLI 버전은 완전히 별개다. OpenClaw에서 Claude Code를 자동으로 호출하려면 CLI 버전이 반드시 필요하다.

```bash
npm install -g @anthropic-ai/claude-code
```

설치 후 아래 명령어로 정상 동작을 확인한다.

```bash
claude --version
```

Claude Pro 구독 계정으로 로그인되어 있으면 CLI도 동일한 구독으로 동작한다. 별도 API Key나 추가 비용이 없다.

## OpenClaw 설치

이제 핵심인 OpenClaw를 설치한다.

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

설치가 시작되면 보안 경고 화면이 나온다. OpenClaw는 파일 읽기와 명령 실행 권한을 가지기 때문에 반드시 읽어봐야 하는 내용이다. 개인 단독 사용이고 외부에 노출하지 않는 환경이라면 Yes를 선택하고 진행한다.

설치 모드는 **Quick Start**를 선택한다. 처음 설치라면 Quick Start로 기본 설정을 잡고 나중에 필요한 부분만 수동으로 수정하는 게 훨씬 효율적이다.

## 모델 설정 — Gemini 무료 API 연동

모델 선택 단계에서 **Google**을 선택한다. `Gemini CLI OAuth` 항목이 보이는데 이건 선택하지 않는다. 일부 사용자에서 구글 계정 제한이 걸리는 사례가 있어서 API Key 방식이 안전하다.

Google AI Studio(`aistudio.google.com/apikey`)에서 무료 API Key를 발급받아 입력한다. 신용카드 없이 구글 계정만 있으면 바로 발급 가능하다.

모델 선택 단계에서는 `google/gemini-2.5-flash`를 선택한다. 여기서 주의할 점이 있다. 무료 API Key를 사용할 경우 일부 모델에서 봇이 응답하지 않는 현상이 발생할 수 있다. 만약 응답이 없다면 `google/gemini-2.0-flash`로 변경해보자. 모델 변경은 언제든 아래 명령어로 가능하다.

```bash
openclaw config edit
```

## 채널 설정 — 텔레그램 연동

채널 선택 단계에서 **Telegram (Bot API)**를 선택한다. 텔레그램 봇 token이 필요한데 아직 없다면 지금 만들면 된다.

텔레그램 앱에서 `@BotFather`를 검색해서 시작한다. `/newbot` 명령어를 입력하고 봇 이름과 username을 설정한다. username은 반드시 `bot`으로 끝나야 한다. 예: `dbai_agent_bot`

설정이 완료되면 아래 형식의 token이 발급된다.

```
123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

이 token을 OpenClaw 설정에 입력한다.

## 웹 검색 설정

웹 검색 제공자 선택 단계에서 **Gemini (Google Search)**를 선택한다. 이미 Gemini API Key를 등록했으니 동일한 키를 입력하면 추가 비용 없이 웹 검색 기능을 사용할 수 있다. 아침 AI 트렌드 자동 정리에 꼭 필요한 기능이다.

## 스킬 및 hook 설정

스킬 설치 단계에서는 `gemini` 스킬만 선택한다. 나머지는 나중에 필요할 때 아래 명령어로 추가할 수 있다.

```bash
openclaw skills install 스킬명
```

hook 설정에서는 `session-memory`를 선택한다. 대화 맥락을 기억해주는 기능으로 텔레그램에서 연속 대화할 때 이전 내용을 유지해준다.

실행 모드는 **Hatch in TUI**를 선택해서 터미널에서 바로 동작 확인이 가능하도록 한다.

## 텔레그램 pairing

OpenClaw TUI가 실행된 상태에서 텔레그램 봇에 메시지를 보내면 pairing 코드가 발급된다. iTerm2에서 `Cmd + T`로 새 탭을 열고 아래 명령어를 실행한다. TUI 화면에서 입력하면 봇이 텍스트로 인식해서 명령이 실행되지 않으니 반드시 새 탭에서 실행해야 한다.

```bash
openclaw pairing approve [페어링코드]
```

`Approved telegram sender` 라는 메시지가 출력되면 텔레그램 연동이 완료된 것이다.

## 동작 확인

텔레그램 봇에서 메시지를 보내면 OpenClaw가 응답한다. TUI 화면 하단에서 현재 상태를 실시간으로 확인할 수 있다.

```
connected | idle | google/gemini-2.5-flash | tokens 16k/200k
```

이 상태가 정상이다. 이제 맥미니가 24시간 AI 에이전트로 동작한다.

## 마무리

오늘은 OpenClaw 설치와 텔레그램 연동까지 완료했다. 현재는 Gemini가 두뇌로 동작하는 상태인데, 다음 포스팅에서는 Claude Code CLI를 실제로 연결해서 블로그 자동 발행과 아침 트렌드 정리 자동화까지 구현해볼 예정이다. 설치하면서 궁금한 점이나 막히는 부분이 있었다면 댓글로 남겨주세요. 함께 해결해봐요!

추천 해시태그: #OpenClaw #맥미니M1 #AI에이전트 #텔레그램봇 #GeminiAPI무료 #ClaudeCode #자동화 #DBA
