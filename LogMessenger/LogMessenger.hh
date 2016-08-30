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
    
    /// set origin identifier
    virtual void set_origin(const string& name, const string& descrip) = 0;
    /// get datapoint identifier
    virtual int64_t get_datapoint_id(const string& name, const string& descrip, const string& unit) = 0;
    /// add datapoint to log
    virtual void add_datapoint(int64_t id, double val, double ts = 0) = 0;
    /// add message to log
    virtual void add_message(const string& m, double ts = 0) = 0;
    
protected:
    int64_t origin_id = 0;  ///< identifier for message originating process
};

#endif
