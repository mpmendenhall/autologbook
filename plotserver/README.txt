Web monitoring tools for autologbook
Michael P. Mendenhall (2016)

launch server in this directory:
export PYTHONPATH=${APP_DIR}/autologbook/:$PYTHONPATH
python3 -m http.server --cgi 8001 --bind 127.0.0.1

TODO
handle ; in descrip
handle --- in object value
fix relative link edit-link path


Metaform object structure:

== basic object structure ==

We may schematically represent two base classes A and B by:

A
    x
        z = 15
        t = "foobar"
    y = 9
    
B
    u = 12
        q = 999
    v

== display directives ==

Special variables "!xml" and "!list" modify how a (sub)object
    is rendered to xml output.

!xml = "tag" results in the ordinary contents being wrapped by <tag> ... contents ... </tag>.
Tag attributes can be specified by !xml.#attr = "foo" for <tag attr="foo"> .

!list indicates an object where only variables named starting with "#"
    will be displayed, sorted by the order of names.
If !list = "tag", each item variable will be wrapped in xml <tag> </tag>;
    otherwise, if !list = None, the items will be "glommed together" in sequence
    (separated by their own XML tags, when existing, or merged as text).

== wildcard variables ==

Variable names ending in "*" are treated as "wildcard" variables.
These over-write values of matching-named variables in the object tree with their own,
    e.g. x*.y = "foo" alongside variables x and x2 would set x.y = "foo" and x2.y = "foo".

== links ==

A node may be a link to another node.
Links may either be absolute, specified like "@A.x.z",
    or relative, specified like "@~2.m.n"
    where the leading "~2" will be expanded by
    the path two levels above where the reference is encountered.

A linked node's (this) value is replaced by the (this) value of the linked node,
    and sub-nodes of the linked node are inherited,
    and over-written by any identical paths in the linking node.
Chains of links to links are permitted, with inheritance/overwriting occurring at each step,
    and the (this) of the initial link node becoming (this) of the non-linking node ending the chain.
Cyclical links will be caught during evaluation,
    which stops further evaluation of a link chain at that point.

    
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

!list                   None
!xml                    tr
#*.!xml                 td
#1_name                 None
#1_name.!xml.#class     neutral
#2_value.!list          None
#2_value.#1             @obj:formfield
#2_value.#1.!xml.#size  10
#3_unit                 None
#4_min                  None
#5_max                  None
#6_comments.!list       None
#6_comments.#1          @obj:formfield

obj:checkline_tblheader header row for checklines table

!list           None
!xml            tr
!xml.#class     tblhead
#*.!xml         td
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

obj:fieldset    form fieldset wrapper object (fill in #0 with legend text; #1...#n with contents)

!list           None
!xml            fieldset
#0.!xml         legend

obj:form        Metaform form outline

!xml            form
!xml.#action    /cgi-bin/Metaform.py
!list           None
#~              @obj:submitbutton


----------------
forms:ctable_???        embed checklines in a table object, then edit their parameters:

!list   None
!xml    table
#1      @obj:checkline
#2      @obj:checkline
#3      @obj:checkline
...




--------------- TO DO ----------------
multi-plot graphs
PMT I,V plots
saved-state sessions
messages display: last n OR time interval
