"""
Question 20: I2C Protocol Analyzer
----------------------------------------
Software protocol analyzer that displays Start Condition, Slave Address,
ACK/NACK bits, Register Address, Data Bytes, Stop Condition, timestamps,
communication statistics, and protocol errors. Maintains a full log for
debugging/verification, exportable to CSV/JSON.
"""

import csv
import json
import time
from dataclasses import dataclass, asdict
from typing import List

from master_slave import I2CMaster, I2CBus, I2CTransactionLog


@dataclass
class I2CLogEntry:
    timestamp: str
    transaction_number: int
    start_condition: bool
    address_hex: str
    rw: str
    address_ack: str
    register_or_first_byte: str
    data_bytes_hex: str
    data_acks: str
    stop_condition: bool
    protocol_error: str


class I2CProtocolAnalyzer:
    def __init__(self):
        self.entries: List[I2CLogEntry] = []
        self.transaction_count = 0
        self.error_count = 0
        self.address_nack_count = 0

    def capture(self, log: I2CTransactionLog):
        self.transaction_count += 1
        error = ""
        if not log.address_acked:
            error = "Address NACK - no device responded"
            self.address_nack_count += 1
            self.error_count += 1
        elif not log.stop_condition:
            error = "Missing STOP condition"
            self.error_count += 1

        entry = I2CLogEntry(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            transaction_number=self.transaction_count,
            start_condition=log.start_condition,
            address_hex=f"0x{log.address:02X}",
            rw="READ" if log.rw_bit else "WRITE",
            address_ack="ACK" if log.address_acked else "NACK",
            register_or_first_byte=(f"0x{log.data_bytes[0]:02X}" if log.data_bytes else "N/A"),
            data_bytes_hex=str([f"0x{b:02X}" for b in log.data_bytes]),
            data_acks=str(log.data_acks),
            stop_condition=log.stop_condition,
            protocol_error=error,
        )
        self.entries.append(entry)

    def statistics(self) -> dict:
        return {
            "total_transactions": self.transaction_count,
            "address_nacks": self.address_nack_count,
            "total_errors": self.error_count,
            "success_rate_pct": round(100 * (self.transaction_count - self.error_count)
                                       / max(1, self.transaction_count), 1),
        }

    def to_csv(self, path: str):
        if not self.entries:
            return
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(self.entries[0]).keys()))
            writer.writeheader()
            for e in self.entries:
                writer.writerow(asdict(e))

    def to_json(self, path: str):
        with open(path, "w") as f:
            json.dump([asdict(e) for e in self.entries], f, indent=2)


if __name__ == "__main__":
    from master_slave import I2CSlave

    bus = I2CBus()
    bus.attach(I2CSlave(0x50, "EEPROM"))
    bus.attach(I2CSlave(0x48, "TempSensor"))
    master = I2CMaster(bus)
    analyzer = I2CProtocolAnalyzer()

    analyzer.capture(master.write(0x50, b"\x00\x99"))
    analyzer.capture(master.read(0x48, 2))
    analyzer.capture(master.write(0x7F, b"\xAA"))   # unknown address -> NACK

    print("I2C Protocol Log:")
    for e in analyzer.entries:
        print(e)

    print("\nStatistics:", analyzer.statistics())

    analyzer.to_csv("../logs/i2c_log.csv")
    analyzer.to_json("../logs/i2c_log.json")
    print("\nSaved to ../logs/i2c_log.csv and ../logs/i2c_log.json")
