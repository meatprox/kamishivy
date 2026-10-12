from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Callable

try:
    import serial
    from serial.serialutil import SerialException
except ImportError:  # pragma: no cover
    serial = None
    SerialException = Exception


MAX_CHANNELS = 10
RAW_CHANNEL = 10
RAW_CHANNEL_NAME = "comA"
DEFAULT_RAW_LENGTH = 8
MAX_RAW_LENGTH = 4096
DEFAULT_RECV_WAIT = 1.0
MAX_RECV_WAIT = 30.0
REALTIME_POLL = 0.05
DEFAULT_RECV_RETRIES = 0
MAX_RECV_RETRIES = 20
DEFAULT_ENCODING = "UTF-8"
ENCODING_CHOICES = ("UTF-8", "ASCII", "シフトJIS", "EUC", "UNICODE")

_ENCODING_CODECS = {
    "utf-8": "utf-8",
    "utf8": "utf-8",
    "ascii": "ascii",
    "シフトjis": "cp932",
    "shift-jis": "cp932",
    "shiftjis": "cp932",
    "sjis": "cp932",
    "cp932": "cp932",
    "euc": "euc_jp",
    "euc-jp": "euc_jp",
    "eucjp": "euc_jp",
    "unicode": "utf-16-le",
    "utf-16": "utf-16-le",
    "utf-16le": "utf-16-le",
    "utf-16-le": "utf-16-le",
}
_CODEC_LABELS = {
    "utf-8": "UTF-8",
    "ascii": "ASCII",
    "cp932": "シフトJIS",
    "shift_jis": "シフトJIS",
    "euc_jp": "EUC",
    "utf-16-le": "UNICODE",
    "utf-16": "UNICODE",
}


def list_com_ports() -> list[str]:
    ports: list[str] = []
    if serial is not None:
        try:
            from serial.tools import list_ports
        except ImportError:
            list_ports = None
        if list_ports is not None:
            for item in list_ports.comports():
                device = (item.device or "").strip()
                if device:
                    ports.append(device)
    try:
        import winreg
    except ImportError:
        winreg = None
    if winreg is not None:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
        except OSError:
            key = None
        if key is not None:
            try:
                index = 0
                while True:
                    try:
                        _name, value, _typ = winreg.EnumValue(key, index)
                    except OSError:
                        break
                    text = str(value).strip()
                    if text:
                        ports.append(text)
                    index += 1
            finally:
                winreg.CloseKey(key)
    return sorted(set(ports), key=_com_sort_key)


def _com_sort_key(name: str) -> tuple[str, int]:
    digits = ""
    prefix = name
    for index, char in enumerate(reversed(name)):
        if char.isdigit():
            digits = char + digits
            prefix = name[: len(name) - index - 1]
        else:
            break
    number = int(digits) if digits else 0
    return (prefix.lower(), number)


def parse_line(line: str) -> dict[str, str]:
    values: dict[str, str] = {}
    text = line.strip()
    if not text:
        return values

    if "=" in text or ":" in text:
        chunks = [chunk.strip() for chunk in text.split(",") if chunk.strip()]
        for chunk in chunks:
            sep = "=" if "=" in chunk else ":" if ":" in chunk else ""
            if not sep:
                continue
            key, value = chunk.split(sep, 1)
            values[key.strip()] = value.strip()
        if values:
            return values

    parts = [part.strip() for part in text.split(",") if part.strip()]
    if len(parts) > 1:
        for index, part in enumerate(parts):
            values[f"v{index}"] = part
        return values

    values["value"] = text
    return values


def _encoding_key(value: str) -> str:
    return value.strip().lower().replace(" ", "").replace("_", "-")


