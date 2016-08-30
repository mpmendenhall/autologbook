#include "LogMessengerSocketed.hh"
#include <unistd.h>

// g++ -std=c++11 logsoctest.cc -o logsoctest

int main(int, char**) {
    LogMessengerSocketed LMS;
    LMS.open_socket("localhost",9999);
    LMS.set_origin("logsoctest","test of sockets connection to logging DB");
    auto datid = LMS.get_datapoint_id("testdata", "hey, it's data", "arbitrary");
    
    LMS.add_message("Start of logging test.");
    for(int i=0; i<10; i++) {
        LMS.add_datapoint(datid, i);
        usleep(500000);
    }
    //usleep(30000000);
    LMS.add_message("End of logging test.");
    
    return EXIT_SUCCESS;
}
