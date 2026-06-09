# Photocastd — Device Routing Enhancement

Selectively cast photos and videos to specific Chromecast devices based on source folder configuration.

## Features

- **Device routing:** Map source folders → target Chromecast devices
- **Backward compatible:** Sources without routing rules cast to all devices
- **YAML configuration:** Simple, readable routing table

## Configuration

Edit `config.yaml`:

```yaml
devices:
  - name: "Living Room"
    host: "192.168.1.100"
  - name: "Bedroom"
    host: "192.168.1.101"

routing:
  photos:
    - "Living Room"
  videos:
    - "Living Room"
    - "Bedroom"
```

Sources not in the routing table cast to **all devices**.

## Implementation

`PhotocastdRouter` class handles:
- Device discovery and lookup
- Routing table resolution
- Per-device casting

See `app.py` for details.