def encoding_codec(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        return "utf-8"
    return _ENCODING_CODECS.get(_encoding_key(text), "utf-8")


def encoding_label(value: str | None) -> str:
    return _CODEC_LABELS.get(encoding_codec(value), DEFAULT_ENCODING)


def decode_bytes(raw: bytes, encoding: str | None) -> str:
    codec = encoding_codec(encoding)
    try:
        return raw.decode(codec, errors="replace")
    except Exception:
        return raw.decode("utf-8", errors="replace")


def channel_label(number: int) -> str:
    if int(number) == RAW_CHANNEL:
        return RAW_CHANNEL_NAME
    return str(number)


def resolve_channel(number: Any) -> int:
    if isinstance(number, str):
        text = number.strip()
        key = text.lower().replace("_", "").replace("-", "")
        if key in {"a", "coma", "10"}:
            return RAW_CHANNEL
        try:
            value = int(text)
        except ValueError:
            return 0
        return value if 1 <= value <= MAX_CHANNELS else 0
    try:
        value = int(number)
    except (TypeError, ValueError):
        return 0
    return value if 1 <= value <= MAX_CHANNELS else 0


def clamp_raw_length(value: int | None, fallback: int = DEFAULT_RAW_LENGTH) -> int:
    try:
        number = int(value) if value is not None else fallback
    except (TypeError, ValueError):
        number = fallback
    return min(MAX_RAW_LENGTH, max(1, number))


def clamp_recv_wait(value: Any, fallback: float = DEFAULT_RECV_WAIT) -> float:
    try:
        wait = float(value if value is not None and str(value).strip() != "" else fallback)
    except (TypeError, ValueError):
        wait = fallback
    if wait < 0:
        wait = 0.0
    return min(MAX_RECV_WAIT, wait)


def clamp_recv_retries(value: Any, fallback: int = DEFAULT_RECV_RETRIES) -> int:
    try:
        retries = int(float(value if value is not None and str(value).strip() != "" else fallback))
    except (TypeError, ValueError):
        retries = fallback
    return min(MAX_RECV_RETRIES, max(0, retries))


def serial_read_timeout(wait: float) -> float:
    """待ち時間0は待たずに次を見る（リアルタイム向き）。"""
    if wait <= 0:
        return REALTIME_POLL
    return wait


def extract_number(payload: dict[str, Any] | None) -> str | None:
    if not payload:
        return None
    candidates: list[Any] = []
    values = payload.get("values") or {}
    if "value" in values:
        candidates.append(values["value"])
    candidates.extend(values.values())
    candidates.append(payload.get("raw"))
    for item in candidates:
        if item is None:
            continue
        text = str(item).strip()
        if not text:
            continue
        try:
            number = float(text)
        except ValueError:
            continue
        if number.is_integer():
            return str(int(number))
        return str(number)
    raw = str(payload.get("raw") or "").strip()
    return raw or None


class SerialService:
    def __init__(self, on_data: Callable[[dict[str, Any]], None] | None = None) -> None:
        self._on_data = on_data
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._port = None
        self.port_name = ""
        self._read_bytes: int | None = None
        self._encoding = "utf-8"
        self._eol: str | None = None
        self._wait = DEFAULT_RECV_WAIT
        self._retries = DEFAULT_RECV_RETRIES
        self._latest: dict[str, Any] | None = None
        self.connected = False
        self.last_error = ""

    def set_callback(self, on_data: Callable[[dict[str, Any]], None] | None) -> None:
        self._on_data = on_data

    def latest(self) -> dict[str, Any] | None:
        with self._lock:
            if self._latest is None:
                return None
            return dict(self._latest)

    def connect(
        self,
        port: str,
        baudrate: int,
        timeout: float = 1.0,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: float = 1,
        read_bytes: int | None = None,
        encoding: str = DEFAULT_ENCODING,
        retries: int = DEFAULT_RECV_RETRIES,
    ) -> None:
        if serial is None:
            raise RuntimeError("pyserial がインストールされていません。pip install pyserial を実行してください。")
        self.disconnect()
        self._wait = clamp_recv_wait(timeout)
        self._retries = clamp_recv_retries(retries)
        try:
            self._port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
                timeout=serial_read_timeout(self._wait),
            )
        except SerialException as exc:
            self.last_error = str(exc)
            self.connected = False
            raise

        self.last_error = ""
        self.connected = True
        self.port_name = port
        self._read_bytes = clamp_raw_length(read_bytes) if read_bytes else None
        self._encoding = encoding_codec(encoding)
        self._stop.clear()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def disconnect(self) -> None:
        self._stop.set()
        port = self._port
        if port is not None:
            try:
                port.close()
            except Exception:
                pass
        thread = self._thread
        if thread is not None:
            thread.join(timeout=1.0)
        self._thread = None
        self._port = None
        self.port_name = ""
        self._read_bytes = None
        self._encoding = "utf-8"
        self._eol = None
        self._wait = DEFAULT_RECV_WAIT
        self._retries = DEFAULT_RECV_RETRIES
        self.connected = False

    def set_eol(self, eol: str | None) -> None:
        text = str(eol or "")
        self._eol = text if text else None

    def write(self, data: str, flush_input: bool = False) -> bool:
        port = self._port
        if port is None or not self.connected:
            return False
        try:
            if flush_input:
                try:
                    port.reset_input_buffer()
                except Exception:
                    pass
            raw = str(data).encode(self._encoding, errors="replace")
            port.write(raw)
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def _read_loop(self) -> None:
        assert self._port is not None
        buf = bytearray()
        empty_tries = 0
        while not self._stop.is_set():
            try:
                if self._read_bytes:
                    need = self._read_bytes - len(buf)
                    raw = self._port.read(need) if need > 0 else b""
                else:
                    eol = self._eol
                    if eol:
                        raw = self._port.read_until(eol.encode(self._encoding, errors="replace"))
                    else:
                        raw = self._port.readline()
                    if raw and self._encoding.startswith("utf-16") and raw.endswith(b"\n"):
                        extra = self._port.read(1)
                        if extra == b"\x00":
                            raw += extra
            except Exception as exc:
                if self._stop.is_set():
                    break
                self.last_error = str(exc)
                self.connected = False
                break
            if raw:
                empty_tries = 0
                if self._read_bytes:
                    buf.extend(raw)
                    if len(buf) < self._read_bytes:
                        continue
                    packet = bytes(buf[: self._read_bytes])
                    del buf[: self._read_bytes]
                    self._emit(packet, mode="raw")
                else:
                    self._emit(raw, mode="line")
                continue
            empty_tries += 1
            waiting = bool(buf) or self._wait > 0
            if waiting and empty_tries <= self._retries:
                continue
            empty_tries = 0
            if buf:
                buf.clear()

    def _emit(self, raw: bytes, mode: str) -> None:
        text = decode_bytes(raw, self._encoding)
        if mode == "line":
            text = text.strip()
            if not text:
                return
            values = parse_line(text)
        else:
            values = {"value": text}
        payload = {
            "raw": text,
            "values": values,
            "time": datetime.now().isoformat(timespec="seconds"),
            "mode": mode,
        }
        with self._lock:
            self._latest = payload
        callback = self._on_data
        if callback is not None:
            callback(payload)


