"""
Question 2: UART Receiver Design
----------------------------------
Consumes a serial bitstream (as produced by UARTTransmitter/UARTFrame),
detects Start bit, reconstructs the data byte, checks parity, validates
the Stop bit, and converts back to ASCII. Reports frame/parity/sync errors.
"""

from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class ReceptionResult:
    char: Optional[str]
    data_byte: Optional[int]
    ok: bool
    errors: List[str] = field(default_factory=list)

    def __str__(self):
        status = "OK" if self.ok else "FAILED"
        char_repr = repr(self.char) if self.char is not None else "N/A"
        err_str = f" | Errors: {', '.join(self.errors)}" if self.errors else ""
        return f"[{status}] char={char_repr}{err_str}"


class UARTReceiver:
    def __init__(self, parity: str = "none"):
        parity = parity.lower()
        if parity not in ("none", "even", "odd"):
            raise ValueError("parity must be 'none', 'even', or 'odd'")
        self.parity = parity

    def _expected_parity(self, data_bits: List[int]) -> int:
        ones = sum(data_bits)
        if self.parity == "even":
            return ones % 2
        else:  # odd
            return 0 if ones % 2 else 1

    def receive_frame(self, bitstream: List[int]) -> ReceptionResult:
        """
        bitstream layout: [start][8 data bits LSB first][parity?][stop]
        """
        errors = []
        expected_len = 1 + 8 + (1 if self.parity != "none" else 0) + 1
        if len(bitstream) != expected_len:
            errors.append(f"Frame length error: expected {expected_len} bits, got {len(bitstream)}")
            return ReceptionResult(None, None, False, errors)

        idx = 0
        start_bit = bitstream[idx]; idx += 1
        if start_bit != 0:
            errors.append("Synchronization error: Start bit not detected (expected 0)")

        data_bits = bitstream[idx:idx + 8]; idx += 8

        parity_bit = None
        if self.parity != "none":
            parity_bit = bitstream[idx]; idx += 1

        stop_bit = bitstream[idx]; idx += 1
        if stop_bit != 1:
            errors.append("Frame error: Stop bit not detected (expected 1)")

        if parity_bit is not None:
            expected = self._expected_parity(data_bits)
            if parity_bit != expected:
                errors.append(f"Parity error: expected {expected}, received {parity_bit}")

        data_byte = 0
        for i, bit in enumerate(data_bits):
            data_byte |= (bit << i)
        char = chr(data_byte)

        ok = len(errors) == 0
        return ReceptionResult(char, data_byte, ok, errors)

    def receive_frames(self, frames_bitstreams: List[List[int]]) -> List[ReceptionResult]:
        return [self.receive_frame(bs) for bs in frames_bitstreams]


if __name__ == "__main__":
    from transmitter import UARTTransmitter

    tx = UARTTransmitter(parity="even")
    rx = UARTReceiver(parity="even")

    message = "Hi!"
    frames = tx.transmit_string(message)
    bitstreams = [f.as_bitstream() for f in frames]

    print(f"Receiving message encoded as: {message!r}\n")
    results = rx.receive_frames(bitstreams)
    for i, res in enumerate(results):
        print(f"Frame {i}: {res}")

    reconstructed = "".join(r.char for r in results if r.char)
    print(f"\nReconstructed string: {reconstructed!r}")
