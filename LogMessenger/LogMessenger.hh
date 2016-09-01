/// \file LogMessenger.hh Interface for passing log messages to (remote) database

#ifndef LOGMESSENGER_HH
#define LOGMESSENGER_HH

#include <cstdint>
#include <string>
using std::string;

/// Base class for logging interface front-end
class LogMessenger {
public:
    /// Constructor
    LogMessenger() { }
    /// Destructor
    virtual ~LogMessenger() { }
    
    bool auto_timestamp = true;    ///< whether to fill in timestamps with current time
    
    /// struct describing datapoint
    struct datapoint {
        datapoint() { }
        datapoint(int64_t i, double v, double t=0): id(i), val(v), ts(t) { }
        int64_t id;
        double val;
        double ts;
    };
    /// struct describing message
    struct message {
        message() { }
        message(const string& m, double t=0): msg(m), ts(t) { }
        string msg;
        double ts;
    };
    
    /// set origin identifier
    virtual void set_origin(const string& name, const string& descrip) = 0;
    /// get datapoint identifier
    virtual int64_t get_datapoint_id(const string& name, const string& descrip, const string& unit) = 0;
    /// add datapoint to log
    virtual void _add_datapoint(int64_t id, double val, double ts = 0) = 0;
    /// add datapoint to log
    void add_datapoint(const datapoint& p) { _add_datapoint(p.id,p.val,p.ts); }
    /// add message to log
    virtual void _add_message(const string& m, double ts = 0) = 0;
    /// add message to log
    void add_message(const message& m) { _add_message(m.msg, m.ts); }
    /// send status notification
    virtual void set_status(int64_t s) = 0;
    
    int64_t origin_id = 0;          ///< identifier for message originating process
};

#endif
