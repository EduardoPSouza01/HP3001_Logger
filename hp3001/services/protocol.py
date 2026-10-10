"""Decodificacao do pacote do HP-3000/HP-3001 (baseado em weewx-hp3000, Matthew Wall).

Requisicao: 7B 03 40 7D + zeros (64 bytes).
Resposta:   7B, depois 8 canais x 3 bytes (temp_hi, temp_lo, umidade), ... 40 7D.
Temperatura = inteiro de 16 bits (big-endian, com sinal) / 10. Canal ausente: 7F FF / FF.
"""
from dataclasses import dataclass
from typing import List, Optional

START = 0x7B
END = (0x40, 0x7D)
CMD_CURRENT = 0x03
CHANNELS = 8


@dataclass
class Sample:
    channel: int
    temperature_c: Optional[float]
    humidity: Optional[int]


def build_request(command: int = CMD_CURRENT) -> bytes:
    return bytes([START, command, 0x40, 0x7D]) + bytes(60)


def trim(buf) -> bytes:
    buf = bytes(buf)
    for i in range(1, len(buf)):
        if buf[i] == END[1] and buf[i - 1] == END[0]:
            return buf[: i + 1]
    return buf


def parse(buf) -> List[Sample]:
    buf = trim(buf)
    if len(buf) < 1 + CHANNELS * 3 + 2 or buf[0] != START:
        raise ValueError("pacote invalido: " + buf.hex(" "))
    body = buf[1 : 1 + CHANNELS * 3]
    if not any(body):
        raise ValueError("pacote de calibracao (tudo zero), ignorado")
    samples = []
    for ch in range(CHANNELS):
        hi, lo, hum = body[ch * 3 : ch * 3 + 3]
        raw = int.from_bytes(bytes([hi, lo]), "big", signed=True)
        if raw == 0x7FFF or hum == 0xFF:
            continue
        samples.append(Sample(ch + 1, raw / 10.0, hum))
    return samples
