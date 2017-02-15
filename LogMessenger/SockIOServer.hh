/// \file SockIOServer.hh I/O server for multiple socket connections

#ifndef SOCKIOSERVER_HH
#define SOCKIOSERVER_HH

#include <netdb.h> // for sockaddr_in, hostent
#include <string>
using std::string;
#include <vector>
using std::vector;

/// Base class listening and handling connections to port
class SockIOServer {
public:
    /// Constructor
    SockIOServer() { }
    /// Destructor
    virtual ~SockIOServer() { }

    /// receive and process connections to host and port
    bool process_connections(const string& host, int port);

protected:
    /// handle each new connection --- subclass me!
    virtual void handle_connection(int csockfd);
};

/// Base class for handling one accepted connection
class ConnHandler {
public:
    /// Constructor
    ConnHandler(int sfd): sockfd(sfd) { }
    /// Destructor
    virtual ~ConnHandler() { }
    /// Communicate with accepted connection
    virtual void handle();

    int sockfd; ///< accepted connection file descriptor
};

/// Socket server spawning threads for each connection
class ThreadedSockIOServer: public SockIOServer {

protected:
    /// create correct handler type
    virtual ConnHandler* makeHandler(int sfd) { return new ConnHandler(sfd); }
    /// handle each new connection
    void handle_connection(int csockfd) override;
};


#endif
