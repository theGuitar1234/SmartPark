CREATE TABLE IF NOT EXISTS app_user (
  user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name      TEXT NOT NULL,
  email          TEXT NOT NULL UNIQUE,
  password_hash  TEXT NOT NULL,
  created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE parking_lot (
  lot_id        INTEGER PRIMARY KEY AUTOINCREMENT,
  name          VARCHAR(120) NOT NULL,
  address       VARCHAR(255),
  city          VARCHAR(80),
  created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE parking_zone (
  zone_id       BIGSERIAL PRIMARY KEY,
  lot_id        BIGINT NOT NULL REFERENCES parking_lot(lot_id) ON DELETE CASCADE,
  name          VARCHAR(80) NOT NULL,
  floor_level   INTEGER,
  created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE (lot_id, name)
);

CREATE TABLE parking_slot (
  slot_id       BIGSERIAL PRIMARY KEY,
  zone_id       BIGINT NOT NULL REFERENCES parking_zone(zone_id) ON DELETE CASCADE,
  slot_code     VARCHAR(30) NOT NULL,
  slot_type     VARCHAR(30) NOT NULL DEFAULT 'STANDARD',
  status        VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE',
  x_pos         NUMERIC(10,2),
  y_pos         NUMERIC(10,2),
  created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE (zone_id, slot_code),
  CHECK (status IN ('AVAILABLE','RESERVED','OCCUPIED','OUT_OF_SERVICE'))
);

CREATE TABLE sensor (
  sensor_id     BIGSERIAL PRIMARY KEY,
  slot_id       BIGINT UNIQUE REFERENCES parking_slot(slot_id) ON DELETE SET NULL,
  sensor_code   VARCHAR(60) NOT NULL UNIQUE,
  sensor_type   VARCHAR(40) NOT NULL DEFAULT 'ULTRASONIC',
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  installed_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE gate (
  gate_id       BIGSERIAL PRIMARY KEY,
  lot_id        BIGINT NOT NULL REFERENCES parking_lot(lot_id) ON DELETE CASCADE,
  gate_type     VARCHAR(10) NOT NULL,
  name          VARCHAR(60) NOT NULL,
  CHECK (gate_type IN ('ENTRY','EXIT'))
);

CREATE TABLE sensor_reading (
  reading_id    BIGSERIAL PRIMARY KEY,
  sensor_id     BIGINT NOT NULL REFERENCES sensor(sensor_id) ON DELETE CASCADE,
  reading_time  TIMESTAMP NOT NULL DEFAULT NOW(),
  occupied      BOOLEAN NOT NULL,
  confidence    NUMERIC(5,2),
  UNIQUE(sensor_id, reading_time)
);

CREATE TABLE vehicle (
  vehicle_id      BIGSERIAL PRIMARY KEY,
  plate_number    VARCHAR(20) NOT NULL UNIQUE,
  vehicle_type    VARCHAR(20) NOT NULL DEFAULT 'CAR',
  owner_name      VARCHAR(120),
  created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE tariff_plan (
  tariff_id       BIGSERIAL PRIMARY KEY,
  lot_id          BIGINT NOT NULL REFERENCES parking_lot(lot_id) ON DELETE CASCADE,
  name            VARCHAR(80) NOT NULL,
  currency        VARCHAR(10) NOT NULL DEFAULT 'AZN',
  grace_minutes   INTEGER NOT NULL DEFAULT 0,
  hourly_rate     NUMERIC(10,2) NOT NULL,
  daily_max       NUMERIC(10,2),
  active          BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE (lot_id, name)
);

CREATE TABLE parking_session (
  session_id      BIGSERIAL PRIMARY KEY,
  vehicle_id      BIGINT NOT NULL REFERENCES vehicle(vehicle_id) ON DELETE RESTRICT,
  slot_id         BIGINT REFERENCES parking_slot(slot_id) ON DELETE SET NULL,
  tariff_id       BIGINT NOT NULL REFERENCES tariff_plan(tariff_id) ON DELETE RESTRICT,
  entry_gate_id   BIGINT REFERENCES gate(gate_id) ON DELETE SET NULL,
  exit_gate_id    BIGINT REFERENCES gate(gate_id) ON DELETE SET NULL,
  entry_time      TIMESTAMP NOT NULL DEFAULT NOW(),
  exit_time       TIMESTAMP,
  status          VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  fee_amount      NUMERIC(10,2),
  CHECK (status IN ('ACTIVE','CLOSED','CANCELLED'))
);

CREATE UNIQUE INDEX uq_vehicle_active_session
ON parking_session(vehicle_id)
WHERE status = 'ACTIVE';

CREATE TABLE payment (
  payment_id      BIGSERIAL PRIMARY KEY,
  session_id      BIGINT NOT NULL UNIQUE REFERENCES parking_session(session_id) ON DELETE CASCADE,
  paid_amount     NUMERIC(10,2) NOT NULL,
  paid_at         TIMESTAMP NOT NULL DEFAULT NOW(),
  method          VARCHAR(20) NOT NULL,
  provider_ref    VARCHAR(120),
  status          VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
  CHECK (method IN ('CASH','CARD','APP')),
  CHECK (status IN ('SUCCESS','FAILED','PENDING'))
);

CREATE INDEX idx_slot_status ON parking_slot(status);
CREATE INDEX idx_session_entry_time ON parking_session(entry_time);
CREATE INDEX idx_session_slot ON parking_session(slot_id);