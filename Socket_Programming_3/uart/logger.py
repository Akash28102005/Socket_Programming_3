"""
Question 6: UART Protocol Logger
------------------------------------
Protocol analyzer that logs every transmitted/received frame with:
timestamp, frame number, transmitted data, binary, hex, ASCII char,
parity status, checksum status, and overall frame status.
Stores the log as CSV and JSON.
"""

import csv
import json
import time
from dataclasses import dataclass, asdict
from typing import List, Optional

from transmitter import UARTTransmitter
from receiver import UARTReceiver
from channel import UARTChannel


@dataclass
class LogEntry:
    frame_number: int
    timestamp: str
    char: str
    binary: str
    hex_value: str
    ascii_char: str
    parity_status: str
    checksum_status: str
    frame_status: str


class UARTProtocolLogger:
    def __init__(self, parity: str = "even"):
        self.parity = parity
        self.entries: List[LogEntry] = []

    def log_session(self, tx: UARTTransmitter, rx: UARTReceiver,
                     channel: UARTChannel, message: str):
        frames = tx.transmit_string(message)
        for i, frame in enumerate(frames):
            wire_bits = channel.transmit(frame.as_bitstream())
            result = rx.receive_frame(wire_bits)

            parity_status = "N/A"
            if self.parity != "none":
                parity_status = "OK" if not any("Parity" in e for e in result.errors) else "FAIL"

            # UART frames here have no checksum field (that's the packet protocol, Q5);
            # report N/A to keep the log schema uniform with Q5-style logs if reused.
            checksum_status = "N/A"

            entry = LogEntry(
                frame_number=i,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                char=repr(frame.char),
                binary=frame.as_binary_string(),
                hex_value=f"0x{ord(frame.char):02X}",
                ascii_char=frame.char if frame.char.isprintable() else repr(frame.char),
                parity_status=parity_status,
                checksum_status=checksum_status,
                frame_status="OK" if result.ok else "FAIL: " + "; ".join(result.errors),
            )
            self.entries.append(entry)

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
    tx = UARTTransmitter(parity="even")
    rx = UARTReceiver(parity="even")
    channel = UARTChannel(bit_error_rate=0.05, delay_ms=0, seed=7)

    logger = UARTProtocolLogger(parity="even")
    logger.log_session(tx, rx, channel, "Log this message!")

    logger.to_csv("../logs/uart_log.csv")
    logger.to_json("../logs/uart_log.json")

    print("Logged frames:")
    for e in logger.entries:
        print(e)
    print("\nSaved to ../logs/uart_log.csv and ../logs/uart_log.json")
