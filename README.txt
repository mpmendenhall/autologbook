autologbook lab logging utility suite
Michael P. Mendenhall (2016--2020)

a collection of Python scripts for generating and managing sqlite3 database log files of lab "slow control" readings
See doc/AutologbookManual.pdf for overview documentation.



--------------------------------------
--------------- TO DO ----------------

unified name lookup cache interface

Reference IDs by name in cgi query

Parse, link nested path ID names

auto-detect I2C attached sensors

calc modules available in plot builder, status display

revive data reduction filters
controlled/clean XMLRPC logger shutdown
static page generators; on-demand updates; fully-remote view

certificate generation, distribution for remotes
revive c++/"hardwired" local net TCP socket interface


------------------------------
fix display of 0 in tree form
fix relative link edit-link path

== quirks ==

Semicolons are not handled correctly in form values; they, and everything following, are truncated.
This appears to be a python3(.4.3) cgi.FieldStorage bug.
