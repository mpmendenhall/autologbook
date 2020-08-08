# assure correct shell is used
SHELL = /bin/sh

# apply implicit rules only for listed file types
.SUFFIXES:
.SUFFIXES: .c .cc .cpp .o

# compiler command to use
CXXFLAGS = -std=c++11 -O3 -fPIC -pedantic -Wall -Wextra -I. -Isqlite-amalgamation -lpthread -ldl
CFLAGS = -O3 -DSQLITE_ENABLE_RBU

VPATH = sqlite-amalgamation:LogMessenger
execs = sqlite_apply_RBU
objs = sqlite3.o
all: $(objs) $(execs)

# generic rule for everything else .cc
% : %.cc sqlite3.o
	$(CXX) $< sqlite3.o $(CXXFLAGS) -o $@

.PHONY: clean
clean:
	-rm -f *.o *.a *.so $(execs)
