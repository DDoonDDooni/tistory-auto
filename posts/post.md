---
title: "[Oracle] OPEN_CURSORS 증가 전 꼭 확인할 것들"
tags: Oracle,OPEN_CURSORS,ORA-01000,커서튜닝,DBA
category: DB 기술
visibility: 0
---
요약: OPEN_CURSORS를 3000→4000으로 올리기 전, cursor leak 여부와 실제 사용량을 먼저 확인해야 한다. 값 증가는 재시작 없이 즉시 적용 가능하지만, 근본 원인 분석 없이 올리면 문제가 반복된다.

운영 Oracle DB에서 ORA-01000이 발생하거나 예방 차원에서 `OPEN_CURSORS`를 올리는 검토를 하게 되는 경우가 있다. 3000에서 4000으로 증가하는 작업은 간단해 보이지만, 빠뜨리면 안 되는 확인 항목이 있다.

## OPEN_CURSORS 파라미터 개요

`OPEN_CURSORS`는 **단일 세션이 동시에 열 수 있는 최대 cursor 수**를 제한하는 파라미터다.

- 기본값: 50 (실무에서는 보통 300~3000 수준)
- 초과 시 발생 에러: `ORA-01000: maximum open cursors exceeded`
- 적용 단위: 세션 단위 (인스턴스 전체가 아닌 세션별 제한)

Connection pool 환경에서는 하나의 세션이 여러 cursor를 장시간 유지하는 경우가 많아, cursor 수 부족이 OLTP 고부하 시 장애로 이어질 수 있다.

## 변경 전: 현재 cursor 사용량 확인

값을 올리기 전에 **실제 얼마나 사용 중인지** 먼저 확인해야 한다.

### 세션별 열린 cursor 수 조회

```sql
-- 세션별 현재 열린 cursor 수
SELECT s.username,
       s.sid,
       s.serial#,
       COUNT(c.cursor#) AS open_cursors
FROM   v$open_cursor c
JOIN   v$session s ON s.saddr = c.saddr
WHERE  s.username IS NOT NULL
GROUP BY s.username, s.sid, s.serial#
ORDER BY open_cursors DESC;
```

확인 포인트:
- 최대값이 현재 한도(3000)에 근접한 세션이 있는가 → 있다면 증가가 의미 있음
- 특정 세션만 비정상적으로 높은가 → cursor leak 의심 신호

### cursor leak 의심 세션 점검

```sql
-- 동일 SQL이 비정상적으로 많이 열린 경우 확인
SELECT c.user_name,
       c.sql_text,
       COUNT(*) AS cursor_count
FROM   v$open_cursor c
WHERE  c.user_name IS NOT NULL
GROUP BY c.user_name, c.sql_text
HAVING COUNT(*) > 100
ORDER BY cursor_count DESC;
```

동일한 SQL이 수백 개 이상 열려 있다면 cursor를 명시적으로 닫지 않는 코드가 원인일 가능성이 높다.

### cursor open/close 통계 확인

```sql
-- 세션별 cursor open/close 누적 통계
SELECT s.username,
       s.sid,
       n.name,
       st.value
FROM   v$sesstat st
JOIN   v$statname n ON n.statistic# = st.statistic#
JOIN   v$session s  ON s.sid = st.sid
WHERE  n.name IN ('opened cursors cumulative', 'opened cursors current')
  AND  s.username IS NOT NULL
ORDER BY s.sid, n.name;
```

`opened cursors current` 값이 지속적으로 증가하고 있다면 cursor leak을 의심해야 한다.

## 변경 방법

`OPEN_CURSORS`는 dynamic 파라미터로 **재시작 없이 즉시 적용** 가능하다.

```sql
-- 즉시 적용 (메모리 + spfile 동시 변경)
ALTER SYSTEM SET open_cursors = 4000 SCOPE=BOTH;

-- 적용 확인
SHOW PARAMETER open_cursors;
```

`SCOPE=BOTH`로 지정하면 현재 실행 중인 인스턴스와 spfile 모두에 반영되어 재시작 후에도 유지된다.

## 기대 효과와 리스크

| 항목 | 내용 |
|------|------|
| 변경 위험도 | 낮음 (Dynamic 파라미터, 재시작 불필요) |
| 기대 효과 | ORA-01000 발생 빈도 감소, 배치/OLTP 고부하 시 안정성 향상 |
| 메모리 영향 | 세션당 최대 cursor 수 증가로 PGA 사용량 소폭 증가 가능 |
| 핵심 리스크 | cursor leak이 원인이라면 값 증가는 문제를 일시적으로 은폐할 뿐 |

> cursor를 명시적으로 닫지 않는 애플리케이션 코드가 있다면, OPEN_CURSORS를 4000으로 올려도 결국 다시 ORA-01000이 발생한다.

## 권장 처리 순서

1. `v$open_cursor` 조회로 세션별 cursor 사용량 확인
2. cursor leak 의심 세션 및 SQL 존재 여부 점검
3. 실제 최대 사용량이 3000에 근접하면 증가 적용 결정
4. `ALTER SYSTEM SET open_cursors = 4000 SCOPE=BOTH;` 실행
5. 적용 후 `v$open_cursor`, `v$sesstat` 모니터링으로 효과 검증
6. cursor leak 의심 세션이 있다면 애플리케이션 팀과 코드 레벨 점검 병행

OPEN_CURSORS 증가 자체는 안전하고 빠른 조치다. 하지만 "값 올렸으니 해결"로 끝내지 말고, cursor leak 여부를 반드시 함께 점검해야 문제가 재발하지 않는다.

추천 해시태그: #Oracle #OPEN_CURSORS #ORA01000 #오라클DBA #커서튜닝 #오라클성능 #데이터베이스
