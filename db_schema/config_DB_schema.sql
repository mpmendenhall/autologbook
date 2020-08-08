-- Experiment configuration parameters sqlite3 database setup
-- sqlite3 <db name> < config_DB_description.txt

-- identifiers for groups of parameters used together
CREATE TABLE config_set (
    name TEXT,                  -- identifying name
    family TEXT,                -- type of configuration (e.g. PMT HV)
    descrip TEXT,               -- human-readable text description
    time REAL                   -- creation timestamp
);
CREATE UNIQUE INDEX idx_config_set ON config_set(name, family);

-- configuration values
CREATE TABLE config_values (
    csid INTEGER,               -- set to which this belongs (config_set rowid)
    name TEXT,                  -- parameter name
    value REAL                  -- parameter value
);
CREATE UNIQUE INDEX idx_config_values ON config_values(csid, name);

-- history of when configurations were applied
CREATE TABLE config_history (
    csid INTEGER,               -- configuration identifier
    time REAL                   -- time applied
);
CREATE INDEX idx_config_history ON config_history(time);
