-- Lab "slow control" logging system sqlite3 database setup
-- sqlite3 <db name> < logger_DB_schema.sql

-- generic configuration key:value pairs
CREATE TABLE config_kv (
    k TEXT,     -- name of parameter
    v BLOB      -- parameter value
);
CREATE UNIQUE INDEX idx_config_kv ON config_kv(k);

-- useful keys:
--
-- creation_time unix timestamp for initialization of DB
-- prev_name     filename of previous archived dataset
-- prev_hash     file hash of previous archived dataset

-- groupings of readouts (e.g. from one instrument)
CREATE TABLE readout_groups (
    readgroup_id INTEGER PRIMARY KEY,   -- primary key for item identification
    name TEXT,                      -- identifying (short) name
    descrip TEXT                    -- longer description
);
CREATE UNIQUE INDEX idx_readout_groups ON readout_groups(name);

-- readout types
CREATE TABLE readout_types (
    readout_id INTEGER PRIMARY KEY, -- primary key for item identification
    name TEXT,                      -- readout name
    descrip TEXT,                   -- longer description
    units TEXT,                     -- units
    readgroup_id INTEGER,           -- readgroup_id from readout_groups
    FOREIGN KEY(readgroup_id) REFERENCES readout_groups(readgroup_id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX idx_readout_types ON readout_types(readgroup_id, name);

-- a readout datapoint
CREATE TABLE readings (
    readout_id INTEGER, -- reading type, from readout_types
    time REAL,          -- reading timestamp
    value REAL,         -- reading value
    FOREIGN KEY(readout_id) REFERENCES readout_types(readout_id) ON DELETE CASCADE
);
CREATE INDEX idx_readings ON readings(readout_id, time);

-- text log messages
CREATE TABLE textlog (
    time REAL,              -- message timestamp
    readgroup_id INTEGER,   -- source of message from readout_groups
    msg TEXT,               -- message text
    FOREIGN KEY(readgroup_id) REFERENCES readout_groups(readgroup_id) ON DELETE SET NULL
);
CREATE INDEX idx_textlog ON textlog(time, readgroup_id);
CREATE INDEX idx_textlog_readgrp ON textlog(readgroup_id);
