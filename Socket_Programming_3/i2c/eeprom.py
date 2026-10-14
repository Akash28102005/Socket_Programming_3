"""
Question 19: I2C EEPROM Simulation
----------------------------------------
An I2C EEPROM supporting Sequential Read, Random Read, Byte Write,
Page Write, Memory Erase, and Memory Dump. Verifies data integrity
across write/read-back cycles.
"""

from master_slave import I2CSlave


class I2CEEPROM(I2CSlave):
    PAGE_SIZE = 8

    def __init__(self, address: int = 0x50, size: int = 256):
        super().__init__(address, "I2C-EEPROM")
        self.size = size
        self.memory = bytearray(size)
        self._pointer = 0

    # --- Low-level protocol handlers (address pointer + data) ---
    def on_write(self, data: bytes) -> bool:
        self.received_log.append(bytes(data))
        if len(data) == 1:
            self._pointer = data[0] % self.size   # set address pointer only (Random Read setup)
            return True
        return False   # use explicit methods below for writes in this simulation

    def on_read(self, num_bytes: int) -> bytes:
        return self.sequential_read(self._pointer, num_bytes)

    # --- High-level EEPROM operations ---
    def byte_write(self, address: int, value: int):
        self._validate(address)
        self.memory[address] = value & 0xFF

    def page_write(self, start_address: int, data: bytes):
        if len(data) > self.PAGE_SIZE:
            raise ValueError(f"Page write exceeds page size of {self.PAGE_SIZE} bytes")
        self._validate(start_address, len(data))
        self.memory[start_address:start_address + len(data)] = data

    def random_read(self, address: int) -> int:
        self._validate(address)
        self._pointer = address + 1
        return self.memory[address]

    def sequential_read(self, start_address: int, length: int) -> bytes:
        self._validate(start_address, length)
        result = bytes(self.memory[start_address:start_address + length])
        self._pointer = start_address + length
        return result

    def erase(self, address: int = None, length: int = None):
        if address is None:
            self.memory = bytearray(self.size)
        else:
            self._validate(address, length or 1)
            for i in range(length or 1):
                self.memory[address + i] = 0x00

    def memory_dump(self) -> bytes:
        return bytes(self.memory)

    def _validate(self, address: int, length: int = 1):
        if address < 0 or address + length > self.size:
            raise ValueError(f"Address 0x{address:02X} (len={length}) out of range")


if __name__ == "__main__":
    eeprom = I2CEEPROM()

    print("-- Byte Write: address 0x00 = 0x7A --")
    eeprom.byte_write(0x00, 0x7A)
    print(f"Random read back: 0x{eeprom.random_read(0x00):02X}")

    print("\n-- Page Write: 8 bytes starting at 0x10 --")
    page_data = bytes(range(0x10, 0x18))
    eeprom.page_write(0x10, page_data)
    print(f"Sequential read back: {list(eeprom.sequential_read(0x10, 8))}")

    print("\n-- Verify data integrity (written == read back) --")
    assert eeprom.random_read(0x00) == 0x7A
    assert eeprom.sequential_read(0x10, 8) == page_data
    print("Integrity check PASSED for both regions.")

    print("\n-- Erase a small region (0x00, 1 byte) --")
    eeprom.erase(address=0x00, length=1)
    print(f"0x00 after erase: 0x{eeprom.memory[0]:02X}")

    print("\n-- Memory Dump (first 32 bytes) --")
    print(list(eeprom.memory_dump()[:32]))
