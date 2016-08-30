/// \file logsoctest.cc Demonstration use of buffered socket connection to log database server
#include "LogMessengerSocketed.hh"
#include <cassert>

/*
# compile:
g++ -std=c++11 -DWITH_MPMUTILS -I$MPMUTILS/GeneralUtils/ logsoctest.cc -lpthread -o logsoctest

# run after starting database server:

# initialize a test database:
cd ..
sqlite3 test.db < logger_DB_schema.sql
# launch socket server:
./LogMessengerSocketServer.py --db test.db --port 9999
*/

int main(int, char**) {
    // set up data and message queues with independent I/O threads
    DataptBuffer DPB("localhost",9999);
    int rc = DPB.launch_mythread();
    assert(rc == 0);
    MessageBuffer MB("localhost",9999);
    rc = MB.launch_mythread();
    assert(rc == 0);
    
    // set "origin identifier" for program, same for data and message queues
    DPB.set_origin("logsoctest","test of sockets connection to logging DB");
    MB.origin_id = DPB.origin_id;
    auto datid = DPB.get_datapoint_id("testdata", "hey, it's data", "arbitrary");
    
    // do "uninterrupted" work while sending messages, datapoints
    MB.send_message("Start of logging test.");
    for(int i=0; i<10; i++) {
        DPB.send_datapoint(datid, i);
        usleep(500000);
    }
    MB.send_message("End of logging test.");
    
    // wait for I/O queues to clear
    rc = DPB.finish_mythread();
    assert(rc == 0);
    rc = MB.finish_mythread();
    assert(rc == 0);
    
    return EXIT_SUCCESS;
}
