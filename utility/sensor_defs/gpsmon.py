import time
from gps import *
from . import SensorItem

class GPSMonitor(SensorItem):
    def __init__(self, DBL):
        SensorItem.__init__(self)

        self.g_id = DBL.create_readgroup("GPS", "Global Positioning System receiver")
        self.lat_id = DBL.create_readout("lat", "GPS", "Latitude", "degrees N")
        self.lon_id = DBL.create_readout("lon", "GPS", "Longitude", "degrees E")
        self.alt_id = DBL.create_readout("alt", "GPS", "Altitude", "m")
        self.lat = self.lon = self.alt = self.t = None

    def read(self, SIO):
        gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
        report = gpsd.next()
        retries = 6
        while report['class'] != 'TPV' and retries:
            #print(report['class'])
            report = gpsd.next()
            retries -= 1
        if report['class'] != 'TPV': return False

        tstr = getattr(report,'time',None)
        self.lat = getattr(report,'lat', None)
        self.lon = getattr(report,'lon', None)
        self.alt = getattr(report,'alt', None)
        self.t = time.time()
        print("GPS", self.t, tstr, self.lat, "N, ", self.lon, "E, ", self.alt, "m")

                #print  getattr(report,'epv','nan'),"\t",
            #print  getattr(report,'ept','nan'),"\t",
            #print  getattr(report,'speed','nan'),"\t",
            #print getattr(report,'climb','nan'),"\t"

        if self.lat is not None: SIO.log_readout(self.lat_id, self.lat, self.t)
        if self.lon is not None: SIO.log_readout(self.lon_id, self.lon, self.t)
        if self.alt is not None: SIO.log_readout(self.alt_id, self.alt, self.t)

