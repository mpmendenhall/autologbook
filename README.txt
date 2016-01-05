autologbook lab logging utility suite
Michael P. Mendenhall (2016)

a collection of Python scripts for generating and managing sqlite3 database log files of lab "slow control" readings
INCOMPLETE WORK IN PROGRESS
MANY COMPONENTS MISSING

DB_Logger:
    - reads in datapoints from devices
    - writes to logbook DB file, copied to differential changes RBU files
    - checks for "actionable" conditions (out-of-range values, etc.)
    - manages rollover/archiving of logbook DB files

DB_Server:
    - pulls RBU data over network for "reasonably up-to-date" response
    - handles data I/O from multiple files
    - in-memory cache of recent data points
    - generate webpage summary tables, plots

Locator:
    - interface for locating and collecting archived data for analysis tasks
    - another place to put trigger actions
