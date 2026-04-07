---
title: "[MariaDB] Galera DR - IST vs SST 심층 분석"
tags: MariaDB,GaleraCluster,IST,SST,DR,Replication,HA,DBA,gcache
category: DB 기술
visibility: 0
---
요약: MariaDB Galera Cluster DR 환경을 Storage 복제 방식으로 구성하는 과정에서 IST가 아닌 SST가 지속 발생하는 근본 원인을 심층 분석합니다. gcache preamble의 synced 플래그가 핵심이며, 라이브 복제 환경에서 IST는 설정이 아닌 Galera 설계상의 구조적 한계임을 확인합니다.

## 1. 이슈 발생

### 상황 설명

MariaDB Galera Cluster DR 환경을 Storage 복제 방식으로 구성하는 과정에서 IST가 아닌 SST가 지속적으로 발생하였습니다. 이전 작업에서 SST 발생 원인을 1차 분석한 데 이어, `gcache.recover=no` 적용 및 seqno 수동 설정 후 IST 유도를 재시도하였으나 동일하게 SST가 발생하여 심층 원인 분석을 진행하였습니다.

### 이슈 내용 및 영향도

- `gcache.recover=no` 적용 및 seqno 수동 설정에도 SST 지속 발생
- SST 소요 시간 약 4분 (mariabackup 방식, 현재 데이터 기준)
- 데이터 용량 증가 시 SST 시간 비례 증가로 빠른 DR 전환 불가

---

## 2. 분석

### [이전 작업 요약] 1차 SST 발생 원인 분석

이전 작업에서 파악된 내용을 간략히 정리합니다.

#### SST 발생 원인 1 — grastate.dat seqno -1 상태로 조인

- DB 미기동 상태의 `grastate.dat` seqno는 항상 -1
- -1 상태로 조인 시 Galera가 유효한 위치 정보 없음으로 판단 → SST 발생
- 해결 시도: `wsrep_recover`로 실제 seqno 확인 후 `{DATADIR}/grastate.dat`에 수동 기입

```bash
# wsrep_recover로 실제 seqno 확인
mysqld --wsrep_recover --user=mysql
grep "recovered position" {LOGDIR}/error/mysqlerr.log | tail -1
# 결과: d028e009-4566-11ee-aede-2a16e5fd3617:11779812
```

#### SST 발생 원인 2 — gcache preamble full reset

- `gcache.recover` 기본값 `yes`로 인해 gcache 복구 실패 시 전체 초기화 발생
- gcache 내 writeset 소실 → IST 불가 → SST 발생
- 해결 시도: `gcache.recover=no` 설정 적용

```
# 이전 작업에서 확인된 gcache full reset 로그
GCache::RingBuffer full reset
GCache history reset: 11246337 -> 0
GCache history reset: 0 -> 11246360
```

---

### [현재 작업] gcache.recover=no 적용 후 재시도 및 심층 분석

#### ① 설정 적용 및 조건 확인

```bash
# my.cnf 설정 변경
wsrep_provider_options="gcache.recover=no; gcache.size=4G"
```

```bash
# grastate.dat seqno 수동 기입
vi {DATADIR}/grastate.dat
# uuid:  d028e009-4566-11ee-aede-2a16e5fd3617
# seqno: 11779812
# safe_to_bootstrap: 0
```

donor 노드 gcache 보유 범위 확인:

```bash
grep -i "gapless" {LOGDIR}/error/mysqlerr.log | tail -5
# GCache::RingBuffer: found gapless sequence 11690753-11779829
```

IST 가능 조건 검증:

```
donor gcache 범위: 11690753 ~ 11779829
joiner seqno:      11779812

11690753 ≤ 11779812 ≤ 11779829  →  ✅ seqno 범위 조건 충족
```

> seqno 범위 조건은 충족됐음에도 SST가 발생 → 로그 심층 분석 진행

---

#### ② 조인 시점 전체 로그 분석

**단계 1 — 기동 및 wsrep_recover**

```
15:24:42  Recovered position: d028e009-...:11779812  ← seqno 정상 확인
15:32:27  Found saved state: d028e009-...:11779812, safe_to_bootstrap: 0
15:32:27  GCache DEBUG: opened preamble  → 다음 단계로
```

**단계 2 — gcache preamble 확인 (핵심 원인)**

```
GCache preamble:
  UUID:    d028e009-4566-11ee-aede-2a16e5fd3617
  seqno:   -1 ~ -1   ← ⚠️ 유효하지 않음
  offset:  -1
  synced:  0          ← 비정상 종료 상태
```

**단계 3 — 클러스터 연결 및 IST 준비**

```
gcomm: connecting to group 'mps_galera'
connection established to MPS1
act_id = 11779831 / last_appl = 11779830

IST uuid: d028e009-... f:11779813, l:11779832
Prepared IST receiver for 11779813-11779832  ← IST 준비까지 완료됨
```

