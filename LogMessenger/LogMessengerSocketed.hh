/// \file LogMessengerSocketed.hh LogMessenger talking to (remote) socket server

#ifndef LOGMESSENGERSOCKETED_HH
#define LOGMESSENGERSOCKETED_HH

#include "LogMessenger.hh"
#include "LocklessCircleBuffer.hh"

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
        ADD_MESSAGE= 4, ///< add log message
        SET_STATUS = 5  ///< notify of current status
    };

    /// close socket
    void close_socket() { close(sockfd); sockfd = 0; }

    /// set origin identifier
    void set_origin(const string& name, const string& descrip) override {
        if(!sockfd) return;
        send(REQ_ORIGIN);
        send(name);
        send(descrip);
        ioret = read(sockfd, &origin_id, sizeof(origin_id));
    }

    /// get datapoint identifier
    int64_t get_datapoint_id(const string& name, const string& descrip, const string& unit) override {
        if(!sockfd) return 0;
        send(REQ_VAR_ID);
        send(origin_id);
        send(name);
        send(descrip);
        send(unit);
        int64_t dpid;
        ioret = read(sockfd, &dpid, sizeof(dpid));
        return dpid;
    }

    /// add datapoint to log
    void _add_datapoint(int64_t id, double val, double ts = 0) override {
        if(!sockfd) return;
        if(auto_timestamp && !ts) ts = time(nullptr);
        send(ADD_DATAPT);
        send(id);
        send(val);
        send(ts);
    }

    /// add message to log
    void _add_message(const string& m, double ts = 0) override {
        if(auto_timestamp && !ts) ts = time(nullptr);
        if(message_stdout) { printf("[%.0f] %s\n", ts, m.c_str()); fflush(stdout); }
        if(!sockfd) return;
        send(ADD_MESSAGE);
        send(origin_id);
        send(m);
        send(ts);
    }

    /// send status notification
    void set_status(int64_t s) override {
        if(!sockfd) return;
        send(SET_STATUS);
        send(origin_id);
        send(s);
    }

    bool message_stdout = false;  ///< whether to print added messages to stdout

protected:
    /// send request type
    void send(const request_type& r) { ioret = write(sockfd, &r, sizeof(r)); }
    /// send double
    void send(const double& d) { ioret = write(sockfd, &d, sizeof(d)); }
    /// send int64_t
    void send(const int64_t& i) { ioret = write(sockfd, &i, sizeof(i)); }
    /// send (length, string) over connection
    void send(const string& s) {
        auto l = s.size();
        ioret = write(sockfd, &l, sizeof(l));
        ioret = write(sockfd, s.c_str(), l);
    }

    int sockfd = 0;                         ///< file descriptor number for socket
    int ioret = 0;                          ///< return code from IO operation
    struct sockaddr_in serv_addr;
    struct hostent* server = nullptr;       ///< server
};

/// Bufferable request for IO task
class LogMessengerIOTask {
public:
    /// Constructor
    LogMessengerIOTask(double v = 0, double t = 0, int64_t id = 0, int64_t s = 0, const string& m = ""):
    val(v), ts(t), datid(id), status(s), msg(m) { }

    double val;         ///< datapoint value
    double ts;          ///< timestampstamp
    int64_t datid;      ///< datapoint ID
    int64_t status;     ///< status number
    string msg;         ///< log message text
};

/// Buffered connection for datapoints, moving I/O delays to separate thread
class MessengerBuffer: public LocklessCircleBuffer<LogMessengerIOTask>, public LogMessengerSocketed {
public:
    /// Constructor
    MessengerBuffer(const string& host = "", int port = 0): LocklessCircleBuffer(1000) { if(host.size() && port) open_socket(host,port); }

    /// forward datapoint to database
    void process_item() override {
        if(current.msg.size()) _add_message(current.msg, current.ts);
        if(current.status) set_status(current.status);
        if(current.datid) _add_datapoint(current.datid, current.val, current.ts);
    }
    /// add datapoint to queue
    void send_datapoint(int64_t id, double val, double ts = 0) { push_buffer(LogMessengerIOTask(val,ts,id)); }
    /// add message to queue (optional combined with status)
    void send_message(const string& m, double ts = 0, int64_t s = 0) { push_buffer(LogMessengerIOTask(0,ts,0,s,m)); }
    /// add status to queue
    void send_status(int64_t s) { push_buffer(LogMessengerIOTask(0,0,0,s)); }
};

#endif
