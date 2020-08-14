import time
import board
import busio
import adafruit_bmp3xx

class BMP3xxMonitor:
    def h2P(h): return 1013.25 * (1 - 2.25577e-5 * h)**5.25588
    def P2h(P): return (1 - (P/1013.25)**(1./5.25588))/2.25577e-5

    def __init__(self, DBL):
        self.g_id = DBL.create_readgroup("BMP388", "BMP388 pressure/temperature sensor")
        self.T_id = DBL.create_readout("T", "BMP388", "ambient temperature", "deg. C")
        self.P_id = DBL.create_readout("P", "BMP388", "ambient pressure", "mbar")
        self.P = self.T = self.t = None
        self.i2c = None

    def read(self, SIO):
        bmp3xx = adafruit_bmp3xx.BMP3XX_I2C(SIO.i2c)
        bmp3xx.pressure_oversampling = 32
        bmp3xx.temperature_oversampling = 32
        self.T = bmp3xx.temperature
        self.P = bmp3xx.pressure
        self.t = time.time()
        print("BMP3xx", self.t, self.T, "C,\t", self.P, "mbar")

        SIO.log_readout(self.T_id, self.T, self.t)
        SIO.log_readout(self.P_id, self.P, self.t)
