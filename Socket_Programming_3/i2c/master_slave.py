"""
Question 15: I2C Master and Slave Communication
-----------------------------------------------------
Simulates I2C protocol elements: Start Condition, 7-bit Slave Address +
R/W bit, ACK/NACK, Data Transfer, Stop Condition. One Master can talk to
multiple Slave devices identified by unique addresses.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class I2CSlave:
    """Base I2C slave: responds to any addressed transaction with ACK and
    optionally returns data bytes for a read."""

    def __init__(self, address: int, name: str = ""):
        self.address = address
        self.name = name or f"Slave@0x{address:02X}"
        self.received_log: List[bytes] = []

    def on_write(self, data: bytes) -> bool:
        """Called when Master writes to this slave. Return True to ACK."""
        self.received_log.append(bytes(data))
        return True

    def on_read(self, num_bytes: int) -> bytes:
        """Called when Master reads from this slave. Return num_bytes of data."""
        return bytes([0xFF] * num_bytes)


@dataclass
class I2CTransactionLog:
    start_condition: bool = False
    address: int = 0
    rw_bit: int = 0            # 0 = write, 1 = read
    address_acked: bool = False
    data_bytes: List[int] = field(default_factory=list)
    data_acks: List[bool] = field(default_factory=list)
    stop_condition: bool = False

    def summary(self) -> str:
        rw = "READ" if self.rw_bit else "WRITE"
        return (f"START -> ADDR=0x{self.address:02X} {rw} "
                f"{'ACK' if self.address_acked else 'NACK'} -> "
                f"DATA={[hex(b) for b in self.data_bytes]} "
                f"ACKs={self.data_acks} -> STOP")


class I2CBus:
    """Manages address-based routing among multiple slaves sharing SDA/SCL."""

    def __init__(self):
        self.slaves: Dict[int, I2CSlave] = {}

    def attach(self, slave: I2CSlave):
        if slave.address in self.slaves:
            raise ValueError(f"Address 0x{slave.address:02X} already in use on the bus")
        self.slaves[slave.address] = slave

    def find(self, address: int) -> Optional[I2CSlave]:
        return self.slaves.get(address)


class I2CMaster:
    def __init__(self, bus: I2CBus):
        self.bus = bus

    def write(self, address: int, data: bytes) -> I2CTransactionLog:
        """Sends the full data buffer as one I2C write transaction (Start ..
        Address .. all data bytes .. Stop). The slave receives the whole
        buffer together, as it would over real SDA/SCL within one transaction,
        so multi-byte protocols (e.g. [register, value]) parse correctly."""
        log = I2CTransactionLog(start_condition=True, address=address, rw_bit=0)
        slave = self.bus.find(address)
        log.address_acked = slave is not None
        if slave:
            acked = slave.on_write(data)
            log.data_bytes = list(data)
            log.data_acks = [acked] * len(data)
        log.stop_condition = True
        return log

    def read(self, address: int, num_bytes: int) -> I2CTransactionLog:
        log = I2CTransactionLog(start_condition=True, address=address, rw_bit=1)
        slave = self.bus.find(address)
        log.address_acked = slave is not None
        if slave:
            data = slave.on_read(num_bytes)
            log.data_bytes = list(data)
            log.data_acks = [True] * len(data)   # master ACKs each byte except the last (NACK) in real I2C
            if log.data_acks:
                log.data_acks[-1] = False  # last byte NACK'd by master to end the read
        log.stop_condition = True
        return log


if __name__ == "__main__":
    bus = I2CBus()
    bus.attach(I2CSlave(0x50, "EEPROM"))
    bus.attach(I2CSlave(0x48, "TempSensor"))

    master = I2CMaster(bus)

    print("-- Write to EEPROM (0x50) --")
    log = master.write(0x50, b"\x01\x02\x03")
    print(log.summary())

    print("\n-- Read from TempSensor (0x48) --")
    log = master.read(0x48, 2)
    print(log.summary())

    print("\n-- Write to unknown address (0x7F) - should NACK --")
    log = master.write(0x7F, b"\xAA")
    print(log.summary())
