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

    def read(self, SIO):
        i2c = busio.I2C(board.SCL, board.SDA, frequency=100000) # freq slower for pm25
        sensor = AS726x_I2C(i2c)
        sensor.integration_time = 50
        sensor. start_measurement()
        self.t = time.time()
        while not sensor.data_ready: time.sleep(0.1)

        r,o,y,g,b,v = sensor.red, sensor.orange, sensor.yellow, sensor.green, sensor.blue, sensor.violet
        self.spectrum = (r,o,y,g,b,v)
        self.T = sensor.temperature

        print("\nAS726x spectrum (uW/cm^2), at", self.T, "deg. C:")
        print(" * R", r)
        print(" * O", o)
        print(" * Y", y)
        print(" * G", g)
        print(" * B", b)
        print(" * V", v)

        SIO.log_readout(self.R_id, r, self.t)
        SIO.log_readout(self.O_id, o, self.t)
        SIO.log_readout(self.Y_id, y, self.t)
        SIO.log_readout(self.G_id, g, self.t)
        SIO.log_readout(self.B_id, b, self.t)
        SIO.log_readout(self.V_id, v, self.t)
        SIO.log_readout(self.T_id, self.T, self.t)
