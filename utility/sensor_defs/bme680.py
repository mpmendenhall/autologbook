import time
import board
import busio
import adafruit_bme680
from . import SensorItem
import traceback

class BME680Monitor(SensorItem):

    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)

        self.g_id   = DBL.create_readout("BME680",     "BME680 environmental sensor sensor", None)
        self.T_id   = DBL.create_readout("BME680/T",   "ambient temperature", "deg. C")
        self.P_id   = DBL.create_readout("BME680/P",   "ambient pressure", "mbar")
        self.RH_id  = DBL.create_readout("BME680/RH",  "relative humidity", "%")
        self.VOC_id = DBL.create_readout("BME680/VOC", "VOC sensor gas conductivity", "millimho")

        self.bme680 = None

    def read(self, SIO):
        if not self.bme680:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)
            self.bme680.temperature_oversample = 16
            self.bme680.pressure_oversample = 16
            self.bme680.humidity_oversampe = 16
        try:
            T   = self.bme680.temperature
            RH  = self.bme680.humidity
            P   = self.bme680.pressure
            VOC = 1000./self.bme680.gas
        except:
            traceback.print_exc()
            self.bme680 = None
            return

        self.t = time.time()
        print("BME680 at t =", self.t, ":\n\t",
              "%.3f C\n\t"%T,
              "%.3f mbar\n\t"%P,
              "%.2f %% humidity\n\t"%RH,
              "%.3g millimho VOC\n"%VOC)

        SIO.log_readout(self.T_id,   T,   self.t)
        SIO.log_readout(self.P_id,   P,   self.t)
        SIO.log_readout(self.RH_id,  RH,  self.t)
        SIO.log_readout(self.VOC_id, VOC, self.t)
