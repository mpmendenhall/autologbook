import time
from . import SensorItem
import adafruit_pcf8523
import _bleio
import adafruit_ble
from adafruit_ble.advertising.standard import Advertisement
from adafruit_ble.services.standard.device_info import DeviceInfoService
from adafruit_ble_berrymed_pulse_oximeter import BerryMedPulseOximeterService

# PyLint can't find BLERadio for some reason so special case it here.
ble = adafruit_ble.BLERadio()  # pylint: disable=no-member

class PulseOxMonitor(SensorItem):

    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)

        self.g_id = DBL.create_readout("BM1000", "BM1000 finger pulse oximeter", None)
        self.SpO2_id = DBL.create_readout("BM1000/SpO2", "BM1000", "Oxygen saturation pressure", "%")
        self.rate_id = DBL.create_readout("BM1000/heartrate", "BM1000", "heart beat rate", "bpm")
        #self.pleth_id = DBL.create_readout("BM1000/pleth", "BM1000", "blood flow", "")

        self.scan_for_device()

    def scan_for_device(self):
        self.poxconn = None
        for adv in ble.start_scan(Advertisement, timeout=5):
            name = adv.complete_name
            if not name: continue
            if name.strip("\x00") == "BerryMed":
                self.poxconn = ble.connect(adv)
                break
        ble.stop_scan()

        if self.poxconn and self.poxconn.connected:
            self.poxserv = pulse_ox_connection[BerryMedPulseOximeterService]
        else:
            self.poxconn = self.poxserv = None

    def read(self, SIO):
        if not self.poxconn: self.scan_for_device()
        if not self.poxconn: return

        try:
            self.t = time.time()
            values = self.poxserv.values
            if values is not None:
                valid, spo2, pulse_rate, pleth, finger = values
                if (not valid) or pulse_rate == 255: return

                SIO.log_readout(self.SpO2_id, spo2, self.t)
                SIO.log_readout(self.rate_id, pulse_rate, self.t)
                #SIO.log_readout(self.pleth_id, pleth, self.t)

        except _bleio.ConnectionError:
            try: self.poxconn.disconnect()
            except _bleio.ConnectionError: pass
            self.poxconn = None
