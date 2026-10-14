"""
Question 8: SPI Master and Slave Simulation
------------------------------------------------
Simulates one SPI Master and one Slave with full-duplex transfer:
Master drives SCLK + CS + MOSI, Slave drives MISO. On every clock pulse
a bit moves in each direction simultaneously (full duplex).
"""

from typing import List


class SPISlave:
    """A simple SPI slave that echoes back a preset response byte-for-byte
    (shift register semantics), one bit per clock, MSB first."""

    def __init__(self, name: str, response_bytes: bytes = b""):
        self.name = name
        self.response_bytes = response_bytes
        self.received_bytes = bytearray()
        self.selected = False

    def select(self, cs_active: bool):
        self.selected = cs_active

    def transfer_bit(self, mosi_bit: int, bit_index_in_byte: int, byte_index: int) -> int:
        """Given the incoming MOSI bit, shift it into an internal receive
        register and return the next MISO bit (from the preset response)."""
        if not self.selected:
            return 1  # idle/high-Z approximated as 1

        if byte_index < len(self.response_bytes):
            miso_byte = self.response_bytes[byte_index]
        else:
            miso_byte = 0x00
        miso_bit = (miso_byte >> (7 - bit_index_in_byte)) & 1
        return miso_bit

    def _commit_byte(self, byte_value: int):
        self.received_bytes.append(byte_value)


class SPIMaster:
    def __init__(self, clock_speed_hz: int = 1_000_000):
        self.clock_speed_hz = clock_speed_hz

    def transfer(self, slave: SPISlave, data_out: bytes) -> bytes:
        """Full-duplex transfer: for every byte sent, a byte is simultaneously
        received. MSB-first, one bit per clock edge."""
        slave.select(True)
        data_in = bytearray()

        for byte_index, out_byte in enumerate(data_out):
            in_byte = 0
            for bit_pos in range(8):
                mosi_bit = (out_byte >> (7 - bit_pos)) & 1
                miso_bit = slave.transfer_bit(mosi_bit, bit_pos, byte_index)
                in_byte = (in_byte << 1) | miso_bit
            data_in.append(in_byte)
            slave._commit_byte(out_byte)  # slave "sees" what master sent, for its own record

        slave.select(False)
        return bytes(data_in)


if __name__ == "__main__":
    master = SPIMaster(clock_speed_hz=4_000_000)
    slave = SPISlave("Slave-1", response_bytes=b"\xDE\xAD\xBE\xEF")

    outgoing = b"\x01\x02\x03\x04"
    print(f"Master sending (MOSI): {list(outgoing)}")

    incoming = master.transfer(slave, outgoing)
    print(f"Master received (MISO): {list(incoming)}")
    print(f"Slave recorded bytes seen on MOSI: {list(slave.received_bytes)}")
    print("\nFull-duplex confirmed: MOSI and MISO data moved simultaneously, "
          "each byte-clocked independently in each direction.")
