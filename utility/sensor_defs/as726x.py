import time
import board
import busio
from adafruit_as726x import AS726x_I2C
from . import SensorItem

class AS726xMonitor(SensorItem):
    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)

        self.g_id = DBL.create_readgroup("AS726x", "AS726x multispectral light sensor")

        self.R_id = DBL.create_readout("R", "AS726x", "650+-40nm Red band",    "μW/cm^2")
        self.O_id = DBL.create_readout("O", "AS726x", "600+-40nm Orange band", "μW/cm^2")
        self.Y_id = DBL.create_readout("Y", "AS726x", "570+-40nm Yellow band", "μW/cm^2")
        self.G_id = DBL.create_readout("G", "AS726x", "550+-40nm Green band",  "μW/cm^2")
        self.B_id = DBL.create_readout("B", "AS726x", "500+-40nm Blue band",   "μW/cm^2")
        self.V_id = DBL.create_readout("V", "AS726x", "450+-40nm Violet band", "μW/cm^2")

        self.T_id = DBL.create_readout("T", "AS726x", "device temperature", "deg. C")
        self.T_integ = 50.

    def read(self, SIO):
        i2c = busio.I2C(board.SCL, board.SDA, frequency=100000) # freq slower for pm25
        sensor = AS726x_I2C(i2c)
        sensor.integration_time = self.T_integ
        sensor.gain = 64 # 1., 3.7, 16., 64.]
        sensor. start_measurement()
        self.t = time.time()
        while not sensor.data_ready: time.sleep(0.1)

        # "typical" 45 counts / uW/cm^2 at gain 16, 166 ms integration
        n = 16*166/(45. * self.T_integ * sensor.gain) # normalization
        r,o,y,g,b,v = sensor.red*n, sensor.orange*n, sensor.yellow*n, sensor.green*n, sensor.blue*n, sensor.violet*n

        self.spectrum = (r,o,y,g,b,v)
        self.T = sensor.temperature
        self.raw = (sensor.raw_red, sensor.raw_orange, sensor.raw_yellow, sensor.raw_green, sensor.raw_blue, sensor.raw_violet)

        print("\nAS726x spectrum (uW/cm^2) over", self.T_integ, "ms, at", self.T, "deg. C:")
        print(" * R", r, self.raw[0])
        print(" * O", o, self.raw[1])
        print(" * Y", y, self.raw[2])
        print(" * G", g, self.raw[3])
        print(" * B", b, self.raw[4])
        print(" * V", v, self.raw[5])

        SIO.log_readout(self.R_id, r, self.t)
        SIO.log_readout(self.O_id, o, self.t)
        SIO.log_readout(self.Y_id, y, self.t)
        SIO.log_readout(self.G_id, g, self.t)
        SIO.log_readout(self.B_id, b, self.t)
        SIO.log_readout(self.V_id, v, self.t)
        SIO.log_readout(self.T_id, self.T, self.t)

        # adjust for next readout
        rmax = max(self.raw)
        if rmax: self.T_integ = min(max((2**15)*self.T_integ/rmax, 3), 700)
        else: self.T_integ = 700
