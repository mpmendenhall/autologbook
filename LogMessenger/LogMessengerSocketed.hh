/// \file LogMessengerSocketed.hh LogMessenger talking to (remote) socket server

#ifndef LOGMESSENGERSOCKETED_HH
#define LOGMESSENGERSOCKETED_HH

#include "LogMessenger.hh"

#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h> 

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>

#include <string.h>

/// LogMessenger passing data to socket connection
class LogMessengerSocketed: public LogMessenger {
public:
    /// Constructor
    LogMessengerSocketed() { }
    /// Destructor
    ~LogMessengerSocketed() { close_socket(); }
    
    /// (try to) open socket connection
    bool open_socket(const string& host, int port) {
        sockfd = socket(AF_INET, SOCK_STREAM, 0);
        if (sockfd < 0) {
            fprintf(stderr, "ERROR opening socket\n");
            return false;
        }
        
        server = gethostbyname(host.c_str());
        if(server == nullptr) {
            fprintf(stderr, "ERROR: Host '%s' not found!\n",host.c_str());
            close_socket();
            return false;
        }
        
        bzero((char*) &serv_addr, sizeof(serv_addr));
        serv_addr.sin_family = AF_INET;
        bcopy((char*)server->h_addr, (char*)&serv_addr.sin_addr.s_addr, server->h_length);
        serv_addr.sin_port = htons(port);
        if(connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
            fprintf(stderr, "ERROR connecting to socket %s:%i\n", host.c_str(), port);
            close_socket();
            return false;
        }
        
        return true;
    }
    
    /// request types in socket communication
    enum request_type {
        REQ_ORIGIN = 1, ///< origin ID
        REQ_VAR_ID = 2, ///< variable ID request
        ADD_DATAPT = 3, ///< add datapoint
        ADD_MESSAGE= 4  ///< add log message
    };
    
    /// close socket
    void close_socket() { close(sockfd); sockfd = 0; }
    
    /// set origin identifier
    void set_origin(const string& name) override {
        send(REQ_ORIGIN);
        send(name);
        read(sockfd, &origin_id, sizeof(origin_id));
        printf("Set origin ID to %zu\n", origin_id);
    }
    
    /// get datapoint identifier
    int64_t get_datapoint_id(const string& name) override {
        send(REQ_VAR_ID);
        send(name);
        int64_t dpid;
        read(sockfd, &dpid, sizeof(dpid));
        return dpid;
    }
    
    /// add datapoint to log
    void add_datapoint(int64_t id, double val, double ts = 0) override {
        if(auto_timestamp && !ts) ts = time(nullptr);
        send(ADD_DATAPT);
        send(id);
        send(val);
        send(ts);
    }
    
    /// add message to log
    void add_message(const string& m, double ts = 0) override {
        if(auto_timestamp && !ts) ts = time(nullptr);
        send(ADD_MESSAGE);
        send(m);
    }

protected:
    /// send request type
    void send(const request_type& r) { write(sockfd, &r, sizeof(r)); }
    /// send double
    void send(const double& d) { write(sockfd, &d, sizeof(d)); }
    /// send int64_t
    void send(const int64_t& i) { write(sockfd, &i, sizeof(i)); }
    /// send (length, string) over connection
    void send(const string& s) { 
        auto l = s.size();
        write(sockfd, &l, sizeof(l));
        write(sockfd, s.c_str(), l);
    }
    
    int sockfd = 0;                         ///< file descriptor number for socket
    struct sockaddr_in serv_addr;
    struct hostent* server = nullptr;       ///< server
};

#endif
