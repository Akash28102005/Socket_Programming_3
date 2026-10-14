"""
Question 14: SPI Verification Framework
--------------------------------------------
pytest-based automated test suite for the SPI simulator: functional tests,
timing verification, invalid clock conditions, incorrect Chip-Select
handling, CRC verification, random data transmission, stress testing,
and continuous communication.

Run with:  pytest -v test_spi.py
"""

import random
import pytest

from master_slave import SPIMaster, SPISlave
from modes import transfer_with_mode, generate_clock_log, SPI_MODES
from multi_slave import SPIBus, TemperatureSensorSlave, ADCSlave
from crc import SPITransmitterCRC, SPIReceiverCRC, corrupt
from eeprom import SPIEEPROM, EEPROMCommand


# ---------- Functional tests ----------

def test_basic_full_duplex_transfer():
    master = SPIMaster()
    slave = SPISlave("S1", response_bytes=b"\x11\x22")
    result = master.transfer(slave, b"\xAA\xBB")
    assert result == b"\x11\x22"
    assert list(slave.received_bytes) == [0xAA, 0xBB]


def test_eeprom_write_then_read():
    eeprom = SPIEEPROM()
    eeprom.handle_command(EEPROMCommand.WRITE, address=0, data=b"AB")
    result = eeprom.handle_command(EEPROMCommand.READ, address=0, data=b"\x00\x00")
    assert result["read_data"] == b"AB"


# ---------- Timing verification ----------

@pytest.mark.parametrize("mode", [0, 1, 2, 3])
def test_clock_edge_count_per_mode(mode):
    events = generate_clock_log(mode, num_bits=8)
    assert len(events) == 16  # 2 edges per bit


@pytest.mark.parametrize("mode", [0, 1, 2, 3])
def test_all_modes_transfer_correct_bytes(mode):
    rx_master, rx_slave, _ = transfer_with_mode(mode, 0xA5, 0x3C)
    assert rx_master == 0xA5
    assert rx_slave == 0x3C


# ---------- Invalid clock condition ----------

def test_invalid_mode_raises():
    with pytest.raises(KeyError):
        generate_clock_log(mode=4, num_bits=8)


# ---------- Chip-Select handling ----------

def test_only_selected_slave_is_active():
    bus = SPIBus()
    bus.attach("A", SPISlave("A", response_bytes=b"\x01"))
    bus.attach("B", SPISlave("B", response_bytes=b"\x02"))
    master = SPIMaster()

    bus.transfer(master, "A", b"\x00")
    assert bus.devices["A"].selected is False   # deselected after transfer
    assert bus.devices["B"].selected is False   # never selected


def test_incorrect_cs_target_raises():
    bus = SPIBus()
    bus.attach("A", SPISlave("A"))
    master = SPIMaster()
    with pytest.raises(ValueError):
        bus.transfer(master, "NONEXISTENT", b"\x00")


# ---------- CRC verification ----------

def test_crc_valid_packet_accepted():
    packet = SPITransmitterCRC.build(b"OK-DATA")
    valid, payload, exp, rec = SPIReceiverCRC.verify(packet.to_bytes())
    assert valid
    assert payload == b"OK-DATA"


def test_crc_corrupted_packet_rejected():
    packet = SPITransmitterCRC.build(b"OK-DATA")
    bad = corrupt(packet.to_bytes(), 0)
    valid, *_ = SPIReceiverCRC.verify(bad)
    assert not valid


# ---------- Random data / stress testing ----------

def test_random_data_round_trip():
    rng = random.Random(123)
    master = SPIMaster()
    for _ in range(20):
        payload = bytes(rng.randint(0, 255) for _ in range(4))
        slave = SPISlave("Random", response_bytes=payload)
        result = master.transfer(slave, b"\x00\x00\x00\x00")
        assert result == payload


def test_stress_many_consecutive_transfers():
    master = SPIMaster()
    slave = SPISlave("Stress", response_bytes=b"\xFF")
    for _ in range(500):
        result = master.transfer(slave, b"\x00")
        assert result == b"\xFF"


# ---------- Continuous communication with multiple peripherals ----------

def test_continuous_multi_peripheral_communication():
    bus = SPIBus()
    bus.attach("EEPROM", SPISlave("EEPROM", response_bytes=b"\x01\x02"))
    bus.attach("TEMP", TemperatureSensorSlave("TEMP", seed=5))
    bus.attach("ADC", ADCSlave("ADC", seed=9))
    master = SPIMaster()

    for name in ["EEPROM", "TEMP", "ADC", "EEPROM", "TEMP"]:
        result = bus.transfer(master, name, b"\x00" * (2 if name == "EEPROM" else 1))
        assert result is not None


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
