"""
Question 4: UART Error Injection
------------------------------------
Deliberately injects specific error types into a UART frame and shows that
the receiver correctly diagnoses each one:
  - Incorrect Start bit
  - Corrupted Data bit(s)
  - Invalid Parity bit
  - Incorrect Stop bit
  - Communication timeout (no frame arrives in time)
"""

from typing import List
from transmitter import UARTTransmitter
from receiver import UARTReceiver


class TimeoutError_(Exception):
    """Raised to simulate a communication timeout."""
    pass


class ErrorInjector:
    @staticmethod
    def corrupt_start_bit(bits: List[int]) -> List[int]:
        bits = bits.copy()
        bits[0] = 1 - bits[0]   # should be 0, force to 1
        return bits

    @staticmethod
    def corrupt_data_bit(bits: List[int], position: int = 0) -> List[int]:
        bits = bits.copy()
        data_index = 1 + position   # offset past start bit
        bits[data_index] ^= 1
        return bits

    @staticmethod
    def corrupt_parity_bit(bits: List[int], parity_index: int = 9) -> List[int]:
        bits = bits.copy()
        bits[parity_index] ^= 1
        return bits

    @staticmethod
    def corrupt_stop_bit(bits: List[int]) -> List[int]:
        bits = bits.copy()
        bits[-1] = 1 - bits[-1]   # should be 1, force to 0
        return bits

    @staticmethod
    def simulate_timeout():
        raise TimeoutError_("No frame received within the expected time window (timeout).")


def demonstrate_error_scenarios():
    tx = UARTTransmitter(parity="even")
    rx = UARTReceiver(parity="even")

    frame = tx.build_frame("A")
    original_bits = frame.as_bitstream()
    print(f"Original frame for 'A': {original_bits}\n")

    scenarios = {
        "Correct frame": original_bits,
        "Incorrect Start bit": ErrorInjector.corrupt_start_bit(original_bits),
        "Corrupted Data bit (bit 3)": ErrorInjector.corrupt_data_bit(original_bits, position=3),
        "Invalid Parity bit": ErrorInjector.corrupt_parity_bit(original_bits),
        "Incorrect Stop bit": ErrorInjector.corrupt_stop_bit(original_bits),
    }

    for name, bits in scenarios.items():
        result = rx.receive_frame(bits)
        print(f"Scenario: {name}")
        print(f"  Bits: {bits}")
        print(f"  Result: {result}\n")

    print("Scenario: Communication timeout")
    try:
        ErrorInjector.simulate_timeout()
    except TimeoutError_ as e:
        print(f"  Result: [FAILED] Timeout error -> {e}\n")


if __name__ == "__main__":
    demonstrate_error_scenarios()
