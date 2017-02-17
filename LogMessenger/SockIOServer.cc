/// \file SockIOServer.cc

#include "SockIOServer.hh"
#include <string.h> // for bzero(...)
#include <unistd.h> // for write(...), usleep(n)
#include <stdio.h>  // for printf(...)
#include <sys/ioctl.h> // for ioctl(...)
#include <pthread.h>
#include <cassert>

bool SockIOServer::process_connections(const string& host, int port) {
    // open socket file descriptor
    auto sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        fprintf(stderr, "ERROR %i opening socket\n", sockfd);
        return false;
    }

    // bind server to socket
    struct sockaddr_in serv_addr;
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons(port); // host to network byte order
    int rc = bind(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr));
    if(rc < 0) {
        fprintf(stderr, "ERROR %i binding socket\n", rc);
        close(sockfd);
        return false;
    }
    // listen on socket for connections, allowing a backlog of 10
    listen(sockfd, 10);
    printf("Listening for connections on port %i (socket fd %i)\n", port, sockfd);

    // block until new socket created for connection
    while(1) {
        struct sockaddr cli_addr;
        socklen_t clilen = sizeof(cli_addr); // returns actual size of client address
        auto newsockfd = accept(sockfd, &cli_addr, &clilen);
        if (newsockfd < 0) {
            fprintf(stderr, "ERROR %i accepting socket connection!\n", newsockfd);
            continue;
        }
        handle_connection(newsockfd);
    }

    close(sockfd);
    return true;
}

void SockIOServer::handle_connection(int csockfd) {
    printf("Accepting new connection %i ... and closing it.\n", csockfd);
    close(csockfd);
}

////////////////////
////////////////////
////////////////////

void ConnHandler::handle() {
    printf("Echoing responses from socket fd %i...\n", sockfd);
    int ntries = 0;
    while(ntries++ < 100) {
        int len = 0;
        ioctl(sockfd, FIONREAD, &len);
        if(len > 0) {
            vector<char> buff(len);
            len = read(sockfd, buff.data(), len);
            printf("%i[%i]> '", sockfd, len);
            for(auto c: buff) printf("%c",c);
            printf("'\n");
            ntries = 0;
        } else usleep(100000);
    }
    printf("Closing responder to handle %i.\n", sockfd);
}

void BlockHandler::handle() {
    int32_t bsize;
    while(1) {
        // TODO ioctl to check for disconnection
        bsize = 0;
        int len = read(sockfd, &bsize, sizeof(bsize));
        if(!len) { usleep(100000); continue; }
        assert(len==sizeof(bsize));

        if(bsize > 0) read_block(bsize);
        if(!process(bsize)) break;
    }
}

void BlockHandler::read_block(int32_t bsize) {
    auto buff = alloc_block(bsize);
    int len = read(sockfd, buff, bsize);
    assert(len == bsize);
}

bool BlockHandler::process(int32_t bsize) {
    if(!bsize) return false;
    printf("%i[%i:%i]> '", sockfd, bsize, (int)dbuff.size());
    assert(bsize < 0 || bsize == (int32_t)dbuff.size());
    if(bsize > 0) for(auto c: dbuff) printf("%c",c);
    printf("'\n");
    dbuff.clear();
    return bsize > 0;
}

////////////////////
////////////////////
////////////////////

void* run_sockio_thread(void* p) {
    auto h = (ConnHandler*)p;
    h->handle();
    close(h->sockfd);
    delete h;
    return nullptr;
}

void ThreadedSockIOServer::handle_connection(int csockfd) {
    pthread_t mythread;
    pthread_create(&mythread, nullptr, // thread attributes
                   run_sockio_thread, makeHandler(csockfd));
}

////////////////////
////////////////////
////////////////////

#ifdef SOCKET_TEST

class TestIOServer: public ThreadedSockIOServer {
protected:
    ConnHandler* makeHandler(int sfd) override { return new BlockHandler(sfd); }
};

int main(int, char **) {
    TestIOServer SIS;
    SIS.process_connections("localhost",9999);
}

#endif
