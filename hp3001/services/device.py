"""Acesso USB ao equipamento (VID 0x0483, PID 0x5750).

No Windows o equipamento e um dispositivo HID, entao o backend 'hid' funciona
sem trocar driver. O backend 'usb' (pyusb/libusb) fica como alternativa.
"""
import random
import time
from typing import List

from . import protocol

VID, PID = 0x0483, 0x5750
FAKE_CHANNELS = (1, 5)


class HidDevice:
    def __init__(self):
        import hid

        self._dev = hid.device()
        self._dev.open(VID, PID)

    def read_packet(self) -> bytes:
        # O primeiro byte e o report id (0)
        self._dev.write(b"\x00" + protocol.build_request())
        data = self._dev.read(64, 2000)
        if not data:
            raise IOError("sem resposta do equipamento")
        return bytes(data)

    def close(self):
        self._dev.close()


class UsbDevice:
    def __init__(self):
        import usb.core

        self._dev = usb.core.find(idVendor=VID, idProduct=PID)
        if self._dev is None:
            raise IOError("equipamento nao encontrado")
        try:
            if self._dev.is_kernel_driver_active(0):
                self._dev.detach_kernel_driver(0)
        except NotImplementedError:
            pass
        self._dev.set_configuration()
        self._dev.ctrl_transfer(0, 9, 1, 0, None)

    def read_packet(self) -> bytes:
        self._dev.write(0x01, protocol.build_request(), 100)
        return bytes(self._dev.read(0x82, 64, 1000))

    def close(self):
        import usb.util

        usb.util.dispose_resources(self._dev)


class FakeDevice:
    """Gera dados falsos (canais 1 e 5) para testar sem o equipamento."""

    def read_packet(self) -> bytes:
        body = bytearray()
        for ch in range(1, protocol.CHANNELS + 1):
            if ch in FAKE_CHANNELS:
                t = int((20 + random.random() * 6) * 10)
                body += t.to_bytes(2, "big") + bytes([random.randint(40, 70)])
            else:
                body += b"\x7f\xff\xff"
        return bytes([protocol.START]) + bytes(body) + b"\x40\x7d"

    def close(self):
        pass


def open_device(backend: str = "hid"):
    if backend == "fake":
        return FakeDevice()
    return UsbDevice() if backend == "usb" else HidDevice()


def read_with_retry(dev, tries: int = 3, delay: float = 1.0) -> List[protocol.Sample]:
    last = None
    for i in range(tries):
        try:
            return protocol.parse(dev.read_packet())
        except (ValueError, IOError) as e:
            last = e
            if i < tries - 1:
                time.sleep(delay)
    raise last
