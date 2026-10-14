"""
Question 13: SPI Protocol Analyzer
----------------------------------------
A software SPI Logic Analyzer that records Clock transitions, MOSI data,
MISO data, Chip-Select status, timestamps, packet info, and communication
statistics, then exports the captured log to CSV for offline analysis.
"""

import csv
import time
from dataclasses import dataclass, asdict
from typing import List

from master_slave import SPIMaster, SPISlave


@dataclass
class SPILogEntry:
    timestamp: str
    transfer_number: int
    byte_index: int
    cs_active: bool
    mosi_byte_hex: str
    miso_byte_hex: str
    clock_edges: int


class SPILogicAnalyzer:
    def __init__(self):
        self.entries: List[SPILogEntry] = []
        self.transfer_count = 0
        self.byte_count = 0
        self.error_count = 0

    def capture_transfer(self, master: SPIMaster, slave: SPISlave, data_out: bytes):
        self.transfer_count += 1
        slave.select(True)
        for byte_index, out_byte in enumerate(data_out):
            in_byte = 0
            for bit_pos in range(8):
                mosi_bit = (out_byte >> (7 - bit_pos)) & 1
                miso_bit = slave.transfer_bit(mosi_bit, bit_pos, byte_index)
                in_byte = (in_byte << 1) | miso_bit

            self.byte_count += 1
            entry = SPILogEntry(
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                transfer_number=self.transfer_count,
                byte_index=byte_index,
                cs_active=slave.selected,
                mosi_byte_hex=f"0x{out_byte:02X}",
                miso_byte_hex=f"0x{in_byte:02X}",
                clock_edges=16,   # 8 bits * 2 edges/bit
            )
            self.entries.append(entry)
        slave.select(False)

    def statistics(self) -> dict:
        return {
            "total_transfers": self.transfer_count,
            "total_bytes": self.byte_count,
            "total_clock_edges": self.byte_count * 16,
            "errors": self.error_count,
        }

    def to_csv(self, path: str):
        if not self.entries:
            return
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(self.entries[0]).keys()))
            writer.writeheader()
            for e in self.entries:
                writer.writerow(asdict(e))


if __name__ == "__main__":
    analyzer = SPILogicAnalyzer()
    master = SPIMaster()
    slave = SPISlave("Slave-1", response_bytes=b"\xAA\xBB\xCC")

    analyzer.capture_transfer(master, slave, b"\x01\x02\x03")
    analyzer.capture_transfer(master, slave, b"\x10\x20")

    print("Captured SPI log entries:")
    for e in analyzer.entries:
        print(e)

    print("\nCommunication statistics:", analyzer.statistics())

    analyzer.to_csv("../logs/spi_log.csv")
    print("\nSaved to ../logs/spi_log.csv")
