#!/usr/bin/env python3
import yaml
import os
from pathlib import Path
from pychromecast import Chromecast
import time

class PhotocastdRouter:
    """Route media sources to specific Chromecast devices."""
    
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.devices = {d['name']: d['host'] for d in self.config['devices']}
        self.routing = self.config.get('routing', {})
    
    def get_target_devices(self, source_name):
        """Get devices for a given source. If not in routing table, return all devices."""
        if source_name in self.routing:
            return self.routing[source_name]
        return list(self.devices.keys())
    
    def cast_to_device(self, device_name, media_path):
        """Cast media to a specific device."""
        if device_name not in self.devices:
            raise ValueError(f"Device '{device_name}' not found")
        
        host = self.devices[device_name]
        try:
            cast = Chromecast(host)
            cast.wait()
            # Cast logic here
            print(f"Casting {media_path} to {device_name}")
        except Exception as e:
            print(f"Error casting to {device_name}: {e}")
    
    def cast_source(self, source_name, media_path):
        """Cast media from a source to its configured devices."""
        targets = self.get_target_devices(source_name)
        for device in targets:
            self.cast_to_device(device, media_path)

if __name__ == "__main__":
    router = PhotocastdRouter()
    print("Photocastd routing enabled")
    print(f"Devices: {router.devices}")
    print(f"Routing table: {router.routing}")
