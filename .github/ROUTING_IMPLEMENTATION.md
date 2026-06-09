# Implementation Notes: Source Routing

## Code Changes Required

### 1. config.yaml
Add optional `routing` section with source paths → device list mapping.

### 2. app.py
In the cast logic (around line 300-350), add device filtering:

```python
def get_target_devices(source_path, all_devices, routing_table):
    """Filter devices based on source routing rules."""
    if not routing_table:
        return all_devices
    
    # Find longest matching prefix
    matching_routes = [k for k in routing_table.keys() if source_path.startswith(k)]
    if matching_routes:
        best_match = max(matching_routes, key=len)
        return routing_table[best_match]
    
    # No routing rule — use all devices
    return all_devices
```

Call this in the cast handler before creating cast threads.

## Backward Compatibility

- Empty or missing `routing` section → cast to all devices
- No config changes required for existing users
- All existing API endpoints unchanged

## Testing

1. Start photocastd without routing config → should work as before
2. Add routing rules → verify only targeted devices receive casts
3. Mixed sources (some routed, some not) → routed use rules, others use all devices
