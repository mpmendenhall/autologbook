Web monitoring tools for autologbook
Michael P. Mendenhall (2016)

launch server in this directory:
export PYTHONPATH=${APP_DIR}/autologbook/:$PYTHONPATH
../HTTPServer.py --port 8005

    
== Recipes for useful objects ==

obj:formfield       self-referencing form input field
# creates its own "value" entry

!xml                    input
!xml.#name.!list        None
!xml.#name.#1           new_
!xml.#name.#2           @$3.value
!xml.#type              text
!xml.#value             @~2.value

obj:checkline       table row for a checklist entry

!list                   td
!xml                    tr
#1_name None
#1_name.!xml            div
#1_name.!xml.#class     neutral
#2_value                @obj:formfield
#2_value.!xml.#size     10.0
#3_unit                 None
#4_min                  None
#5_max                  None
#6_comments             @obj:formfield
#6_comments.!xml.#size  50.0

obj:checkline_tblheader header row for checklines table

!list           td
!xml            tr
!xml.#class     tblhead
#1              Name
#2              Value
#3              Units
#4              min.
#5              max.
#6              Comments

obj:submitbutton    form submit button

!xml    input
!xml.#name      update
!xml.#type      submit
!xml.#value     Submit

obj:fieldset    form fieldset wrapper object (fill in #0 with legend text, #1...#n with contents)

!list           None
!xml            fieldset
#0.!xml         legend

obj:form        Form outline, with submit button and hidden return-to-page-view

!list           None
!xml            form
!xml.#action    /cgi-bin/Metaform.py
!xml.#method    post
#~              @obj:submitbutton
#~1.!xml        input
#~1.!xml.#name  view
#~1.!xml.#type  hidden
#~1.!xml.#value @$3


----------------
forms:ctable_???        embed checklines in a table object, then edit their parameters:

!list   None
!xml    table
#1      @obj:checkline
#2      @obj:checkline
#3      @obj:checkline
...


== quirks ==

Semicolons are not handled correctly in form values; they, and everything following, are truncated.
This appears to be a python3(.4.3) cgi.FieldStorage bug.


--------------- TO DO ----------------
fix relative link edit-link path
multi-plot graphs
PMT I,V plots
saved-state sessions
messages display: last n OR time interval
