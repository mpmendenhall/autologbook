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

////////////////////
////////////////////
////////////////////

void BlockHandler::handle() {
    int32_t bsize;
    while(1) {
        // TODO ioctl to check for disconnection
        bsize = 0;
        int len = read(sockfd, &bsize, sizeof(bsize));
        if(!len) { usleep(1000); continue; }
        assert(len==sizeof(bsize));

        if(bsize > 0) read_block(bsize);
        if(!process(bsize)) break;
    }
}

void BlockHandler::read_block(int32_t bsize) {
    auto buff = alloc_block(bsize);
    if(!buff) return;
    int32_t nread = 0;
    while(nread < bsize) {
        auto len = read(sockfd, buff+nread, bsize-nread);
        if(len < 0) break;
        nread += len;
        if(nread != bsize) usleep(1000);
    }
}

bool BlockHandler::process(int32_t bsize) {
    if(!bsize || !theblock) return false;
    static size_t received = 0;
    static int nprocessed = 0;
    nprocessed++;
    received += bsize;

    if(nprocessed<100 || !(nprocessed % int(nprocessed/100))) {
        printf("%i[%i:%i]> '", sockfd, bsize, (int)theblock->data.size());
        assert(bsize < 0 || bsize == (int32_t)theblock->data.size());
        if(bsize > 0 && bsize < 1024) for(auto c: theblock->data) printf("%c",c);
        else printf("%.1f MB", received/(1024*1024.));
        printf("'\n");
    }
    return_block();
    return bsize > 0;
}

char* BlockHandler::alloc_block(int32_t bsize) {
    request_block(bsize);
    if(!theblock) return nullptr;
    theblock->H = this;
    theblock->data.resize(bsize);
    return theblock->data.data();
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

void SockBlockSerializerHandler::request_block(int32_t /*bsize*/) { theblock = myServer->get_allocated(); }
void SockBlockSerializerHandler::return_block() { if(theblock) myServer->return_allocated(theblock); }


#ifdef SOCKET_TEST
// make SockIOServer -j4; ./SockIOServer
class TestIOServer: public ThreadedSockIOServer {
protected:
    ConnHandler* makeHandler(int sfd) override { return new BlockHandler(sfd); }
};

int main(int, char **) {
    SockBlockSerializerServer SBS;
    SBS.launch_mythread();
    SBS.process_connections("localhost",9999);
}
#endif
