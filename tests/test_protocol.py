import pytest

from hp3001.services import protocol
from hp3001.services.device import FakeDevice


def packet(*channels):
    body = bytearray()
    for i in range(8):
        body += bytes(channels[i]) if i < len(channels) else b"\x7f\xff\xff"
    return bytes([0x7B]) + bytes(body) + b"\x40\x7d" + bytes(37)


def test_parse_positive_negative_and_missing():
    r = protocol.parse(packet((0x00, 0xFB, 55), (0xFF, 0xF6, 40), (0x01, 0x2B, 60)))
    assert [(x.channel, x.temperature_c, x.humidity) for x in r] == [
        (1, 25.1, 55), (2, -1.0, 40), (3, 29.9, 60)]


def test_calibration_packet_rejected():
    with pytest.raises(ValueError):
        protocol.parse(b"\x7b" + bytes(24) + b"\x40\x7d")


def test_bad_start():
    with pytest.raises(ValueError):
        protocol.parse(b"\x00" * 30)


def test_fake_device_returns_channels_1_and_5():
    assert [s.channel for s in protocol.parse(FakeDevice().read_packet())] == [1, 5]
