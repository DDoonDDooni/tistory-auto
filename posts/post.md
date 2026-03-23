---
title: "[MariaDB] Galera Cluster DR 환경 재구성 작업기"
tags: MariaDB,GaleraCluster,DR구성,SST,IST,wsrep,클러스터,재해복구,DBA,HA
category: DB 기술
visibility: 0
---
요약: OS 미복제 환경에서 Storage 복제 기반으로 MariaDB Galera Cluster DR을 재구성하면서 겪은 galera.service 오류, library 누락, SST 강제 발생 문제를 작업 순서에 따라 원인과 해결 방법을 정리합니다.

## 작업 배경 및 환경

Binary 설치 방식으로 운영 중인 MariaDB Galera Cluster를 Storage 복제 방식으로 DR 환경에 재구성하는 작업을 진행했습니다.

| 항목 | 내용 |
|------|------|
| DB 구성 | MariaDB Galera Cluster (Multi-Master) |
| 설치 방식 | Binary 설치 |
| DR 구성 방식 | Storage 복제 |
| OS 복제 여부 | 미복제 (`/etc` 등 OS 영역 제외) |

OS 영역을 복제하지 않은 환경이었기 때문에 `my.cnf`, init 스크립트, library 등 다수 항목을 수동으로 복원해야 했습니다.

---

## 이슈 발생

작업 과정에서 아래 세 가지 이슈가 순차적으로 발생했습니다.

| # | 이슈 | 영향 |
|---|------|------|
| 1 | `Unit galera.service not found` | 서비스 기동/중지 불가 |
| 2 | `libgalera_smm.so`, `libncurses` 등 library 누락 | DB 기동 불가 |
| 3 | IST가 아닌 SST 발생 | 클러스터 재구성 시간 지연 |

세 이슈 모두 OS 미복제에서 비롯된 연쇄 문제였으며, 이하 작업 순서에 따라 해결 과정을 기록합니다.

---

## 구성 작업 순서

### 1단계. Storage 복제 및 기본 환경 구성

Data, Engine, Log, Tmp 등 영역 storage 복제를 진행했습니다. Binary 기반 구성이므로 별도 엔진 설치는 불필요했고, 아래 항목을 수동 복원했습니다.

- `/etc/my.cnf` 기존 서비스 내용 복사 및 file owner 변경
- DR 환경에 맞게 IP parameter 수정

```bash
# my.cnf 내 DR 환경 IP로 수정 필요한 항목
wsrep_cluster_address = gcomm://[DR_NODE1_IP],[DR_NODE2_IP],[DR_NODE3_IP]
wsrep_node_address    = [현재 노드 DR IP]
```

---

### 2단계. galera.service Unit Not Found 해결

`service galera start` 수행 시 `Unit galera.service not found` 오류가 발생했습니다.

**원인:**

- `galera.service`는 MariaDB 공식 패키지에서 제공하지 않는 unit 파일
- MariaDB의 실제 systemd service unit 이름은 `mariadb.service` (alias: `mysql.service`, `mysqld.service`)
- 기존 서버의 `/etc/init.d/galera`는 커스텀 init 스크립트 — OS 미복제로 누락된 상태

**해결:**

```bash
# Galera RPM 별도 설치
yum localinstall galera*.rpm

# 기존 서버에서 init.d 스크립트 복사
scp [기존서버]:/etc/init.d/galera /etc/init.d/galera

# 권한 설정
chown root:root /etc/init.d/galera
chmod 755 /etc/init.d/galera

# Data, Log 영역 등 config 경로 확인 후 systemd 재로드
systemctl daemon-reload
```

---

### 3단계. 의존 library 누락 해결

Galera RPM 설치 후 DB 기동 시 library 누락 오류가 추가로 발생했습니다.

| 누락 library | 해결 방법 |
|-------------|----------|
| `libgalera_smm.so` | galera RPM 설치 (`yum localinstall galera*.rpm`) |
| `libncurses.so.5` | ncurses-libs RPM 설치 또는 symbolic link 생성 |
| `libtinfo.so.5` | symbolic link 생성 |

```bash
# ncurses library 설치
yum install ncurses-libs -y

# 설치 불가 시 symbolic link 생성
ln -s /usr/lib64/libncursesw.so.6 /usr/lib64/libncurses.so.5
ln -s /usr/lib64/libtinfo.so.6    /usr/lib64/libtinfo.so.5

ldconfig
```

---

### 4단계. 최신 노드 선정 및 Bootstrap 설정

DB 미기동 상태에서 각 노드의 데이터 최신성을 판별해야 합니다. `grastate.dat`의 `seqno`는 DB 실행 중에는 항상 `-1`로 표시되므로 `wsrep_recover`로 실제 seqno를 추출합니다.

```bash
# 각 노드에서 실행 — 실제 seqno 추출
mysqld --wsrep_recover --user=mysql

# error log에서 recovered position 확인
grep 'recovered position' /var/lib/mysql/mysql.err | tail -1

# 출력 예시
# WSREP: Recovered position: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:11246360
#                                      UUID                         seqno ↑
```

