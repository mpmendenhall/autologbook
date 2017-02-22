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

//////////////////////////////
//////////////////////////////

/// Simple block data transfer protocol: int32_t bsize, data[bsize]
class BlockHandler: public ConnHandler {
public:
    /// Constructor
    BlockHandler(int sfd): ConnHandler(sfd) { }
    /// Receive block size and whole of expected data
    void handle() override;

    /// received data block with recipient identifier
    struct dblock {
        BlockHandler* H;    ///< pointer back to this handler
        vector<char> data;  ///< data location
    };

protected:
    /// Read block data of expected size
    virtual void read_block(int32_t bsize);
    /// Set theblock to write point, or null if unavailable
    virtual void request_block(int32_t /*bsize*/) { if(!theblock) theblock = new dblock; }
    /// Return completed block to whence it came
    virtual void return_block() { }

    /// Allocate block buffer space
    virtual char* alloc_block(int32_t bsize);
    /// Process data after buffer read; return false to end communication
    virtual bool process(int32_t bsize);

    dblock* theblock = nullptr; ///< default buffer space
};

//////////////////////////////
//////////////////////////////

#include "ThreadDataSerializer.hh"
class SockBlockSerializerServer;

/// Block protocol handler for serializer server
class SockBlockSerializerHandler: public BlockHandler {
public:
    /// Constructor
    SockBlockSerializerHandler(int sfd, SockBlockSerializerServer* SBS): BlockHandler(sfd), myServer(SBS) { }
protected:
    /// Set theblock to write point, or null if unavailable
    void request_block(int32_t /*bsize*/) override;
    /// Return completed block to whence it came
    void return_block() override;

    SockBlockSerializerServer* myServer;    ///< server handling serialization
};

/// Block data serializer server
class SockBlockSerializerServer: public ThreadedSockIOServer,
public ThreadDataSerializer<BlockHandler::dblock> {
protected:
    /// Generate handler that returns data to this
    ConnHandler* makeHandler(int sfd) override { return new SockBlockSerializerHandler(sfd, this); }
};

#endif