class ChannelHub:
    """COM をデータ番号 1〜N に割り当て、UI には番号付きの値だけを渡す。"""

    def __init__(self, on_data: Callable[[int, dict[str, Any]], None] | None = None) -> None:
        self._on_data = on_data
        self._lock = threading.Lock()
        self._services: dict[int, SerialService] = {}
        self._latest: dict[int, dict[str, Any]] = {}
        self._eol: dict[int, str] = {}
        self.last_errors: dict[int, str] = {}

    @property
    def connected(self) -> bool:
        return any(service.connected for service in self._services.values())

    def connect(
        self,
        ports: dict[int, str],
        options: dict[str, Any],
        baudrates: dict[str, int] | None = None,
        encodings: dict[str, str] | None = None,
        timeouts: dict[str, float] | None = None,
        retries: dict[str, int] | None = None,
        raw_length: int = DEFAULT_RAW_LENGTH,
    ) -> dict[int, str]:
        self.disconnect()
        errors: dict[int, str] = {}
        baudrates = baudrates or {}
        encodings = encodings or {}
        timeouts = timeouts or {}
        retries = retries or {}
        lowered = {name.lower(): rate for name, rate in baudrates.items()}
        enc_lowered = {name.lower(): label for name, label in encodings.items()}
        wait_lowered = {name.lower(): wait for name, wait in timeouts.items()}
        retry_lowered = {name.lower(): count for name, count in retries.items()}
        chunk = clamp_raw_length(raw_length)
        for number, port in sorted(ports.items()):
            service = SerialService(on_data=self._make_callback(number))
            opts = dict(options)
            if port in baudrates:
                opts["baudrate"] = int(baudrates[port])
            elif port.lower() in lowered:
                opts["baudrate"] = int(lowered[port.lower()])
            if port in encodings:
                opts["encoding"] = encoding_codec(encodings[port])
            elif port.lower() in enc_lowered:
                opts["encoding"] = encoding_codec(enc_lowered[port.lower()])
            else:
                opts["encoding"] = encoding_codec(DEFAULT_ENCODING)
            if port in timeouts:
                opts["timeout"] = clamp_recv_wait(timeouts[port])
            elif port.lower() in wait_lowered:
                opts["timeout"] = clamp_recv_wait(wait_lowered[port.lower()])
            if port in retries:
                opts["retries"] = clamp_recv_retries(retries[port])
            elif port.lower() in retry_lowered:
                opts["retries"] = clamp_recv_retries(retry_lowered[port.lower()])
            if number == RAW_CHANNEL:
                opts["read_bytes"] = chunk
            try:
                service.connect(port=port, **opts)
            except Exception as exc:
                errors[number] = f"{port}: {exc}"
                continue
            ending = self._eol.get(number)
            if ending:
                service.set_eol(ending)
            self._services[number] = service
        self.last_errors = errors
        return errors

    def disconnect(self) -> None:
        for service in self._services.values():
            service.disconnect()
        self._services.clear()
        self.last_errors = {}

    def payload(self, number: int) -> dict[str, Any] | None:
        with self._lock:
            data = self._latest.get(number)
            return dict(data) if data is not None else None

    def send(self, number: int | str, data: str, flush_input: bool = False) -> bool:
        channel = resolve_channel(number)
        if channel < 1:
            return False
        service = self._services.get(channel)
        if service is None or not service.connected:
            return False
        return service.write(data, flush_input=flush_input)

    def set_eol(self, number: int | str, eol: str) -> None:
        channel = resolve_channel(number)
        if channel < 1:
            return
        text = str(eol or "")
        if not text:
            self._eol.pop(channel, None)
            service = self._services.get(channel)
            if service is not None:
                service.set_eol(None)
            return
        self._eol[channel] = text
        service = self._services.get(channel)
        if service is not None:
            service.set_eol(text)

    def raw(self, number: int | str) -> str | None:
        channel = resolve_channel(number)
        if channel < 1:
            return None
        payload = self.payload(channel)
        if not payload:
            return None
        raw = payload.get("raw")
        return None if raw is None else str(raw)

    def get_data(self, number: int | str) -> str | None:
        channel = resolve_channel(number)
        if channel < 1:
            return None
        payload = self.payload(channel)
        if channel == RAW_CHANNEL:
            if not payload:
                return None
            raw = payload.get("raw")
            return None if raw is None else str(raw)
        return extract_number(payload)

    def assigned_ports(self) -> dict[int, str]:
        return {
            number: service.port_name
            for number, service in self._services.items()
            if service.connected and service.port_name
        }

    def port_health(self) -> dict[str, str]:
        health: dict[str, str] = {}
        for service in self._services.values():
            if not service.port_name:
                continue
            health[service.port_name] = "on" if service.connected else "error"
        return health

    def get_all_data(self) -> dict[int, str | None]:
        numbers = set(self._services.keys())
        with self._lock:
            numbers.update(self._latest.keys())
        return {number: self.get_data(number) for number in sorted(numbers)}

    def _make_callback(self, number: int) -> Callable[[dict[str, Any]], None]:
        def _callback(payload: dict[str, Any]) -> None:
            with self._lock:
                self._latest[number] = payload
            if self._on_data is not None:
                self._on_data(number, payload)

        return _callback
