/// \file sqlite_apply_RBU.cc \brief Apply "" to sqlite3 file
// This file was produced under the employ of the United States Government,
// and is consequently in the PUBLIC DOMAIN, free from all provisions of
// US Copyright Law (per USC Title 17, Section 105).
//
// -- Michael P. Mendenhall, 2015

#include <stdlib.h>
#include <stdio.h>
#include "sqlite3.h"
#include "sqlite3rbu.h"

int main(int argc, char** argv) {
    if(argc != 3 && argc != 4) return EXIT_FAILURE;

                    //              target   RBU      state
    sqlite3rbu* p = sqlite3rbu_open(argv[1], argv[2], argc==4? argv[3] : NULL);

    int ret;
    while((ret = sqlite3rbu_step(p)) == SQLITE_OK) { }

    if(ret != SQLITE_DONE) printf("Error %i in applying RBU!\n", ret);
    char* msg = NULL;
    sqlite3rbu_close(p, &msg);
    if(msg) printf("Error message: '%s'\n", msg); 

    return EXIT_SUCCESS;
}
