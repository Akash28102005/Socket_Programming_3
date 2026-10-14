"""
Question 7: UART Verification Framework
--------------------------------------------
pytest-based automated test suite covering: valid frames, invalid frames,
parity errors, checksum(packet) failures, timeout conditions, continuous
transmission, and boundary value testing.

Run with:  pytest -v test_uart.py
"""

import pytest
from transmitter import UARTTransmitter
from receiver import UARTReceiver
from error_injection import ErrorInjector, TimeoutError_
from packet import PacketBuilder, PacketReceiver, corrupt_packet


# ---------- Valid frame tests ----------

def test_valid_frame_even_parity():
    tx = UARTTransmitter(parity="even")
    rx = UARTReceiver(parity="even")
    frame = tx.build_frame("A")
    result = rx.receive_frame(frame.as_bitstream())
    assert result.ok
    assert result.char == "A"


def test_valid_frame_odd_parity():
    tx = UARTTransmitter(parity="odd")
    rx = UARTReceiver(parity="odd")
    frame = tx.build_frame("Z")
    result = rx.receive_frame(frame.as_bitstream())
    assert result.ok
    assert result.char == "Z"


def test_valid_frame_no_parity():
    tx = UARTTransmitter(parity="none")
    rx = UARTReceiver(parity="none")
    frame = tx.build_frame("k")
    result = rx.receive_frame(frame.as_bitstream())
    assert result.ok


# ---------- Invalid frame / error tests ----------

def test_incorrect_start_bit():
    tx = UARTTransmitter(parity="even")
    rx = UARTReceiver(parity="even")
    bits = tx.build_frame("A").as_bitstream()
    bad = ErrorInjector.corrupt_start_bit(bits)
    result = rx.receive_frame(bad)
    assert not result.ok
    assert any("Synchronization" in e for e in result.errors)


def test_corrupted_data_bit_changes_char_but_frame_may_still_fail_parity():
    tx = UARTTransmitter(parity="even")
    rx = UARTReceiver(parity="even")
    bits = tx.build_frame("A").as_bitstream()
    bad = ErrorInjector.corrupt_data_bit(bits, position=0)
    result = rx.receive_frame(bad)
    # Flipping one data bit changes bit-count parity -> parity check should fail
    assert not result.ok
    assert any("Parity" in e for e in result.errors)


def test_invalid_parity_bit():
    tx = UARTTransmitter(parity="even")
    rx = UARTReceiver(parity="even")
    bits = tx.build_frame("A").as_bitstream()
    bad = ErrorInjector.corrupt_parity_bit(bits)
    result = rx.receive_frame(bad)
    assert not result.ok
    assert any("Parity" in e for e in result.errors)


def test_incorrect_stop_bit():
    tx = UARTTransmitter(parity="even")
    rx = UARTReceiver(parity="even")
    bits = tx.build_frame("A").as_bitstream()
    bad = ErrorInjector.corrupt_stop_bit(bits)
    result = rx.receive_frame(bad)
    assert not result.ok
    assert any("Stop bit" in e for e in result.errors)


def test_timeout_condition():
    with pytest.raises(TimeoutError_):
        ErrorInjector.simulate_timeout()


# ---------- Packet / checksum tests ----------

def test_valid_packet_checksum():
    packet = PacketBuilder.build("Data")
    raw = packet.to_bytes()
    result = PacketReceiver().parse(raw)
    assert result["ok"]
    assert result["payload"] == "Data"


def test_checksum_failure_detected():
    packet = PacketBuilder.build("Data")
    raw = corrupt_packet(packet.to_bytes(), "payload")
    result = PacketReceiver().parse(raw)
    assert not result["ok"]
    assert any("Checksum" in e for e in result["errors"])


# ---------- Continuous transmission ----------

def test_continuous_transmission_multiple_characters():
    tx = UARTTransmitter(parity="even")
    rx = UARTReceiver(parity="even")
    message = "UART Test 123"
    frames = tx.transmit_string(message)
    results = [rx.receive_frame(f.as_bitstream()) for f in frames]
    reconstructed = "".join(r.char for r in results)
    assert reconstructed == message
    assert all(r.ok for r in results)


# ---------- Boundary value tests ----------

@pytest.mark.parametrize("char", ["\x00", "\x7f", "A", "z", " "])
def test_boundary_ascii_values(char):
    tx = UARTTransmitter(parity="even")
    rx = UARTReceiver(parity="even")
    frame = tx.build_frame(char)
    result = rx.receive_frame(frame.as_bitstream())
    assert result.ok
    assert result.char == char


def test_empty_string_transmission():
    tx = UARTTransmitter(parity="even")
    assert tx.transmit_string("") == []


def test_frame_length_error_on_truncated_bitstream():
    rx = UARTReceiver(parity="even")
    result = rx.receive_frame([0, 1, 1, 1, 0])  # too short
    assert not result.ok
    assert any("length" in e.lower() for e in result.errors)


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
