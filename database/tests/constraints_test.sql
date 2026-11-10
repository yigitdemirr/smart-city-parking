-- Design checks for M1: proves the database itself enforces the rules the
-- network scenarios rely on. Each block must end with the NOTICE shown.
\set ON_ERROR_STOP on

-- 1) First hold on space A-01, 10:00-12:00 -> accepted
BEGIN;
INSERT INTO operations VALUES ('aaaaaaaa-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-000000000002','HOLD_SPACE', repeat('a',64),
  'SUCCEEDED', 201, '{"status":"HELD"}', 'RESERVATION', NULL, now());
INSERT INTO reservations (user_id, space_id, operation_id, start_time, end_time,
                          hold_expires_at, price_per_hour_snapshot, total_amount)
SELECT '00000000-0000-0000-0000-000000000002', id, 'aaaaaaaa-0000-0000-0000-000000000001',
       '2026-12-01 10:00+01', '2026-12-01 12:00+01', now() + interval '10 minutes', 4.00, 8.00
FROM parking_spaces WHERE label = 'A-01';
COMMIT;
\echo 'OK 1: first hold accepted'

-- 2) Competing hold on the same space, overlapping period -> must fail
DO $$
BEGIN
  INSERT INTO operations VALUES ('aaaaaaaa-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000001','HOLD_SPACE', repeat('b',64),
    'SUCCEEDED', 201, '{}', 'RESERVATION', NULL, now());
  INSERT INTO reservations (user_id, space_id, operation_id, start_time, end_time,
                            hold_expires_at, price_per_hour_snapshot, total_amount)
  SELECT '00000000-0000-0000-0000-000000000001', id, 'aaaaaaaa-0000-0000-0000-000000000002',
         '2026-12-01 11:00+01', '2026-12-01 13:00+01', now() + interval '10 minutes', 4.00, 8.00
  FROM parking_spaces WHERE label = 'A-01';
  RAISE EXCEPTION 'FAIL 2: double booking was accepted';
EXCEPTION WHEN exclusion_violation THEN
  RAISE NOTICE 'OK 2: competing overlapping hold rejected (exclusion_violation)';
END $$;

-- 3) Retry with the SAME operation_id -> must not create a second operation
DO $$
BEGIN
  INSERT INTO operations VALUES ('aaaaaaaa-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000002','HOLD_SPACE', repeat('a',64),
    'SUCCEEDED', 201, '{}', 'RESERVATION', NULL, now());
  RAISE EXCEPTION 'FAIL 3: duplicate operation accepted';
EXCEPTION WHEN unique_violation THEN
  RAISE NOTICE 'OK 3: duplicate operation_id rejected (unique_violation) -> service replays stored response';
END $$;

-- 4) After the first hold expires, the same period can be held again
UPDATE reservations SET status = 'EXPIRED'
 WHERE operation_id = 'aaaaaaaa-0000-0000-0000-000000000001';
BEGIN;
INSERT INTO operations VALUES ('aaaaaaaa-0000-0000-0000-000000000003',
  '00000000-0000-0000-0000-000000000001','HOLD_SPACE', repeat('c',64),
  'SUCCEEDED', 201, '{}', 'RESERVATION', NULL, now());
INSERT INTO reservations (user_id, space_id, operation_id, start_time, end_time,
                          hold_expires_at, price_per_hour_snapshot, total_amount)
SELECT '00000000-0000-0000-0000-000000000001', id, 'aaaaaaaa-0000-0000-0000-000000000003',
       '2026-12-01 11:00+01', '2026-12-01 13:00+01', now() + interval '10 minutes', 4.00, 8.00
FROM parking_spaces WHERE label = 'A-01';
COMMIT;
\echo 'OK 4: expired hold released the space'

-- 5) Only one successful (simulated) payment per reservation
DO $$
DECLARE r UUID;
BEGIN
  SELECT id INTO r FROM reservations WHERE operation_id = 'aaaaaaaa-0000-0000-0000-000000000003';
  INSERT INTO operations VALUES ('bbbbbbbb-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001','PAY_RESERVATION', repeat('d',64),
    'SUCCEEDED', 200, '{}', 'PAYMENT', NULL, now());
  INSERT INTO payments (reservation_id, operation_id, amount, status)
    VALUES (r, 'bbbbbbbb-0000-0000-0000-000000000001', 8.00, 'SUCCEEDED');
  INSERT INTO operations VALUES ('bbbbbbbb-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000001','PAY_RESERVATION', repeat('e',64),
    'SUCCEEDED', 200, '{}', 'PAYMENT', NULL, now());
  INSERT INTO payments (reservation_id, operation_id, amount, status)
    VALUES (r, 'bbbbbbbb-0000-0000-0000-000000000002', 8.00, 'SUCCEEDED');
  RAISE EXCEPTION 'FAIL 5: second successful payment accepted';
EXCEPTION WHEN unique_violation THEN
  RAISE NOTICE 'OK 5: second successful payment rejected';
END $$;

-- 6) Payments can never be marked as real
DO $$
DECLARE r UUID;
BEGIN
  SELECT id INTO r FROM reservations WHERE operation_id = 'aaaaaaaa-0000-0000-0000-000000000003';
  INSERT INTO operations VALUES ('bbbbbbbb-0000-0000-0000-000000000003',
    '00000000-0000-0000-0000-000000000001','PAY_RESERVATION', repeat('f',64),
    'SUCCEEDED', 200, '{}', 'PAYMENT', NULL, now());
  INSERT INTO payments (reservation_id, operation_id, amount, status, is_simulated)
    VALUES (r, 'bbbbbbbb-0000-0000-0000-000000000003', 8.00, 'SUCCEEDED', FALSE);
  RAISE EXCEPTION 'FAIL 6: real payment accepted';
EXCEPTION WHEN check_violation THEN
  RAISE NOTICE 'OK 6: is_simulated is forced to TRUE';
END $$;