> **핵심**: seqno 값이 가장 큰 노드가 최신 데이터를 보유한 노드입니다. 반드시 최신 노드를 bootstrap 노드로 선정해야 데이터 유실을 방지할 수 있습니다.

```bash
# 최신 노드의 grastate.dat 수정
vi /var/lib/mysql/grastate.dat

# safe_to_bootstrap: 0  →  1 로 변경
# wsrep_cluster_address=gcomm://  (빈 값으로 변경)

service galera start
```

---

### 5단계. SST 발생 원인 분석 및 IST 유도

동일 시점 storage 복제 환경임에도 나머지 노드 조인 시 IST가 아닌 SST가 발생했습니다.

**원인 1 — grastate.dat seqno -1 상태로 조인**

`grastate.dat`의 `seqno`가 `-1`인 상태로 기동 시 Galera는 유효한 위치 정보가 없다고 판단하여 SST로 폴백합니다. 조인 전 `wsrep_recover`로 확인한 실제 seqno를 `grastate.dat`에 수동 기입해야 합니다.

**원인 2 — gcache preamble full reset**

gcache 파일(4GB)이 존재함에도 기동 시 gcache preamble에서 full reset이 발생했습니다. `gcache.recover` 기본값이 `yes`이므로 복구 실패 시 gcache 전체가 초기화되고 IST 불가 → SST가 발생합니다.

```bash
# error log에서 gcache full reset 확인
grep -i "gcache\|preamble" /var/lib/mysql/mysql.err | tail -20

# full reset 발생 시 로그 예시
# GCache::RingBuffer full reset
# GCache history reset: 11246337 -> 0
# GCache history reset: 0 -> 11246360
```

**IST 유도를 위한 조인 절차:**

```bash
# 1. joiner 노드 my.cnf — gcache.recover=no 설정
wsrep_provider_options="gcache.recover=no; gcache.size=4G"

# 2. wsrep_recover로 실제 seqno 확인
mysqld --wsrep_recover --user=mysql
grep 'recovered position' /var/lib/mysql/mysql.err | tail -1

# 3. grastate.dat seqno 수동 기입
vi /var/lib/mysql/grastate.dat
# seqno: [wsrep_recover로 확인한 값]

# 4. 클러스터 조인
service galera start

# 5. IST 진행 여부 확인
grep -i "ist\|sst" /var/lib/mysql/mysql.err | tail -10
```

> `gcache.recover=no` 설정은 joiner 노드에만 적용합니다. Bootstrap 노드(donor)는 이 설정과 무관합니다.

---

## 결론 및 체크리스트

### 핵심 정리

| 이슈 | 원인 | 해결 |
|------|------|------|
| `galera.service not found` | OS 미복제로 init.d 스크립트 누락 | galera RPM 설치 + init.d 스크립트 복원 |
| library 누락 | OS 미복제로 lib 파일 누락 | galera RPM + ncurses-libs 설치, symbolic link 생성 |
| SST 발생 | seqno -1 상태 조인 + gcache full reset | seqno 수동 기입 + `gcache.recover=no` |
| bootstrap 노드 선정 실패 | seqno 비교 없이 bootstrap 시도 | `wsrep_recover`로 seqno 비교 후 최신 노드 선정 |

### DR 구성 시 OS 미복제 환경 체크리스트

- [ ] `/etc/my.cnf` 복사 및 DR IP 반영 (`wsrep_cluster_address`, `wsrep_node_address`)
- [ ] `/etc/init.d/galera` 스크립트 복원 및 권한 설정
- [ ] galera RPM 설치 (`libgalera_smm.so` 확보)
- [ ] `libncurses.so.5`, `libtinfo.so.5` library 확인 및 symbolic link 생성
- [ ] 각 노드 `wsrep_recover`로 seqno 확인 → 최신 노드 bootstrap 선정
- [ ] joiner 노드 `gcache.recover=no` 설정 후 조인

### 클러스터 정상 확인 쿼리

```sql
-- 클러스터 노드 수 확인
SHOW GLOBAL STATUS LIKE 'wsrep_cluster_size';

-- 노드 동기화 상태 확인 (Synced 여부)
SHOW GLOBAL STATUS LIKE 'wsrep_local_state_comment';

-- 클러스터 상태 확인 (Primary 여부)
SHOW GLOBAL STATUS LIKE 'wsrep_cluster_status';

-- 마지막 커밋 seqno 확인 (노드 간 동일해야 함)
SELECT VARIABLE_NAME, VARIABLE_VALUE
FROM information_schema.GLOBAL_STATUS
WHERE VARIABLE_NAME IN (
    'wsrep_last_committed',
    'wsrep_local_state_uuid'
);
```

추천 해시태그: #MariaDB #GaleraCluster #DR구성 #SST #IST #wsrep #클러스터 #재해복구 #DBA #HA
