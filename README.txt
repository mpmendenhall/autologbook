autologbook lab logging utility suite
Michael P. Mendenhall (2016)

a collection of Python scripts for generating and managing sqlite3 database log files of lab "slow control" readings
INCOMPLETE WORK IN PROGRESS
See doc/AutologbookManual.pdf for overview documentation.



--------------------------------------
--------------- TO DO ----------------
fix relative link edit-link path
multi-plot graphs
PMT I,V plots
saved-state sessions
messages display: last n OR time interval

== quirks ==

Semicolons are not handled correctly in form values; they, and everything following, are truncated.
This appears to be a python3(.4.3) cgi.FieldStorage bug.
