---
title: "[Oracle] ORA-01000 예방 OPEN_CURSORS 튜닝 실무 가이드"
tags: Oracle,OPEN_CURSORS,ORA-01000,커서튜닝,DBA,오라클성능
category: DB 기술
visibility: 0
---

요약: Oracle OPEN_CURSORS를 3000→4000으로 올리기 전에 반드시 실제 사용량을 먼저 확인해야 합니다. 값 증가는 위험도가 낮지만, 커서 누수(Cursor Leak)가 원인이라면 값만 올리면 문제가 재발합니다.

Oracle DBA라면 ORA-01000 에러를 한 번쯤 마주해봤을 겁니다. 세션이 열 수 있는 커서 수 한도를 초과했다는 에러인데요. 보통 이 에러가 나면 OPEN_CURSORS 값을 올리는 게 첫 번째 반응입니다. 하지만 값만 올리는 게 능사가 아닐 수 있어요. 3000에서 4000으로 올리는 작업을 검토하면서 정리한 내용을 공유합니다.

## OPEN_CURSORS가 뭔가요

OPEN_CURSORS는 **단일 세션이 동시에 열 수 있는 커서의 최대 수**를 제한하는 파라미터입니다. 세션 전체가 아니라 세션 하나당 기준이에요.

기본값은 300이지만 OLTP 환경이나 Connection Pool을 쓰는 환경에서는 이 값이 금방 모자랍니다. 특히 세션 재사용이 많은 WAS 환경에서는 커서가 제대로 닫히지 않으면 순식간에 한도에 도달합니다.

## 변경 전 반드시 확인할 것

값을 올리기 전에 **현재 얼마나 쓰고 있는지**부터 봐야 합니다.

```sql
-- 세션별 현재 열린 커서 수
SELECT s.username, s.sid, s.serial#,
       COUNT(c.cursor#) AS open_cursors
FROM v$open_cursor c
JOIN v$session s ON s.saddr = c.saddr
WHERE s.username IS NOT NULL
GROUP BY s.username, s.sid, s.serial#
ORDER BY open_cursors DESC;
```

여기서 확인할 포인트는 두 가지입니다.

**1. 최대값이 현재 한도(3000)에 근접한 세션이 있는가**
실제로 3000에 가깝게 쓰고 있다면 증가가 의미 있습니다. 반면 최대 수백 개 수준이라면 4000으로 올려봤자 근본 원인이 따로 있다는 신호입니다.

**2. 특정 세션만 비정상적으로 높은가**
일부 세션만 수천 개를 열고 있다면 그 세션의 애플리케이션 코드에 커서 누수가 있을 가능성이 큽니다.

## 실제 변경 방법

Dynamic 파라미터라 재시작 없이 즉시 적용됩니다. 운영 중에 바로 올릴 수 있어서 변경 위험도 자체는 낮은 편입니다.

```sql
ALTER SYSTEM SET open_cursors = 4000 SCOPE=BOTH;
```

`SCOPE=BOTH`는 메모리와 spfile 양쪽에 모두 적용한다는 의미입니다. 재시작 후에도 유지됩니다.

적용 후 확인:

```sql
SHOW PARAMETER open_cursors;
```

## 값 증가의 부작용

모든 파라미터 튜닝이 그렇듯 트레이드오프가 있습니다.

**메모리 사용량 증가**
커서 최대 수가 늘어나면 세션당 할당 가능한 메모리도 늘어납니다. 세션 수가 많은 환경이라면 전체 메모리에 영향을 줄 수 있어요. 다만 커서 하나당 메모리 점유는 작기 때문에 3000에서 4000으로 올리는 수준은 대부분 문제 없습니다.

**근본 원인 은폐**
이게 더 중요한 포인트입니다. ORA-01000의 진짜 원인이 **커서 누수**라면 값을 올리는 건 시간을 버는 것에 불과합니다. 4000으로 올려도 커서를 명시적으로 닫지 않는 코드가 있다면 결국 4000에서도 같은 에러가 납니다.

커서 누수 여부는 V$SESSTAT로 추가 확인할 수 있습니다.

```sql
-- 세션별 커서 오픈/클로즈 통계
SELECT s.username, s.sid,
       n.name, st.value
FROM v$sesstat st
JOIN v$statname n ON n.statistic# = st.statistic#
JOIN v$session s ON s.sid = st.sid
WHERE n.name IN ('opened cursors cumulative', 'opened cursors current')
  AND s.username IS NOT NULL
ORDER BY s.sid, n.name;
```

`opened cursors current` 값이 지속적으로 우상향한다면 누수를 의심해야 합니다.

## 정리

| 항목 | 내용 |
|------|------|
| 변경 위험도 | 낮음 (Dynamic 파라미터, 재시작 불필요) |
| 즉시 적용 | 가능 (`SCOPE=BOTH`) |
| 메모리 영향 | 미미한 수준 (3000→4000) |
| 주의사항 | 커서 누수 여부 병행 점검 필수 |

결국 OPEN_CURSORS 증가 자체는 안전하고 간단한 작업입니다. 다만 "값을 올렸으니 해결됐다"고 넘어가지 말고, 실제 사용량 확인 → 누수 세션 점검 → 증가 적용 → 모니터링 순서로 진행하는 게 맞습니다.

ORA-01000이 실제로 발생했다면 애플리케이션 팀과 함께 커서를 닫지 않는 코드가 있는지 반드시 같이 봐야 해요. DB 파라미터 조정은 임시방편이 될 수 있습니다.

추천 해시태그: #Oracle #OPEN_CURSORS #ORA-01000 #오라클DBA #커서튜닝 #오라클성능 #데이터베이스
