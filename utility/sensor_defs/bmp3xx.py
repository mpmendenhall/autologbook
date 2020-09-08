import time
import board
import busio
import adafruit_bmp3xx
from . import SensorItem
import traceback

class BMP3xxMonitor(SensorItem):
    def h2P(h): return 1013.25 * (1 - 2.25577e-5 * h)**5.25588
    def P2h(P): return (1 - (P/1013.25)**(1./5.25588))/2.25577e-5

    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)

        self.g_id = DBL.create_readout("BMP388",   "BMP388 pressure/temperature sensor", None)
        self.T_id = DBL.create_readout("BMP388/T", "ambient temperature", "deg. C")
        self.P_id = DBL.create_readout("BMP388/P", "ambient pressure", "mbar")
        self.P = self.T = self.t = None
        self.bmp3xx = None

    def read(self, SIO):
        if not self.bmp3xx:
            i2c = busio.I2C(board.SCL, board.SDA, frequency=100000) # freq slower for pm25
            self.bmp3xx = adafruit_bmp3xx.BMP3XX_I2C(i2c)
            self.bmp3xx.pressure_oversampling = 32
            self.bmp3xx.temperature_oversampling = 2
        try:
            self.T = self.bmp3xx.temperature
            self.P = self.bmp3xx.pressure
        except:
            traceback.print_exc()
            self.bmp3xx = None
            return

        self.t = time.time()
        print("BMP3xx", self.t, self.T, "C,\t", self.P, "mbar")

        SIO.log_readout(self.T_id, self.T, self.t)
        SIO.log_readout(self.P_id, self.P, self.t)
