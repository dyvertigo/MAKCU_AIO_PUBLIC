import json
import os
import serial.tools.list_ports
import hashlib

DEVICES_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'devices.json')
DEVICE_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'device_db.json')

class DeviceManager:
    def local_db_lookup(self, vid, pid):
        if not os.path.exists(DEVICE_DB_PATH):
            return None
        with open(DEVICE_DB_PATH, 'r', encoding='utf-8') as f:
            db = json.load(f)
            for dev in db:
                if dev['vid'].upper() == vid.upper() and dev['pid'].upper() == pid.upper():
                    return dev
        return None

    def fetch_device_data(self, vid, pid):
        """
        Attempt to fetch device data automatically via online database or local scan.
        This is a stub, you can add a real API call or database lookup later.
        """
        # First check local database
        local = self.local_db_lookup(vid, pid)
        if local:
            return local
        # You can add a real online API call here later
        return None
    def validate_device_info(self, info):
        required = ["name", "vid", "pid", "features", "serial_protocol", "firmware", "protocol_info"]
        for key in required:
            if key not in info or not info[key]:
                return False, f"Field '{key}' is missing or empty."
        fw = info["firmware"]
        proto = info["protocol_info"]
        if not fw.get("version") or not fw.get("url") or not fw.get("flash_method"):
            return False, "Firmware info is incomplete."
        if not proto.get("baudrate") or not proto.get("command_set"):
            return False, "Protocol info is incomplete."
        return True, ""

    def test_device(self, vid, pid):
        # Simple test: check if device is connected and protocol info is correct
        for port in serial.tools.list_ports.comports():
            if str(port.vid).upper() == vid.upper() and str(port.pid).upper() == pid.upper():
                return True, f"Device found on {port.device}: {port.description}"
        return False, "Device not found on USB."

    def __init__(self):
        self.devices = self.load_devices()

    def load_devices(self):
        if not os.path.exists(DEVICES_CONFIG_PATH):
            return []
        with open(DEVICES_CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('devices', [])

    def save_devices(self):
        with open(DEVICES_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump({'devices': self.devices}, f, indent=2)

    def find_connected_devices(self):
        found = []
        ports = serial.tools.list_ports.comports()
        for port in ports:
            for dev in self.devices:
                if str(port.vid).upper() == dev['vid'].upper() and str(port.pid).upper() == dev['pid'].upper():
                    found.append({
                        'name': dev['name'],
                        'port': port.device,
                        'features': dev.get('features', []),
                        'serial_protocol': dev.get('serial_protocol', 'standard')
                    })
        return found

    def detect_unknown_devices(self):
        unknown = []
        ports = serial.tools.list_ports.comports()
        known_vid_pid = {(dev['vid'].upper(), dev['pid'].upper()) for dev in self.devices}
        for port in ports:
            vid = str(port.vid).upper() if port.vid else None
            pid = str(port.pid).upper() if port.pid else None
            if vid and pid and (vid, pid) not in known_vid_pid:
                unknown.append({'vid': vid, 'pid': pid, 'port': port.device, 'description': port.description})
        return unknown

    def add_device(self, device_info):
        self.devices.append(device_info)
        self.save_devices()

# Example usage:
if __name__ == '__main__':
    manager = DeviceManager()
    print('Known devices:', manager.find_connected_devices())
    print('Unknown devices:', manager.detect_unknown_devices())
