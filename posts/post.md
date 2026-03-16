---
title: "[ExaCC] Oracle 19c Multitenant PDB 생성 및 TDE 설정 가이드"
tags: ExaCC,Oracle,PDB,Multitenant,TDE,CDB,Oracle19c
category: DB 기술
visibility: 0
---
요약: ExaCC 환경에서 Oracle 19c CDB에 PDB를 생성하고, TDE wallet 설정까지 완료하는 전체 절차를 단계별로 정리합니다.

## PDB 생성 (RECO 영역 사용)

SEED DB의 기본 파일 영역은 `+DATA`이지만, ExaCC 환경에서는 데이터 파일을 `+RECO` 영역에 생성하도록 `FILE_NAME_CONVERT`를 명시합니다.

```sql
CREATE PLUGGABLE DATABASE NEW_PDB
  ADMIN USER ADMINUSER IDENTIFIED BY {PWD}
  ROLES = (DBA)
  FILE_NAME_CONVERT = ('+DATA', '+RECO');
```

> `FILE_NAME_CONVERT`를 생략하면 SEED DB의 기본 경로(+DATA)를 그대로 사용하므로, 영역 설계에 맞게 반드시 지정할 것.

생성 후 PDB 목록을 확인합니다.

```sql
SHOW PDBS;
```

---

## PDB Open 및 상태 저장

생성 직후 PDB는 `MOUNTED` 상태이므로 `OPEN` 상태로 전환해야 접속 가능합니다.

```sql
ALTER PLUGGABLE DATABASE NEW_PDB OPEN;
SHOW PDBS;
ALTER PLUGGABLE DATABASE NEW_PDB SAVE STATE;
```

`SAVE STATE`를 실행하지 않으면 CDB 재기동 시 PDB가 자동으로 OPEN되지 않으므로 반드시 설정합니다.
특히 ExaCC 환경에서는 패치 작업이나 DR Failover 이후 PDB가 MOUNTED 상태로 남아 서비스 중단이 발생할 수 있습니다.

---

## PDB 접속 및 Tablespace 확인

CDB에서 PDB 컨테이너로 전환 후 tablespace 목록을 확인합니다.

```sql
ALTER SESSION SET CONTAINER = NEW_PDB;

SELECT TABLESPACE_NAME, STATUS, CONTENTS
FROM   DBA_TABLESPACES;
```

---

## 리스너 서비스 확인

PDB가 생성되면 기존 listener에 PDB 서비스가 자동 등록됩니다. FQDN 형태로 추가되었는지 확인합니다.

```bash
lsnrctl status LISTENER
```

`Service` 섹션에 `NEW_PDB.{DB_DOMAIN}` 형태의 FQDN 서비스가 추가된 것을 확인합니다.
등록되어 있지 않다면 PDB를 `CLOSE` 후 재 `OPEN`하거나 listener를 `reload`합니다.

---

## TDE Wallet 상태 확인

TBS 생성 전 TDE 설정이 필요합니다. 먼저 wallet 상태를 확인합니다.

```sql
SELECT CON_ID, WRL_TYPE, WRL_PARAMETER, STATUS, WALLET_TYPE
FROM   V$ENCRYPTION_WALLET;
```

`STATUS`가 `OPEN_NO_MASTER_KEY` 또는 `CLOSED`인 경우 아래 절차를 진행합니다.

---

## Autologin → Password Wallet 전환 및 Master Key 생성

### 1. SSO 파일 백업 (Autologin 비활성화 준비)

Autologin keystore(cwallet.sso)를 백업하여 일시적으로 비활성화합니다.

```bash
mv cwallet.sso cwallet.sso.bak
```

### 2. CDB에서 Keystore Close 후 Password 모드로 재 Open

```sql
-- CDB$ROOT에서 실행
ADMINISTER KEY MANAGEMENT SET KEYSTORE CLOSE;
ADMINISTER KEY MANAGEMENT SET KEYSTORE OPEN
  IDENTIFIED BY {PWD}
  CONTAINER = ALL;
```

### 3. PDB에서 TDE Master Key 생성 (AES256)

```sql
ALTER SESSION SET CONTAINER = NEW_PDB;

ADMINISTER KEY MANAGEMENT SET KEY
  USING ALGORITHM 'AES256'
  IDENTIFIED BY {PWD}
  WITH BACKUP;
```

### 4. CDB에서 Autologin Keystore 재생성

```sql
-- CDB$ROOT에서 실행
ADMINISTER KEY MANAGEMENT CREATE AUTO_LOGIN KEYSTORE
  FROM KEYSTORE '{WALLET_PATH}'
  IDENTIFIED BY {PWD};
```

경로는 `V$ENCRYPTION_WALLET`의 `WRL_PARAMETER` 컬럼에서 확인합니다.

---

## DB 재기동 후 Autologin 확인

Autologin 변경 사항 적용을 위해 DB를 재기동합니다.
ExaCC(RAC) 환경에서는 반드시 `srvctl`을 사용합니다.

```bash
srvctl stop database -d {DB_NAME}
srvctl start database -d {DB_NAME}
```

재기동 후 wallet 상태를 확인합니다.

```sql
SELECT CON_ID, WRL_TYPE, WRL_PARAMETER, STATUS, WALLET_TYPE
FROM   V$ENCRYPTION_WALLET;
```

`STATUS = OPEN`, `WALLET_TYPE = AUTOLOGIN`이면 정상입니다.

---

## Tablespace 생성

TDE 설정 완료 후 신규 PDB에 tablespace를 생성합니다.

```sql
ALTER SESSION SET CONTAINER = NEW_PDB;

CREATE BIGFILE TABLESPACE NEW_TBS
  DATAFILE '+RECO'
  AUTOEXTEND OFF;
```

### 참고) Default tablespace 타입 확인

```sql
SELECT PROPERTY_NAME, PROPERTY_VALUE
FROM   DATABASE_PROPERTIES
WHERE  PROPERTY_NAME = 'DEFAULT_TBS_TYPE';
```

---

## 주의사항

| 항목 | 설명 |
|------|------|
| TDE Master Key 미설정 | tablespace 생성 시 `ORA-28361` 오류 발생 |
| SAVE STATE 미설정 | CDB 재기동/Failover 시 PDB가 MOUNTED 상태로 남음 |
| +DATA/+RECO 구분 | ExaCC에서 disk group 용도를 팀 내 정책으로 통일할 것 |
| shutdown/startup 금지 | RAC 환경에서는 `srvctl` 사용, `shutdown/startup` 지양 |

추천 해시태그: #ExaCC #Oracle #PDB #Multitenant #TDE #CDB #Oracle19c #오라클 #DBA
