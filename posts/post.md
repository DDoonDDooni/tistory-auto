---
title: "[AI자동화] Mac 개발환경 세팅 - Homebrew 설치 완벽 가이드"
tags: Mac,Homebrew,개발환경,macOS,패키지매니저,M1,M2,Apple Silicon,개발자,세팅
category: DB 기술
visibility: 0
---
요약: Mac에서 개발환경을 구축할 때 가장 먼저 설치하는 Homebrew의 설치 방법과 기본 사용법, Apple Silicon(M1/M2/M3) 환경에서의 주의사항을 정리합니다.

## Homebrew란?

Homebrew는 macOS(및 Linux)용 패키지 매니저입니다. 개발에 필요한 도구들을 터미널 명령어 하나로 설치, 업데이트, 삭제할 수 있어 Mac 개발환경 세팅의 시작점이 됩니다.

| 항목 | 내용 |
|------|------|
| 공식 사이트 | brew.sh |
| 지원 OS | macOS, Linux |
| 설치 위치 (Intel) | `/usr/local` |
| 설치 위치 (Apple Silicon) | `/opt/homebrew` |

---

## 사전 요구사항

Homebrew 설치 전 아래 항목이 준비되어 있어야 합니다.

### Command Line Tools 설치

Xcode Command Line Tools가 없으면 Homebrew 설치 중 오류가 발생합니다. 터미널에서 아래 명령어로 먼저 설치합니다.

```bash
xcode-select --install
```

팝업 창이 뜨면 "설치" 버튼을 클릭하고 완료될 때까지 대기합니다. 이미 설치된 경우 아래 메시지가 출력됩니다.

```bash
xcode-select: error: command line tools are already installed
```

---

## Homebrew 설치

### 설치 명령어

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

설치 중 macOS 로그인 비밀번호를 요구할 수 있습니다. 설치 완료까지 수 분이 소요됩니다.

### Apple Silicon(M1/M2/M3) 환경 추가 설정

Apple Silicon Mac은 Homebrew 설치 경로가 `/opt/homebrew`로 Intel Mac과 다릅니다. 설치 완료 후 터미널에 아래 메시지가 출력되면 **반드시 PATH를 등록해야 합니다.**

```bash
# 설치 완료 후 출력되는 안내 메시지
==> Next steps:
- Run these commands in your terminal to add Homebrew to your PATH:
    echo >> ~/.zprofile
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
```

안내대로 명령어를 실행하거나 직접 `.zprofile`에 추가합니다.

```bash
echo >> ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

> PATH 등록을 하지 않으면 새 터미널 창에서 `brew: command not found` 오류가 발생합니다.

---

## 설치 확인

```bash
brew --version
```

아래와 같이 버전 정보가 출력되면 정상 설치된 것입니다.

```bash
Homebrew 5.1.1
```

---

## 기본 사용법

### 패키지 설치 / 삭제

```bash
# 패키지 설치
brew install <패키지명>

# 패키지 삭제
brew uninstall <패키지명>

# 설치된 패키지 목록 확인
brew list
```

### 패키지 검색 및 정보 확인

```bash
# 패키지 검색
brew search python

# 패키지 상세 정보
brew info python@3.12
```

### 업데이트

```bash
# Homebrew 자체 업데이트
brew update

# 설치된 패키지 전체 업그레이드
brew upgrade

# 특정 패키지만 업그레이드
brew upgrade python@3.12
```

### Cask — GUI 앱 설치

`brew install`은 CLI 도구용, GUI 앱(Chrome, VSCode 등)은 `--cask` 옵션을 사용합니다.

```bash
# Google Chrome 설치
brew install --cask google-chrome

# Visual Studio Code 설치
brew install --cask visual-studio-code

# 설치된 Cask 목록 확인
brew list --cask
```

---

## 자주 쓰는 개발 패키지 모음

개발환경 초기 세팅 시 주로 함께 설치하는 패키지 목록입니다.

```bash
# Python
brew install python@3.12

# Node.js
brew install node

# Git
brew install git

# wget / curl
brew install wget

# jq (JSON 파싱)
brew install jq
```

---

## 문제 진단 — brew doctor

설치나 실행 중 이상 증상이 있을 때 `brew doctor`로 환경 문제를 점검합니다.

```bash
brew doctor
```

`Your system is ready to brew.` 메시지가 출력되면 정상입니다. 경고 메시지가 있으면 안내에 따라 조치 후 재실행합니다.

---

## 정리

| 명령어 | 설명 |
|--------|------|
| `brew install <pkg>` | 패키지 설치 |
| `brew uninstall <pkg>` | 패키지 삭제 |
| `brew upgrade` | 전체 업그레이드 |
| `brew list` | 설치 목록 |
| `brew search <pkg>` | 패키지 검색 |
| `brew install --cask <app>` | GUI 앱 설치 |
| `brew doctor` | 환경 진단 |

Mac 개발환경 세팅의 첫 단계는 Homebrew입니다. 설치 후 Python, Node.js, Git 등을 차례로 추가하면 대부분의 개발 작업을 바로 시작할 수 있습니다.

추천 해시태그: #Mac #Homebrew #개발환경 #macOS #패키지매니저 #AppleSilicon #M1 #M2 #개발자 #환경세팅
