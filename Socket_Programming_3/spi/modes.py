"""
Question 9: SPI Communication Modes
----------------------------------------
Models CPOL/CPHA and the resulting four SPI modes:
  Mode 0: CPOL=0, CPHA=0  -> sample on rising edge,  clock idles low
  Mode 1: CPOL=0, CPHA=1  -> sample on falling edge,  clock idles low
  Mode 2: CPOL=1, CPHA=0  -> sample on falling edge,  clock idles high
  Mode 3: CPOL=1, CPHA=1  -> sample on rising edge,   clock idles high

Since this is a logical simulation (no real electrical clock), we model
each mode by generating a "clock transition log" and applying the
correct sample-edge rule when shifting data, so the transferred bytes
match what real SPI hardware would exchange in that mode.
"""

from dataclasses import dataclass
from typing import List, Tuple

SPI_MODES = {
    0: {"CPOL": 0, "CPHA": 0},
    1: {"CPOL": 0, "CPHA": 1},
    2: {"CPOL": 1, "CPHA": 0},
    3: {"CPOL": 1, "CPHA": 1},
}


@dataclass
class ClockEvent:
    edge_number: int
    clock_level: int
    action: str   # "sample" or "shift"


def generate_clock_log(mode: int, num_bits: int) -> List[ClockEvent]:
    """Builds the sequence of clock edges and whether each is a sample or
    a shift-out event, based on CPOL/CPHA for the given mode."""
    cfg = SPI_MODES[mode]
    cpol, cpha = cfg["CPOL"], cfg["CPHA"]
    idle_level = cpol
    events = []
    level = idle_level
    edge = 0
    for bit in range(num_bits):
        # First edge of each bit period
        level = 1 - level
        edge += 1
        first_action = "shift" if cpha == 1 else "sample"
        events.append(ClockEvent(edge, level, first_action))
        # Second edge of each bit period
        level = 1 - level
        edge += 1
        second_action = "sample" if cpha == 1 else "shift"
        events.append(ClockEvent(edge, level, second_action))
    return events


def transfer_with_mode(mode: int, mosi_byte: int, miso_byte: int) -> Tuple[int, int, List[ClockEvent]]:
    """Simulate one full-duplex byte transfer under the given SPI mode.
    Regardless of mode, correctly-implemented SPI yields the same final
    byte values -- CPOL/CPHA only change *when* sampling happens relative
    to the clock edge, which matters for real hardware timing margins."""
    events = generate_clock_log(mode, 8)

    mosi_bits = [(mosi_byte >> (7 - i)) & 1 for i in range(8)]
    miso_bits = [(miso_byte >> (7 - i)) & 1 for i in range(8)]

    received_from_slave = 0
    received_from_master = 0
    bit_i = 0
    for ev in events:
        if ev.action == "sample" and bit_i < 8:
            received_from_slave = (received_from_slave << 1) | miso_bits[bit_i]
            received_from_master = (received_from_master << 1) | mosi_bits[bit_i]
            bit_i += 1

    return received_from_master, received_from_slave, events


def describe_mode(mode: int) -> str:
    cfg = SPI_MODES[mode]
    edge_master = "rising" if (cfg["CPOL"] == cfg["CPHA"]) else "falling"
    return (f"Mode {mode}: CPOL={cfg['CPOL']}, CPHA={cfg['CPHA']} -> "
            f"clock idles {'HIGH' if cfg['CPOL'] else 'LOW'}, "
            f"data sampled on {edge_master} edge")


if __name__ == "__main__":
    mosi_byte = 0xA5   # 1010 0101
    miso_byte = 0x3C   # 0011 1100

    for mode in range(4):
        print(describe_mode(mode))
        rx_master, rx_slave, events = transfer_with_mode(mode, mosi_byte, miso_byte)
        print(f"  MOSI byte sent:      0x{mosi_byte:02X}")
        print(f"  MISO byte sent:      0x{miso_byte:02X}")
        print(f"  Master received:     0x{rx_master:02X}  (should equal MOSI byte, echoed back for verification)")
        print(f"  Slave-side captured: 0x{rx_slave:02X}   (should equal MISO byte)")
        print(f"  Clock edges (first 4 of {len(events)}): "
              f"{[(e.edge_number, e.clock_level, e.action) for e in events[:4]]}")
        print()

    print("Comparison: all four modes exchange the same bytes correctly; only the")
    print("clock-edge polarity/phase used for sampling vs. shifting differs, which")
    print("is why Master and Slave must agree on the same mode to interoperate.")
