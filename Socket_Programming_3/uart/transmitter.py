"""
Question 1: UART Frame Generation
----------------------------------
Simulates a UART transmitter. Accepts an ASCII character/string and builds
a UART frame: 1 Start bit + 8 Data bits + optional Parity bit + 1 Stop bit.

Frame layout (LSB first, as real UART transmits):
    [Start=0] [D0 D1 D2 D3 D4 D5 D6 D7] [Parity?] [Stop=1]
"""

from typing import List, Optional


class UARTFrame:
    """Represents a single UART frame and its component fields."""

    def __init__(self, char: str, data_bits: List[int], parity_bit: Optional[int],
                 parity_mode: str, start_bit: int = 0, stop_bit: int = 1):
        self.char = char
        self.start_bit = start_bit
        self.data_bits = data_bits          # LSB first, length 8
        self.parity_bit = parity_bit        # None if parity_mode == 'none'
        self.parity_mode = parity_mode
        self.stop_bit = stop_bit

    def as_bitstream(self) -> List[int]:
        """Return the full serialized bitstream for this frame (LSB-first data)."""
        bits = [self.start_bit] + self.data_bits
        if self.parity_bit is not None:
            bits.append(self.parity_bit)
        bits.append(self.stop_bit)
        return bits

    def as_binary_string(self) -> str:
        return "".join(str(b) for b in self.as_bitstream())

    def human_readable(self) -> str:
        parity_str = f", Parity={self.parity_bit} ({self.parity_mode})" if self.parity_bit is not None else ", Parity=None"
        return (f"Char='{self.char}' | Start={self.start_bit} | "
                f"Data(LSB->MSB)={self.data_bits} (0x{self._data_byte():02X})"
                f"{parity_str} | Stop={self.stop_bit}")

    def _data_byte(self) -> int:
        value = 0
        for i, bit in enumerate(self.data_bits):
            value |= (bit << i)
        return value


class UARTTransmitter:
    """Builds UART frames for characters/strings with optional parity."""

    def __init__(self, parity: str = "none"):
        """
        parity: 'none', 'even', or 'odd'
        """
        parity = parity.lower()
        if parity not in ("none", "even", "odd"):
            raise ValueError("parity must be 'none', 'even', or 'odd'")
        self.parity = parity

    def _char_to_bits(self, char: str) -> List[int]:
        if len(char) != 1 or ord(char) > 255:
            raise ValueError("UARTTransmitter encodes one 8-bit ASCII/byte value at a time")
        value = ord(char)
        return [(value >> i) & 1 for i in range(8)]  # LSB first

    def _compute_parity(self, data_bits: List[int]) -> Optional[int]:
        if self.parity == "none":
            return None
        ones = sum(data_bits)
        if self.parity == "even":
            return ones % 2               # makes total number of 1s even
        else:  # odd
            return 0 if ones % 2 else 1   # makes total number of 1s odd

    def build_frame(self, char: str) -> UARTFrame:
        data_bits = self._char_to_bits(char)
        parity_bit = self._compute_parity(data_bits)
        return UARTFrame(char, data_bits, parity_bit, self.parity)

    def transmit_string(self, text: str) -> List[UARTFrame]:
        """Build a frame per character; returns the list of frames (the 'wire' output)."""
        return [self.build_frame(ch) for ch in text]


def explain_uart_fields() -> str:
    return (
        "UART Frame Field Roles:\n"
        "  Start bit (0)   -> Falling edge tells the receiver a new frame begins, "
        "enabling clock/bit synchronization on an otherwise idle (high) line.\n"
        "  Data bits (8)   -> Carry the actual byte of information, sent LSB first.\n"
        "  Parity bit      -> Simple error-detection: even/odd parity lets the receiver "
        "catch single-bit corruption in the data field.\n"
        "  Stop bit (1)    -> Marks frame end and guarantees a minimum idle/high period, "
        "giving the receiver time to prepare for the next Start bit.\n"
    )


if __name__ == "__main__":
    tx = UARTTransmitter(parity="even")
    print(explain_uart_fields())

    message = "Hi!"
    frames = tx.transmit_string(message)

    print(f"Transmitting message: {message!r}\n")
    for i, frame in enumerate(frames):
        print(f"Frame {i}: {frame.human_readable()}")
        print(f"          Binary (Start..Stop): {frame.as_binary_string()}\n")
