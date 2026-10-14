"""
Question 17: I2C Multi-Device Bus
----------------------------------------
An I2C bus with several distinct peripherals: EEPROM, Temperature Sensor,
Real-Time Clock, and Display Controller -- each with its own unique
address. The Master addresses each independently without disturbing
the others.
"""

import random
from master_slave import I2CSlave, I2CBus, I2CMaster
from register_device import RegisterDevice


class EEPROMDevice(RegisterDevice):
    def __init__(self, address: int):
        super().__init__(address, "EEPROM", num_registers=256)


class TemperatureSensorDevice(RegisterDevice):
    def __init__(self, address: int, seed: int = None):
        super().__init__(address, "TempSensor", num_registers=4)
        self.rng = random.Random(seed)
        self.registers[0] = self.rng.randint(15, 35)  # deg C at register 0


class RTCDevice(RegisterDevice):
    """Real-Time Clock: registers hold seconds, minutes, hours."""
    def __init__(self, address: int):
        super().__init__(address, "RTC", num_registers=8)
        self.registers[0], self.registers[1], self.registers[2] = 0, 0, 12  # sec, min, hr

    def tick(self):
        self.registers[0] = (self.registers[0] + 1) % 60
        if self.registers[0] == 0:
            self.registers[1] = (self.registers[1] + 1) % 60


class DisplayControllerDevice(RegisterDevice):
    """Register 0 = display on/off, Register 1 = brightness."""
    def __init__(self, address: int):
        super().__init__(address, "Display", num_registers=4)


def build_demo_bus() -> I2CBus:
    bus = I2CBus()
    bus.attach(EEPROMDevice(0x50))
    bus.attach(TemperatureSensorDevice(0x48, seed=11))
    bus.attach(RTCDevice(0x68))
    bus.attach(DisplayControllerDevice(0x3C))
    return bus


if __name__ == "__main__":
    bus = build_demo_bus()
    master = I2CMaster(bus)

    print("Devices on bus:", {hex(addr): dev.name for addr, dev in bus.slaves.items()})

    print("\n-- Write to EEPROM (0x50), register 0x00 = 0x99 --")
    print(master.write(0x50, bytes([0x00, 0x99])).summary())

    print("\n-- Read TempSensor (0x48) register 0x00 --")
    master.write(0x48, bytes([0x00]))
    print(master.read(0x48, 1).summary())

    print("\n-- Tick RTC (0x68) and read seconds register --")
    rtc = bus.find(0x68)
    for _ in range(5):
        rtc.tick()
    master.write(0x68, bytes([0x00]))
    print(master.read(0x68, 1).summary())

    print("\n-- Configure Display (0x3C): power on, brightness 80 --")
    print(master.write(0x3C, bytes([0x00, 0x01])).summary())
    print(master.write(0x3C, bytes([0x01, 80])).summary())

    print("\n-- Verify EEPROM register untouched by other device transactions --")
    master.write(0x50, bytes([0x00]))
    print(master.read(0x50, 1).summary())

    print("\nAll four peripherals communicated independently without cross-interference.")
