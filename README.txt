autologbook lab logging utility suite
Michael P. Mendenhall (2016)

a collection of Python scripts for generating and managing sqlite3 database log files of lab "slow control" readings
INCOMPLETE WORK IN PROGRESS : MANY COMPONENTS MISSING

DB_Logger:
    - 3 components in separate threads:
        - read-only xmlrpc server interface (probably localhost only, accessed via cgi script views)
        - read/write xmlrpc interface (restrict to localhost) for communication with data collection scripts; duplicates data to RBU
        - in-memory recent data cache shared between interfaces

    - TODO checks for "actionable" conditions (out-of-range values, etc.)
    - TODO manages rollover/archiving of logbook DB files

FakeHVControl.py,TestFunctionGen.py: test data generators talking to RB_Logger

plotserver utilities:
    - cgi scripts run through Python cgi server
    - stateless views of DB_Logger data
    - TODO state-cacheing advanced plotting sessions
    
--------------- TO DO ----------------

general configuration file
alarm/range configuration files
finish RBU setup, including instruments/readings in RBU

DB_Server:
    - pulls RBU data over network as (slightly delayed, higher-traffic-volume) proxy for DB_Logger
    - provides data access to cgi plotters

Locator:
    - interface for locating and collecting archived data for analysis tasks
