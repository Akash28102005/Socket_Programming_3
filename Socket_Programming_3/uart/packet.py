"""
Question 5: UART Packet-Based Communication
-----------------------------------------------
Packet format:
  [Header (1 byte, 0xAA)] [Length (1 byte)] [Payload (N bytes)]
  [Checksum (1 byte)] [End Marker (1 byte, 0x55)]

Checksum = 8-bit sum (mod 256) of all payload bytes.
"""

from dataclasses import dataclass
from typing import List, Optional

HEADER = 0xAA
END_MARKER = 0x55


@dataclass
class UARTPacket:
    header: int
    length: int
    payload: bytes
    checksum: int
    end_marker: int

    def to_bytes(self) -> bytes:
        return bytes([self.header, self.length]) + self.payload + \
               bytes([self.checksum, self.end_marker])


class PacketBuilder:
    @staticmethod
    def compute_checksum(payload: bytes) -> int:
        return sum(payload) % 256

    @staticmethod
    def build(payload: str) -> UARTPacket:
        payload_bytes = payload.encode("ascii")
        if len(payload_bytes) > 255:
            raise ValueError("Payload too long for 1-byte length field (max 255 bytes)")
        checksum = PacketBuilder.compute_checksum(payload_bytes)
        return UARTPacket(HEADER, len(payload_bytes), payload_bytes, checksum, END_MARKER)


class PacketReceiver:
    """Parses a raw byte stream into a packet, validating structure and checksum."""

    def parse(self, raw: bytes) -> dict:
        errors = []

        if len(raw) < 4:
            return {"ok": False, "payload": None, "errors": ["Packet too short to be valid"]}

        header = raw[0]
        length = raw[1]

        if header != HEADER:
            errors.append(f"Invalid header: expected 0x{HEADER:02X}, got 0x{header:02X}")

        expected_total_len = 2 + length + 2  # header+len + payload + checksum + end
        if len(raw) != expected_total_len:
            errors.append(f"Length mismatch: declared payload length {length}, "
                           f"packet size implies {len(raw) - 4} bytes")
            # Attempt best-effort parse using min available length to still report other errors
            payload = raw[2:2 + max(0, min(length, len(raw) - 4))]
        else:
            payload = raw[2:2 + length]

        checksum_index = 2 + length
        received_checksum = raw[checksum_index] if checksum_index < len(raw) else None
        end_marker = raw[checksum_index + 1] if checksum_index + 1 < len(raw) else None

        expected_checksum = PacketBuilder.compute_checksum(payload)
        if received_checksum != expected_checksum:
            errors.append(f"Checksum mismatch: expected {expected_checksum}, got {received_checksum}")

        if end_marker != END_MARKER:
            errors.append(f"Invalid end marker: expected 0x{END_MARKER:02X}, got "
                           f"{'0x%02X' % end_marker if end_marker is not None else None}")

        ok = len(errors) == 0
        return {
            "ok": ok,
            "payload": payload.decode("ascii", errors="replace") if ok else None,
            "errors": errors,
        }


def corrupt_packet(raw: bytes, mode: str) -> bytes:
    raw = bytearray(raw)
    if mode == "checksum":
        raw[-2] ^= 0xFF
    elif mode == "payload":
        if len(raw) > 3:
            raw[2] ^= 0xFF
    elif mode == "header":
        raw[0] ^= 0xFF
    elif mode == "end_marker":
        raw[-1] ^= 0xFF
    return bytes(raw)


if __name__ == "__main__":
    receiver = PacketReceiver()

    packet = PacketBuilder.build("Hello")
    raw = packet.to_bytes()
    print(f"Built packet bytes: {list(raw)}")

    print("\n-- Valid packet --")
    print(receiver.parse(raw))

    print("\n-- Corrupted payload (checksum will fail) --")
    print(receiver.parse(corrupt_packet(raw, "payload")))

    print("\n-- Corrupted checksum byte directly --")
    print(receiver.parse(corrupt_packet(raw, "checksum")))

    print("\n-- Corrupted header --")
    print(receiver.parse(corrupt_packet(raw, "header")))

    print("\n-- Corrupted end marker --")
    print(receiver.parse(corrupt_packet(raw, "end_marker")))
