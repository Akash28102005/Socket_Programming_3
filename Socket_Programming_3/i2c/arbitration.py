"""
Question 18: I2C Arbitration and Clock Stretching
----------------------------------------------------------
Simulates:
  - Bus Arbitration: multiple Masters attempt to drive SDA simultaneously;
    the Master transmitting the lowest address / a '0' where another
    drives '1' loses arbitration and backs off (open-drain wired-AND rule).
  - Clock Stretching: a Slave that needs more time holds SCL low, and the
    Master waits until the Slave releases the clock before continuing.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class MasterRequest:
    name: str
    address_bits: List[int]   # MSB-first bits of the address being driven


def arbitrate(requests: List[MasterRequest]) -> Tuple[str, List[str]]:
    """
    Simulates open-drain wired-AND arbitration bit by bit: the effective bus
    value on each bit is the AND of all drivers (any '0' pulls the bus low).
    A master that drove '1' but observes '0' on the bus has lost arbitration
    and stops driving.
    """
    active = list(requests)
    losers = []
    num_bits = len(requests[0].address_bits)

    for bit_index in range(num_bits):
        if len(active) <= 1:
            break
        bus_value = 1
        for req in active:
            bus_value &= req.address_bits[bit_index]

        still_active = []
        for req in active:
            if req.address_bits[bit_index] == 1 and bus_value == 0:
                losers.append(req.name)   # this master drove 1 but bus reads 0 -> lost
            else:
                still_active.append(req)
        active = still_active

    winner = active[0].name if active else requests[0].name
    return winner, losers


class ClockStretchingSlave:
    """A slave that needs `stretch_cycles` extra cycles before it can
    respond, modeled by holding SCL low for that many simulated cycles."""

    def __init__(self, name: str, stretch_cycles: int = 0):
        self.name = name
        self.stretch_cycles = stretch_cycles

    def respond(self) -> dict:
        cycles_waited = self.stretch_cycles
        # Master must wait until SCL is released (i.e., slave stops stretching)
        return {
            "slave": self.name,
            "scl_held_low_cycles": cycles_waited,
            "master_waited": cycles_waited > 0,
            "response": "ACK+DATA",
        }


if __name__ == "__main__":
    print("-- Bus Arbitration demo --")
    # Lower address value wins in real I2C (dominant '0' wins wired-AND arbitration)
    requests = [
        MasterRequest("Master-A", [0, 1, 0, 1, 0, 0, 0]),  # address 0x28
        MasterRequest("Master-B", [0, 1, 0, 0, 0, 0, 0]),  # address 0x20 (should win: has a 0 where A has 1)
        MasterRequest("Master-C", [0, 1, 0, 1, 0, 1, 0]),  # address 0x2A
    ]
    winner, losers = arbitrate(requests)
    print(f"Requests: {[(r.name, r.address_bits) for r in requests]}")
    print(f"Arbitration winner: {winner}")
    print(f"Masters that lost arbitration and backed off: {losers}")

    print("\n-- Clock Stretching demo --")
    fast_slave = ClockStretchingSlave("FastSensor", stretch_cycles=0)
    slow_slave = ClockStretchingSlave("SlowEEPROM", stretch_cycles=5)

    for slave in (fast_slave, slow_slave):
        result = slave.respond()
        print(f"{result['slave']}: SCL held low for {result['scl_held_low_cycles']} cycles, "
              f"master waited: {result['master_waited']}, response: {result['response']}")
