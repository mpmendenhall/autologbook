-- Simple chat messages database
-- sqlite3 <db name> < chat_DB_schema.sql

-- text chat log messages
CREATE TABLE messages (
    time REAL,          -- message timestamp
    src TEXT,           -- source of message (connection IP address)
    name TEXT,          -- name of sender
    msg TEXT,           -- message text
    state INTEGER       -- state flags: 0 = hidden, 1 = display, ...
);
CREATE INDEX idx_messages ON messages(time, state, src);
