# Source-to-Device Routing

This enhancement adds optional routing rules to photocastd, allowing you to map specific source folders to specific Chromecast devices.

## Configuration

Add a `routing` section to `config.yaml`:

```yaml
routing:
  "/mnt/nas/Family": ["Living Room"]
  "/mnt/nas/Personal": ["Bedroom"]
  "/mnt/nas/Events": ["Living Room", "Bedroom"]
```

## Behavior

- **If a source path matches a routing rule:** Cast to only those devices
- **If a source path has no rule:** Cast to all configured devices (backward compatible)
- **Partial path matching:** Uses longest-prefix match (e.g., `/mnt/nas/Family/2025` matches `/mnt/nas/Family`)

## Implementation

The routing logic is applied in `app.py` at cast time:
1. Load routing table from config
2. For each playback request, check if source path has a routing rule
3. Filter device list accordingly
4. Proceed with normal casting to selected devices

All existing features (image rendering, playlists, S3/WebDAV, API) remain unchanged.
