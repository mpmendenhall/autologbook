/// \file LogMessengerSocketed.hh LogMessenger talking to (remote) socket server

#ifndef LOGMESSENGERSOCKETED_HH
#define LOGMESSENGERSOCKETED_HH

#include "LogMessenger.hh"
#include "LocklessCircleBuffer.hh"
#include "SockConnection.hh"

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>

/// LogMessenger passing data to socket connection
class LogMessengerSocketed: public LogMessenger, public SockConnection {
public:
    /// Constructor
    LogMessengerSocketed() { }

    /// request types in socket communication
    enum request_type {
        REQ_ORIGIN = 1, ///< origin ID
        REQ_VAR_ID = 2, ///< variable ID request
        ADD_DATAPT = 3, ///< add datapoint
        ADD_MESSAGE= 4, ///< add log message
        SET_STATUS = 5  ///< notify of current status
    };

    /// set origin identifier
    void set_origin(const string& name, const string& descrip) override {
        if(!sockfd) return;
        send(REQ_ORIGIN);
        send(name);
        send(descrip);
        sockread((char*)&origin_id, sizeof(origin_id));
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
        sockread((char*)&dpid, sizeof(dpid));
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
    /// send scalar
    template<class T>
    void send(const T& r) { sockwrite((const char*)&r, sizeof(r), true); }
    /// send (length, string)
    void send(const string& s) {
        auto l = s.size();
        send(l);
        sockwrite(s.c_str(), l, true);
    }
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
    MessengerBuffer(const string& _host = "", int _port = 0): LocklessCircleBuffer(1000) {
        if(_host.size() && _port) connect_to_socket(_host, _port);
    }

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