**단계 4 — SST 결정 (IST 준비 완료에도 SST 선택)**

```
State transfer needed: yes
Group state:  d028e009-...:11779832
Local state:  d028e009-...:11779812
Selected MPS1 as donor
Proceeding with SST  ← IST 준비 완료했음에도 SST 결정
```

**단계 5 — SST 진행 (mariabackup, 약 4분 소요)**

```
15:32:28  mariabackup SST started on joiner
15:36:50  State transfer to MPS2 complete
15:36:51  Preparing the backup
```

**단계 6 — SST 완료 후 IST 전환**

```
SST succeeded for position d028e009-...:11779832
GCache history reset: 0 → d028e009-...:11779832
####### IST applying starts with 11779833
Receiving IST... 100.0% (1/1 events) complete  ← IST 1개 수신
Shifting JOINER → JOINED → SYNCED
Server MPS2 synced with group  ← 최종 정상 완료
```

---

#### ③ gcache preamble 개념 및 SST 결정 메커니즘 분석

**gcache preamble이란**

`galera.cache` 파일의 헤더 영역으로, Galera가 IST/SST를 결정할 때 가장 먼저 참조하는 메타정보입니다.

```
galera.cache 파일 구조
┌─────────────────────────────┐
│  preamble (헤더)             │
│  - UUID     : 클러스터 식별자 │
│  - seqno_min: 최소 writeset  │
│  - seqno_max: 최대 writeset  │
│  - synced   : 정상종료 여부  │  ← 0이면 gcache 무효 처리
├─────────────────────────────┤
│  ring buffer (실제 데이터)   │
│  writeset 11690753 ~ ...    │
└─────────────────────────────┘
```

**IST/SST 결정 순서**

```
① preamble synced 확인
   synced=0  →  gcache 무효 → SST 결정 (이후 단계 무시)
   synced=1  →  다음 단계로

② preamble seqno_min ~ seqno_max 범위 확인
   joiner seqno 범위 내  →  IST 시도
   joiner seqno 범위 밖  →  SST 결정
```

**DB 종료 상태에 따른 preamble 값**

| DB 종료 상태 | synced | seqno | IST 가능 여부 |
|---|---|---|---|
| 정상 종료 | 1 | 유효한 값 | ✅ 가능 |
| 비정상 종료 | 0 | -1 | ❌ 불가 |
| 라이브 상태 복제 | 0 | -1 | ❌ 불가 |

---

#### ④ 라이브 스토리지 복제 시 preamble이 항상 -1인 이유

```
DB 프로세스 실행 중
        ↓
preamble synced=0, seqno=-1 (실행 중에는 항상 미완성 상태)
        ↓
라이브 상태로 스토리지 복제
        ↓
복제된 gcache preamble도 동일하게 synced=0, seqno=-1
        ↓
gcache.recover=no 설정에도 관계없이 IST 불가
```

> preamble은 **DB 정상 종료 시점에만** synced=1, seqno 유효값으로 기록됩니다. 라이브 복제는 이 시점을 포착할 수 없습니다.

---

#### ⑤ IST 유도를 위한 추가 시도 검토 결과

**preamble 강제 수정 가능 여부**
- gcache 파일은 바이너리 형식으로 공식적인 수동 수정 방법 없음
- 강제 수정 시 preamble seqno와 실제 ring buffer 내용 불일치로 데이터 정합성 파괴 위험
- **시도 불가 결론**

**bootstrap 후 트랜잭션 발생으로 IST 유도 가능 여부**

```
bootstrap 후 gcache seqno_min: 11779832  (bootstrap 시점)
joiner seqno:                  11779812

11779812 < 11779832  →  joiner seqno가 gcache 범위 밖
→  IST 불가
```

- bootstrap 시점 seqno가 이미 joiner seqno보다 높아 트랜잭션 추가로도 해결 불가
- **시도 불가 결론**

---

#### ⑥ Galera IST가 실제로 동작하는 케이스

| 구성 방법 | IST 가능 여부 | 이유 |
|---|---|---|
| 운영 중 노드 일시 중단 후 재조인 | ✅ 가능 | gcache 유효, seqno 연속 |
| 네트워크 순단 후 재연결 | ✅ 가능 | gcache 범위 내 gap만 수신 |
| DB 정상 종료 후 재기동 | ✅ 가능 | preamble 정상 기록됨 |
| 정상 종료 후 스토리지 복제 | ✅ 가능 | preamble 유효 상태로 복제 |
| **라이브 스토리지 복제 DR 구성** | ❌ 불가 | preamble 항상 synced=0 |
| **신규 노드 추가** | ❌ 불가 | gcache 자체 없음 |

