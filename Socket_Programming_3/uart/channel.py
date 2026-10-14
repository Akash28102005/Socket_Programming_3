"""
Question 3: UART Communication Channel
----------------------------------------
Full model: Transmitter -> Channel -> Receiver.
The channel simulates transmission delay and random bit errors (bit flips).
"""

import random
import time
from typing import List
from transmitter import UARTTransmitter
from receiver import UARTReceiver, ReceptionResult


class UARTChannel:
    def __init__(self, bit_error_rate: float = 0.0, delay_ms: float = 0.0, seed: int = None):
        """
        bit_error_rate: probability [0,1] that any individual bit gets flipped in transit
        delay_ms: simulated propagation delay per frame (milliseconds)
        """
        if not (0.0 <= bit_error_rate <= 1.0):
            raise ValueError("bit_error_rate must be between 0 and 1")
        self.bit_error_rate = bit_error_rate
        self.delay_ms = delay_ms
        self.rng = random.Random(seed)

    def transmit(self, bitstream: List[int]) -> List[int]:
        """Simulate delay + possible random bit corruption on a single frame."""
        if self.delay_ms > 0:
            time.sleep(self.delay_ms / 1000.0)

        corrupted = []
        for bit in bitstream:
            if self.rng.random() < self.bit_error_rate:
                corrupted.append(bit ^ 1)   # flip
            else:
                corrupted.append(bit)
        return corrupted


class UARTCommunicationModel:
    """Ties Transmitter + Channel + Receiver into one system."""

    def __init__(self, parity: str = "even", bit_error_rate: float = 0.0,
                 delay_ms: float = 0.0, seed: int = None):
        self.tx = UARTTransmitter(parity=parity)
        self.rx = UARTReceiver(parity=parity)
        self.channel = UARTChannel(bit_error_rate=bit_error_rate, delay_ms=delay_ms, seed=seed)

    def send_message(self, text: str) -> List[ReceptionResult]:
        frames = self.tx.transmit_string(text)
        results = []
        for frame in frames:
            wire_bits = self.channel.transmit(frame.as_bitstream())
            results.append(self.rx.receive_frame(wire_bits))
        return results


if __name__ == "__main__":
    model = UARTCommunicationModel(parity="even", bit_error_rate=0.02, delay_ms=1, seed=42)

    message = "Hello, UART!"
    print(f"Sending message: {message!r} over a channel with 2% bit error rate\n")
    results = model.send_message(message)

    ok_count = 0
    reconstructed = []
    for i, res in enumerate(results):
        print(f"Frame {i}: {res}")
        if res.ok:
            ok_count += 1
        reconstructed.append(res.char if res.char else "?")

    print(f"\nReconstructed: {''.join(reconstructed)!r}")
    print(f"Integrity: {ok_count}/{len(results)} frames received without error "
          f"({100*ok_count/len(results):.1f}%)")
