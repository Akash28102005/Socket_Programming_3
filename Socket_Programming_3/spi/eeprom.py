"""
Question 10: SPI Memory Device Simulation
----------------------------------------------
Simulates a 256-byte SPI EEPROM with commands: Read, Write, Erase,
Read Status Register, and Device Reset. The Master issues commands;
the EEPROM keeps its 256-byte memory array consistent across operations.
"""

from enum import IntEnum


class EEPROMCommand(IntEnum):
    READ = 0x03
    WRITE = 0x02
    ERASE = 0x06
    RDSR = 0x05    # Read Status Register
    RESET = 0x99


class StatusRegister:
    def __init__(self):
        self.write_in_progress = False
        self.write_enabled = True

    def as_byte(self) -> int:
        byte = 0
        if self.write_in_progress:
            byte |= 0b0000_0001
        if self.write_enabled:
            byte |= 0b0000_0010
        return byte


class SPIEEPROM:
    SIZE = 256

    def __init__(self):
        self.memory = bytearray(self.SIZE)
        self.status = StatusRegister()

    def handle_command(self, command: EEPROMCommand, address: int = 0, data: bytes = b"") -> dict:
        if command == EEPROMCommand.READ:
            return self._read(address, len(data) or 1)
        elif command == EEPROMCommand.WRITE:
            return self._write(address, data)
        elif command == EEPROMCommand.ERASE:
            return self._erase()
        elif command == EEPROMCommand.RDSR:
            return {"status_register": self.status.as_byte()}
        elif command == EEPROMCommand.RESET:
            return self._reset()
        else:
            return {"error": f"Unknown command 0x{command:02X}"}

    def _validate_address(self, address: int, length: int = 1):
        if address < 0 or address + length > self.SIZE:
            raise ValueError(f"Address 0x{address:02X} (len={length}) out of range for {self.SIZE}-byte EEPROM")

    def _read(self, address: int, length: int) -> dict:
        self._validate_address(address, length)
        data = bytes(self.memory[address:address + length])
        return {"read_data": data, "address": address}

    def _write(self, address: int, data: bytes) -> dict:
        self._validate_address(address, len(data))
        self.status.write_in_progress = True
        self.memory[address:address + len(data)] = data
        self.status.write_in_progress = False
        return {"written": len(data), "address": address}

    def _erase(self) -> dict:
        self.memory = bytearray(self.SIZE)
        return {"erased_bytes": self.SIZE}

    def _reset(self) -> dict:
        self.status = StatusRegister()
        return {"reset": True}


if __name__ == "__main__":
    eeprom = SPIEEPROM()

    print("-- Write 'HELLO' at address 0x10 --")
    print(eeprom.handle_command(EEPROMCommand.WRITE, address=0x10, data=b"HELLO"))

    print("\n-- Read 5 bytes from address 0x10 --")
    result = eeprom.handle_command(EEPROMCommand.READ, address=0x10, data=b"\x00" * 5)
    print(result, "->", result["read_data"].decode())

    print("\n-- Read Status Register --")
    print(eeprom.handle_command(EEPROMCommand.RDSR))

    print("\n-- Write again at 0x20, then verify memory consistency across both writes --")
    eeprom.handle_command(EEPROMCommand.WRITE, address=0x20, data=b"WORLD")
    r1 = eeprom.handle_command(EEPROMCommand.READ, address=0x10, data=b"\x00" * 5)
    r2 = eeprom.handle_command(EEPROMCommand.READ, address=0x20, data=b"\x00" * 5)
    print(f"0x10 -> {r1['read_data'].decode()}, 0x20 -> {r2['read_data'].decode()}")

    print("\n-- Erase entire chip --")
    print(eeprom.handle_command(EEPROMCommand.ERASE))
    r3 = eeprom.handle_command(EEPROMCommand.READ, address=0x10, data=b"\x00" * 5)
    print(f"0x10 after erase -> {list(r3['read_data'])}")

    print("\n-- Device Reset --")
    print(eeprom.handle_command(EEPROMCommand.RESET))
