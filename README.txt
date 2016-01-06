autologbook lab logging utility suite
Michael P. Mendenhall (2016)

a collection of Python scripts for generating and managing sqlite3 database log files of lab "slow control" readings
INCOMPLETE WORK IN PROGRESS : MANY COMPONENTS MISSING

DB_Logger:
    - reads in datapoints from devices
    - writes to logbook DB file, copied to differential changes RBU files
    - checks for "actionable" conditions (out-of-range values, etc.)
    - manages rollover/archiving of logbook DB files

plotserver utilities:
    - cgi scripts run through simple Python cgi server
    - stateless versions pull data each time
    - TODO state-cacheing advanced plotting sessions
    
--------------- TO DO ----------------

DB_Logger log messages interface
general configuration file
alarm/range configuration files
DB_Logger sockets write interface for c++/fast-DAQ integration

DB_Server:
    - pulls RBU data over network as (slightly delayed, higher-traffic-volume) proxy for DB_Logger
    - provides data access to cgi plotters

Locator:
    - interface for locating and collecting archived data for analysis tasks
