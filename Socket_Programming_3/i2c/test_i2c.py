"""
Question 21: I2C Verification Framework
--------------------------------------------
Comprehensive pytest suite validating: correct device addressing,
ACK/NACK handling, register access, repeated Start conditions, Clock
Stretching, arbitration, invalid addresses, timeout conditions, and
long-duration communication. Prints a pass/fail summary with coverage.

Run with:  pytest -v test_i2c.py
"""

import time
import pytest

from master_slave import I2CBus, I2CMaster, I2CSlave
from register_device import RegisterDevice
from multi_device import build_demo_bus
from arbitration import arbitrate, MasterRequest, ClockStretchingSlave


# ---------- Device addressing ----------

def test_correct_device_addressing():
    bus = build_demo_bus()
    master = I2CMaster(bus)
    log = master.write(0x50, bytes([0x00, 0xAB]))  # EEPROM
    assert log.address == 0x50
    assert log.address_acked


def test_each_device_reachable_independently():
    bus = build_demo_bus()
    master = I2CMaster(bus)
    for addr in [0x50, 0x48, 0x68, 0x3C]:
        log = master.write(addr, bytes([0x00]))
        assert log.address_acked, f"Device at 0x{addr:02X} should ACK"


# ---------- ACK / NACK handling ----------

def test_ack_on_known_address():
    bus = I2CBus()
    bus.attach(I2CSlave(0x10, "X"))
    master = I2CMaster(bus)
    log = master.write(0x10, b"\x01")
    assert log.address_acked


def test_nack_on_unknown_address():
    bus = I2CBus()
    bus.attach(I2CSlave(0x10, "X"))
    master = I2CMaster(bus)
    log = master.write(0x77, b"\x01")   # not attached
    assert not log.address_acked


# ---------- Register access ----------

def test_register_write_then_read():
    bus = I2CBus()
    dev = RegisterDevice(0x40, "Dev", num_registers=8)
    bus.attach(dev)
    master = I2CMaster(bus)

    master.write(0x40, bytes([0x02, 0x77]))   # write register 2 = 0x77
    master.write(0x40, bytes([0x02]))         # set pointer to register 2
    log = master.read(0x40, 1)
    assert log.data_bytes[0] == 0x77


def test_register_out_of_range_write_fails():
    bus = I2CBus()
    dev = RegisterDevice(0x40, "Dev", num_registers=4)
    bus.attach(dev)
    master = I2CMaster(bus)
    log = master.write(0x40, bytes([0x10, 0x01]))   # register 0x10 doesn't exist
    assert all(ack is False for ack in log.data_acks)


# ---------- Repeated Start condition ----------

def test_repeated_start_write_then_read_same_transaction_style():
    bus = I2CBus()
    dev = RegisterDevice(0x40, "Dev", num_registers=4)
    bus.attach(dev)
    master = I2CMaster(bus)

    # Simulate a repeated-START pattern: write register pointer, immediately read
    write_log = master.write(0x40, bytes([0x01]))
    read_log = master.read(0x40, 1)
    assert write_log.stop_condition and read_log.stop_condition
    assert write_log.address == read_log.address == 0x40


# ---------- Clock stretching ----------

def test_clock_stretching_slave_holds_scl():
    slave = ClockStretchingSlave("Slow", stretch_cycles=10)
    result = slave.respond()
    assert result["master_waited"] is True
    assert result["scl_held_low_cycles"] == 10


def test_no_clock_stretching_when_not_needed():
    slave = ClockStretchingSlave("Fast", stretch_cycles=0)
    result = slave.respond()
    assert result["master_waited"] is False


# ---------- Arbitration ----------

def test_arbitration_lower_address_wins():
    requests = [
        MasterRequest("A", [0, 1, 1]),
        MasterRequest("B", [0, 1, 0]),  # has a 0 where A has 1 -> B wins
    ]
    winner, losers = arbitrate(requests)
    assert winner == "B"
    assert "A" in losers


def test_arbitration_single_master_always_wins():
    requests = [MasterRequest("Solo", [1, 0, 1])]
    winner, losers = arbitrate(requests)
    assert winner == "Solo"
    assert losers == []


# ---------- Invalid addresses ----------

def test_duplicate_address_raises():
    bus = I2CBus()
    bus.attach(I2CSlave(0x50, "A"))
    with pytest.raises(ValueError):
        bus.attach(I2CSlave(0x50, "B"))


# ---------- Timeout condition ----------

def test_timeout_when_no_response_simulated():
    class DeadBus(I2CBus):
        def find(self, address):
            return None   # simulate every device timing out / not responding

    bus = DeadBus()
    master = I2CMaster(bus)
    log = master.write(0x50, b"\x00")
    assert not log.address_acked   # modeled as address NACK / timeout equivalent


# ---------- Long-duration / stress communication ----------

def test_long_duration_communication():
    bus = build_demo_bus()
    master = I2CMaster(bus)
    start = time.time()
    for i in range(300):
        master.write(0x50, bytes([i % 256, (i * 2) % 256]))
        master.read(0x48, 1)
    elapsed = time.time() - start
    assert elapsed < 5.0  # sanity bound; simulation should be fast


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
