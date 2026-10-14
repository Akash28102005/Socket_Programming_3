"""
Question 11: SPI Multi-Slave Communication
------------------------------------------------
One Master, multiple Slaves (EEPROM, Temperature Sensor, ADC), each with
its own Chip Select line. Only the selected slave participates; all
others remain inactive (their MISO output is ignored/high-Z).
"""

import random
from master_slave import SPISlave


class TemperatureSensorSlave(SPISlave):
    """Reports a simulated temperature reading (1 byte, degrees C) on each transfer."""

    def __init__(self, name: str, seed: int = None):
        super().__init__(name)
        self.rng = random.Random(seed)

    def transfer_bit(self, mosi_bit, bit_index_in_byte, byte_index):
        if not self.selected:
            return 1
        if bit_index_in_byte == 0:
            self._current_temp_byte = self.rng.randint(15, 35)  # deg C
        miso_bit = (self._current_temp_byte >> (7 - bit_index_in_byte)) & 1
        return miso_bit


class ADCSlave(SPISlave):
    """Returns a simulated 8-bit ADC conversion result."""

    def __init__(self, name: str, seed: int = None):
        super().__init__(name)
        self.rng = random.Random(seed)

    def transfer_bit(self, mosi_bit, bit_index_in_byte, byte_index):
        if not self.selected:
            return 1
        if bit_index_in_byte == 0:
            self._current_sample = self.rng.randint(0, 255)
        miso_bit = (self._current_sample >> (7 - bit_index_in_byte)) & 1
        return miso_bit


class SPIBus:
    """Manages Chip-Select routing across multiple slave devices."""

    def __init__(self):
        self.devices = {}   # name -> slave instance

    def attach(self, name: str, slave):
        self.devices[name] = slave

    def select_only(self, name: str):
        """Assert CS for exactly one device; deassert (deselect) all others."""
        if name not in self.devices:
            raise ValueError(f"No device named {name!r} on the bus")
        for dev_name, dev in self.devices.items():
            dev.select(dev_name == name)

    def transfer(self, master, name: str, data_out: bytes) -> bytes:
        self.select_only(name)
        result = master.transfer(self.devices[name], data_out)
        # after transfer, master.transfer() itself deselects; ensure bus-level consistency
        for dev in self.devices.values():
            if dev is not self.devices[name]:
                assert dev.selected is False
        return result


if __name__ == "__main__":
    from master_slave import SPIMaster

    bus = SPIBus()
    bus.attach("EEPROM", SPISlave("EEPROM", response_bytes=b"\x11\x22\x33"))
    bus.attach("TEMP_SENSOR", TemperatureSensorSlave("TEMP_SENSOR", seed=1))
    bus.attach("ADC", ADCSlave("ADC", seed=2))

    master = SPIMaster()

    print("Communicating with EEPROM (others must stay inactive):")
    resp = bus.transfer(master, "EEPROM", b"\x00\x00\x00")
    print(f"  EEPROM response: {list(resp)}")
    print(f"  TEMP_SENSOR selected? {bus.devices['TEMP_SENSOR'].selected} (must be False)")
    print(f"  ADC selected?         {bus.devices['ADC'].selected} (must be False)")

    print("\nCommunicating with TEMP_SENSOR:")
    resp = bus.transfer(master, "TEMP_SENSOR", b"\x00")
    print(f"  Temperature reading: {resp[0]} deg C")

    print("\nCommunicating with ADC:")
    resp = bus.transfer(master, "ADC", b"\x00")
    print(f"  ADC sample: {resp[0]}")

    print("\nAll transfers completed with correct Chip-Select isolation.")
