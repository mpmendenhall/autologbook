from . import SensorItem
import platform
import subprocess
import time

class CPUMonitor(SensorItem):
    """Local system load/health indicators"""
    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)

        self.hostname = platform.node()
        self.g_id = DBL.create_readgroup(self.hostname, "Computer '" + self.hostname + "' status")
        self.Tcpu_id = DBL.create_readout("Tcpu", self.hostname, "CPU temperature", "deg. C")
        self.Tgpu_id = DBL.create_readout("Tgpu", self.hostname, "GPU temperature", "deg. C")

        try:
            subprocess.check_output(["vcgencmd","measure_temp"])
            self.has_tgpu = True
        except:
            self.has_tgpu = False
            self.Tgpu = None

    def read(self, SIO):
        self.t = time.time()
        if self.has_tgpu: self.Tgpu = float(subprocess.check_output(["vcgencmd","measure_temp"]).decode()[5:9])
        self.Tcpu = float(open("/sys/class/thermal/thermal_zone0/temp",'r').read())/1000.
        print("\n", self.hostname, "Tcpu =", self.Tcpu, "C, Tgpu =", self.Tgpu, "C")

        SIO.log_readout(self.Tcpu_id,    self.Tcpu, self.t)
        if self.Tgpu is not None: SIO.log_readout(self.Tgpu_id, self.Tgpu, self.t)

"""
Reference ID    : C0A82B0A (pitorius0.lan)
Stratum         : 3
Ref time (UTC)  : Tue Aug 18 14:03:11 2020
System time     : 0.000224996 seconds slow of NTP time
Last offset     : -0.000230364 seconds
RMS offset      : 0.300154030 seconds
Frequency       : 4.141 ppm fast
Residual freq   : +12.910 ppm
Skew            : 0.280 ppm
Root delay      : 0.219955415 seconds
Root dispersion : 0.017975340 seconds
Update interval : 260.0 seconds
Leap status     : Normal
"""

class ChronyMonitor(SensorItem):
    """chronyc tracking monitor"""
    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)

        self.hostname = platform.node()
        self.g_id     = DBL.create_readgroup(self.hostname, "Computer '" + self.hostname + "' status")
        self.freq_id  = DBL.create_readout("clockfreq", self.hostname, "clock frequency offset", "ppm")
        self.resid_id = DBL.create_readout("clockresid", self.hostname, "residual frequency offset", "ppm")
        self.err_id   = DBL.create_readout("clockerr", self.hostname, "system clock error on update", "ms")

    def read(self, SIO):
        self.t = time.time()
        for l in subprocess.check_output(["chronyc","tracking"]).decode().split("\n"):
            l = l.split()
            if not l: continue
            if l[0] == "Frequency":
                self.freq = float(l[2])*(-1 if l[4] == "slow" else 1)
                SIO.log_readout(self.freq_id, self.freq, self.t)
            if l[0] == "Residual":
                SIO.log_readout(self.resid_id, float(l[3]), self.t)
            #if l[0] == "Ref":
            #    st = time.strptime(' '.join(l[-4:])+" UTC", "%b %d %H:%M:%S %Y %Z")
            #    self.tref = time.mktime(st) - time.timezone
            if l[0] == "Update":
                self.tnext = self.t + 0.5*float(l[3])
            if l[0] == "Last":
                SIO.log_readout(self.err_id, 1e3*float(l[3]), self.t)

        print("Clock frequency off by", self.freq, "ppm; next read at", time.ctime(self.tnext))
