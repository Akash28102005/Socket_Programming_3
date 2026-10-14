"""
Question 12: SPI CRC Verification
---------------------------------------
Appends a CRC-8 field to every SPI packet. The receiver independently
recomputes the CRC over the payload and compares it to the received
value, accepting valid packets and rejecting corrupted ones.
"""

from dataclasses import dataclass
from typing import Tuple

CRC8_POLY = 0x07   # x^8 + x^2 + x^1 + 1 (common CRC-8-CCITT variant)


def crc8(data: bytes, poly: int = CRC8_POLY, init: int = 0x00) -> int:
    crc = init
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ poly) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


@dataclass
class SPIPacketCRC:
    payload: bytes
    crc: int

    def to_bytes(self) -> bytes:
        return self.payload + bytes([self.crc])


class SPITransmitterCRC:
    @staticmethod
    def build(payload: bytes) -> SPIPacketCRC:
        return SPIPacketCRC(payload, crc8(payload))


class SPIReceiverCRC:
    @staticmethod
    def verify(raw: bytes) -> Tuple[bool, bytes, int, int]:
        """Returns (is_valid, payload, expected_crc, received_crc)."""
        if len(raw) < 1:
            return False, b"", 0, 0
        payload, received_crc = raw[:-1], raw[-1]
        expected_crc = crc8(payload)
        return expected_crc == received_crc, payload, expected_crc, received_crc


def corrupt(raw: bytes, byte_index: int) -> bytes:
    raw = bytearray(raw)
    raw[byte_index] ^= 0xFF
    return bytes(raw)


if __name__ == "__main__":
    payload = b"SPI-DATA"
    packet = SPITransmitterCRC.build(payload)
    raw = packet.to_bytes()
    print(f"Payload: {payload}, CRC-8: 0x{packet.crc:02X}, Raw packet: {list(raw)}")

    print("\n-- Valid packet --")
    valid, pl, exp, rec = SPIReceiverCRC.verify(raw)
    print(f"Valid={valid}, payload={pl}, expected_crc=0x{exp:02X}, received_crc=0x{rec:02X}")

    print("\n-- Corrupted payload byte --")
    bad = corrupt(raw, 2)
    valid, pl, exp, rec = SPIReceiverCRC.verify(bad)
    print(f"Valid={valid}, payload={pl}, expected_crc=0x{exp:02X}, received_crc=0x{rec:02X}")
    print("-> Packet correctly rejected due to CRC mismatch." if not valid else "-> ERROR: should have failed")

    print("\n-- Corrupted CRC byte itself --")
    bad_crc = corrupt(raw, -1)
    valid, pl, exp, rec = SPIReceiverCRC.verify(bad_crc)
    print(f"Valid={valid}, payload={pl}, expected_crc=0x{exp:02X}, received_crc=0x{rec:02X}")
