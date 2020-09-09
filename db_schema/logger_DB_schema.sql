-- Lab "slow control" logging system sqlite3 database setup
-- sqlite3 <db name> < logger_DB_schema.sql

-- readout types
CREATE TABLE readout_types (
    readout_id INTEGER PRIMARY KEY, -- primary key for item identification
    name TEXT,                      -- readout name
    descrip TEXT,                   -- longer description
    units TEXT                      -- units
);
CREATE UNIQUE INDEX idx_readout_types ON readout_types(name);

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
    readout_id INTEGER,     -- source of message from readout_types
    time REAL,              -- message timestamp
    msg TEXT,               -- message text
    FOREIGN KEY(readout_id) REFERENCES readout_types(readout_id) ON DELETE SET NULL
);
CREATE INDEX idx_textlog_time ON textlog(time);
CREATE INDEX idx_textlog_readid ON textlog(readout_id, time);
