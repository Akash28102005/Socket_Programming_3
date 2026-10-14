"""
Question 16: I2C Register-Based Device
--------------------------------------------
An I2C slave that maintains a register map. Master performs register
Read/Write using [device address][register address][data]. Demonstrates
reading a simulated sensor register and writing a configuration register.
"""

import random
from master_slave import I2CSlave, I2CBus, I2CMaster


class RegisterDevice(I2CSlave):
    """
    Write protocol:  Master writes [register_addr, value] -> sets register.
    Read protocol:   Master first writes [register_addr] to set a pointer,
                      then issues a read to receive that register's value(s).
    """

    def __init__(self, address: int, name: str, num_registers: int = 16):
        super().__init__(address, name)
        self.registers = bytearray(num_registers)
        self._pointer = 0

    def on_write(self, data: bytes) -> bool:
        self.received_log.append(bytes(data))
        if len(data) == 1:
            # Set register pointer for a subsequent read
            reg = data[0]
            if reg >= len(self.registers):
                return False
            self._pointer = reg
            return True
        elif len(data) >= 2:
            reg, value = data[0], data[1]
            if reg >= len(self.registers):
                return False
            self.registers[reg] = value
            self._pointer = reg
            return True
        return False

    def on_read(self, num_bytes: int) -> bytes:
        result = bytearray()
        ptr = self._pointer
        for _ in range(num_bytes):
            if ptr < len(self.registers):
                result.append(self.registers[ptr])
            else:
                result.append(0x00)
            ptr += 1
        return bytes(result)

    def simulate_sensor_update(self, register: int, rng: random.Random):
        """Simulate a live sensor value changing a register (e.g. temperature)."""
        self.registers[register] = rng.randint(0, 255)


if __name__ == "__main__":
    bus = I2CBus()
    sensor = RegisterDevice(0x40, "SensorDevice", num_registers=8)
    bus.attach(sensor)
    master = I2CMaster(bus)

    rng = random.Random(3)
    # Register 0x00 = TEMP_MSB (sensor value), Register 0x01 = CONFIG
    sensor.simulate_sensor_update(0x00, rng)
    print(f"Sensor's internal register 0x00 (simulated live reading) = {sensor.registers[0]}")

    print("\n-- Master reads sensor register 0x00 --")
    master.write(0x40, bytes([0x00]))            # set pointer to register 0
    log = master.read(0x40, 1)
    print(f"Read value: {log.data_bytes[0]}  (matches sensor register: "
          f"{log.data_bytes[0] == sensor.registers[0]})")

    print("\n-- Master writes configuration register 0x01 = 0x55 --")
    log = master.write(0x40, bytes([0x01, 0x55]))
    print(log.summary())
    print(f"Register map after write: {list(sensor.registers)}")
