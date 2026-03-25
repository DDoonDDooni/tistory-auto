"""
setup_credentials.py
카카오 계정 비밀번호를 OS 키체인에 저장합니다.
최초 1회 또는 비밀번호 변경 시 실행하세요.

- macOS : Keychain Access에 저장
- Windows: Windows Credential Manager에 저장
"""

import json
import getpass
import keyring

KEYRING_SERVICE = "tistory-auto"

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

email = config.get("kakao_email", "")
if not email:
    email = input("카카오 이메일: ").strip()

print(f"계정: {email}")
password = getpass.getpass("카카오 비밀번호 (입력 내용은 화면에 표시되지 않습니다): ")

keyring.set_password(KEYRING_SERVICE, email, password)
print(f"\n[완료] 비밀번호가 OS 키체인에 저장됐습니다.")
print(f"  서비스명 : {KEYRING_SERVICE}")
print(f"  계정     : {email}")
print(f"  저장 위치: {'Keychain Access' if __import__('platform').system() == 'Darwin' else 'Windows Credential Manager'}")
