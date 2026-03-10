---
title: "[Oracle] SQL 코드블록 스타일 테스트"
tags: Oracle,테스트,스타일,DBA
category: DB 기술
visibility: 0
---

요약: SQL 코드블록 기본 텍스트 색상(#ffffff) 및 키워드/함수/주석 하이라이팅이 정상 적용되는지 확인하는 테스트 글입니다.

## 테스트 목적

`_sql_block_to_div` 적용 후 일반 텍스트(컬럼명, 테이블명, 별칭)는 흰색, 키워드는 파란색, 함수는 주황색, 주석은 회색으로 표시되는지 확인합니다.

## 샘플 쿼리

```sql
-- 세션별 열린 커서 수 (주석은 회색)
SELECT s.username, s.sid, s.serial#,
       COUNT(c.cursor#) AS open_cursors
FROM v$open_cursor c
JOIN v$session s ON s.saddr = c.saddr
WHERE s.username IS NOT NULL
GROUP BY s.username, s.sid, s.serial#
ORDER BY open_cursors DESC;
```

위 블록에서 `username`, `sid`, `open_cursors`, `c`, `s` 등은 기본색(#ffffff), `SELECT`, `FROM`, `WHERE` 등은 키워드 색, `COUNT`는 함수 색으로 나와야 합니다.

추천 해시태그: #Oracle #DBA #테스트 #스타일
