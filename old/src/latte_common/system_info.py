"""Read-only CPU-Z/HWiNFO style facts and live sensor values."""
import os
import re
import time


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as stream:
            return stream.read().strip()
    except OSError:
        return ""


def cpu_info(root="/proc"):
    fields = {}
    processors = 0
    for line in read(os.path.join(root, "cpuinfo")).splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            continue
        key = key.strip()
        if key == "processor":
            processors += 1
        elif key not in fields:
            fields[key] = value.strip()
    return {
        "model": fields.get("model name", fields.get("Hardware", "Neznámy procesor")),
        "vendor": fields.get("vendor_id", fields.get("CPU implementer", "Neznámy výrobca")),
        "architecture": fields.get("Architecture", ""),
        "cores": processors,
        "threads": processors,
        "frequency": fields.get("cpu MHz", ""),
        "cache": fields.get("cache size", ""),
        "flags": fields.get("flags", fields.get("Features", "")).split(),
    }


def memory_info(root="/proc"):
    values = {}
    for line in read(os.path.join(root, "meminfo")).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            parts = value.split()
            if parts:
                try:
                    values[key] = int(parts[0]) * (1024 if len(parts) > 1 and parts[1].lower() == "kb" else 1)
                except ValueError:
                    pass
    return values


def sensors(sys_root="/sys"):
    """Najde teploty a otacky dostupne cez hwmon bez vyvolania privilegovaneho skenu."""
    result = []
    base = os.path.join(sys_root, "class", "hwmon")
    try:
        devices = sorted(os.listdir(base))
    except OSError:
        return result
    for device in devices:
        directory = os.path.join(base, device)
        try:
            names = os.listdir(directory)
        except OSError:
            continue
        for name in names:
            match = re.match(r"(temp|fan|power)(\d+)_(input|label)$", name)
            if not match or match.group(3) != "input":
                continue
            value = read(os.path.join(directory, name))
            if not value:
                continue
            try:
                number = float(value)
            except ValueError:
                continue
            kind = match.group(1)
            if kind == "temp":
                number /= 1000
                unit = "°C"
            elif kind == "power":
                number /= 1000000
                unit = "W"
            else:
                unit = "RPM"
            label = read(os.path.join(directory, "%s%s_label" % (kind, match.group(2)))) or device
            result.append({"name": label, "kind": kind, "value": number, "unit": unit})
    return result


def thermal_zones(sys_root="/sys"):
    result = []
    base = os.path.join(sys_root, "class", "thermal")
    try:
        zones = sorted(name for name in os.listdir(base) if name.startswith("thermal_zone"))
    except OSError:
        return result
    for zone in zones:
        directory = os.path.join(base, zone)
        value = read(os.path.join(directory, "temp"))
        if not value:
            continue
        try:
            result.append({"name": read(os.path.join(directory, "type")) or zone,
                           "kind": "temp", "value": float(value) / 1000, "unit": "°C"})
        except ValueError:
            pass
    return result


def _counter_lines(path):
    result = {}
    for line in read(path).splitlines():
        fields = line.split()
        if fields:
            result[fields[0]] = fields[1:]
    return result


class TelemetrySampler:
    """Read-only interval telemetry for disks, network and DRM GPU engines."""

    def __init__(self, proc_root="/proc", sys_root="/sys", clock=time.monotonic):
        self.proc_root = proc_root
        self.sys_root = sys_root
        self.clock = clock
        self.previous = None

    def read(self):
        now = self.clock()
        disks = self._disks()
        network = self._network()
        elapsed = now - self.previous[0] if self.previous else 0
        if elapsed <= 0:
            elapsed = 1
        if self.previous:
            old_disks, old_network = self.previous[1], self.previous[2]
            for name, value in disks.items():
                old = old_disks.get(name, (0, 0))
                value["read_bytes_sec"] = max(0, value["read_bytes"] - old[0]) / elapsed
                value["write_bytes_sec"] = max(0, value["write_bytes"] - old[1]) / elapsed
            for name, value in network.items():
                old = old_network.get(name, (0, 0))
                value["receive_bytes_sec"] = max(0, value["receive_bytes"] - old[0]) / elapsed
                value["send_bytes_sec"] = max(0, value["send_bytes"] - old[1]) / elapsed
        self.previous = (now,
                         {name: (item["read_bytes"], item["write_bytes"]) for name, item in disks.items()},
                         {name: (item["receive_bytes"], item["send_bytes"]) for name, item in network.items()})
        return {"disks": list(disks.values()), "network": list(network.values()), "gpu": self._gpu()}

    def _disks(self):
        result = {}
        for line in read(os.path.join(self.proc_root, "diskstats")).splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            name, fields = parts[2], parts[3:]
            if len(fields) < 7 or name.startswith(("loop", "ram", "zram", "fd")):
                continue
            try:
                result[name] = {"name": name, "read_bytes": int(fields[2]) * 512,
                                "write_bytes": int(fields[6]) * 512,
                                "read_bytes_sec": 0.0, "write_bytes_sec": 0.0}
            except ValueError:
                continue
        return result

    def _network(self):
        result = {}
        for line in read(os.path.join(self.proc_root, "net/dev")).splitlines():
            if ":" not in line:
                continue
            name, values = line.split(":", 1)
            fields = values.split()
            if len(fields) < 9 or name.strip() == "lo":
                continue
            try:
                result[name.strip()] = {"name": name.strip(), "receive_bytes": int(fields[0]),
                                        "send_bytes": int(fields[8]), "receive_bytes_sec": 0.0,
                                        "send_bytes_sec": 0.0}
            except ValueError:
                continue
        return result

    def _gpu(self):
        result = []
        base = os.path.join(self.sys_root, "class", "drm")
        try:
            names = sorted(os.listdir(base))
        except OSError:
            return result
        for name in names:
            if not re.match(r"card\d+$", name):
                continue
            directory = os.path.join(base, name, "device")
            busy = read(os.path.join(directory, "gpu_busy_percent"))
            if busy:
                try:
                    result.append({"name": name, "busy_percent": float(busy)})
                except ValueError:
                    pass
        return result