> **IST는 기존 클러스터 멤버였던 노드가 잠시 이탈 후 재조인하는 경우에 동작하는 메커니즘입니다.** DR 구성처럼 완전히 새로운 환경을 구성하는 경우는 IST 대상이 아닙니다.

---

### 분석 결과 종합

| 시도 항목 | 결과 | 비고 |
|---|---|---|
| `gcache.recover=no` 적용 | gcache full reset 방지됨 | preamble 문제는 별개 |
| seqno 수동 설정 | 정상 적용됨 | seqno 범위 조건 충족 |
| gcache preamble 확인 | synced=0, seqno=-1 | 라이브 복제의 구조적 한계 |
| IST 준비 | 완료됨 | preamble 무효로 SST 폴백 |
| preamble 강제 수정 | 불가 | 데이터 정합성 파괴 위험 |
| 트랜잭션 발생으로 IST 유도 | 불가 | seqno 범위 구조적 불충족 |

---

## 3. 결론

### 핵심 발견사항

라이브 스토리지 복제 기반 DR 구성에서 IST는 **설정이나 파라미터 문제가 아닌 Galera 설계상의 구조적 한계**로 불가능합니다.

```
라이브 복제 → preamble synced=0
        ↓
gcache.recover=no  →  full reset 방지 가능
seqno 수동 설정    →  범위 조건 충족 가능
preamble synced=0  →  변경 불가, IST 결정 단계에서 SST로 폴백
        ↓
SST 불가피
```

### Storage 복제 DR 구성의 한계

데이터 용량이 커질수록 SST 소요 시간이 비례하여 증가합니다. 빠른 DR 전환(낮은 RTO)이 목표인 환경에서는 현실적인 제약이 존재합니다.

| 데이터 규모 | SST 예상 소요 시간 | DR 전환 가능 여부 |
|---|---|---|
| 수십 GB | 수 분 | 가능 |
| 수백 GB | 수십 분 | 제한적 |
| TB 이상 | 수 시간 | 사실상 불가 |

---

## 4. 권고 구성 방안 — Replication 기반 DR + Galera 재구성

빠른 DR 전환이 목표라면 아래 구성을 권고합니다.

### 구성 개요

```
운영 환경 (Galera 3 Node)
  Node 1
  Node 2  ─── Replication (비동기) ───▶  DR Node 1개
  Node 3                                  (실시간 동기화)
  (Source: 사용량 적은 노드 선택)
                                               │
                                      DR 전환 시
                                               ▼
                                     DR Node 기준으로
                                     Galera 3 Node 재구성
```

### 구성 방식 비교

| 항목 | Storage 복제 DR | Replication 기반 DR |
|---|---|---|
| DR 전환 시간 | SST 소요 시간 의존 | 거의 즉시 |
| 데이터 최신성 | 복제 시점 snapshot | 실시간 동기화 |
| 용량 증가 영향 | SST 시간 비례 증가 | 영향 없음 |
| 구성 복잡도 | 낮음 | 중간 |

### Replication 구성 절차

```sql
-- 1. 운영 환경에서 가장 사용량이 적은 노드를 Source로 설정
SHOW MASTER STATUS;

-- 2. DR Node에서 Replication 구성
CHANGE REPLICATION SOURCE TO
    SOURCE_HOST='[운영 Node IP]',
    SOURCE_USER='repl_user',
    SOURCE_PASSWORD='password',
    SOURCE_AUTO_POSITION=1;

START REPLICA;

-- 3. 복제 정상 여부 확인
SHOW REPLICA STATUS\G
-- Replica_IO_Running: Yes
-- Replica_SQL_Running: Yes
-- Seconds_Behind_Source: 0
```

### DR 전환 시 절차

```bash
# 1. DR Node Replication 중단
STOP REPLICA;

# 2. DR Node를 Galera bootstrap 노드로 기동
vi {DATADIR}/grastate.dat
# safe_to_bootstrap: 1
# wsrep_cluster_address=gcomm://

service galera start

# 3. 추가 노드 2대 Galera 조인 (SST로 동기화)
# DR Node 기준 최신 데이터로 구성됨
service galera start

# 4. 클러스터 정상 확인
mysql -u root -p -e "SHOW GLOBAL STATUS LIKE 'wsrep_cluster_size';"
mysql -u root -p -e "SHOW GLOBAL STATUS LIKE 'wsrep_local_state_comment';"
```

### 향후 계획

- Replication 기반 DR Node 구성 검토 및 적용
- DR 전환 절차 표준화 및 Runbook 작성
- DR 전환 시간 목표(RTO) 기준으로 구성 방식 최종 결정

추천 해시태그: #MariaDB #GaleraCluster #IST #SST #DR #gcache #Replication #HA #DBA #데이터베이스
