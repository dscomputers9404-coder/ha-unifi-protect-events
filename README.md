# UniFi Protect Events

A Home Assistant custom integration that exposes recent **UniFi Protect** events as camera entities with snapshots and event metadata.

> This project is an independent community integration and is not affiliated with or endorsed by Ubiquiti Inc. or Home Assistant.

## Features

- Local connection to the UniFi Protect Integration API using an API key.
- WebSocket-based local push event feed.
- Eight recent detection camera entities with JPEG snapshots.
- Event metadata including event type, camera name, timestamp, confidence and zones when available.
- Smart-detection prioritization: `person`, `vehicle`, `animal`, `package`, `face` and `licensePlate` replace nearby generic `motion` events from the same camera.
- A 5-second merge window to reduce duplicate motion/smart-detection thumbnails.
- High-quality snapshot request with automatic fallback when a camera returns HTTP 400.
- Persistent recent detections and snapshots across Home Assistant restarts.
- UI-based configuration through **Settings → Devices & services**.

## Requirements

- Home Assistant 2026.7.0 or newer.
- A UniFi console running Protect with the local Integration API available.
- A local API key with access to Protect.
- Network access from Home Assistant to the UniFi console.

## Installation with HACS

### Custom repository

Until this repository is included in the default HACS catalog:

1. Open **HACS**.
2. Open the menu in the top-right corner and choose **Custom repositories**.
3. Add the GitHub repository URL.
4. Select **Integration** as the repository type.
5. Download **UniFi Protect Events**.
6. Restart Home Assistant.

Then go to **Settings → Devices & services → Add integration** and search for **UniFi Protect Events**.

## Manual installation

Copy:

```text
custom_components/unifi_protect_events/
```

to:

```text
/config/custom_components/unifi_protect_events/
```

Restart Home Assistant and add the integration from **Settings → Devices & services**.

## Configuration

The setup dialog asks for:

- **IP address or hostname** — for example `192.168.x.x` or `unifi-console.local`.
- **API key** — a local UniFi API key.
- **Verify SSL certificate** — enable this only when the UniFi console certificate can be validated by Home Assistant.

The integration uses the local Protect endpoints under `/proxy/protect/integration/v1`.

## Entities

The integration creates:

- `Detection 1` through `Detection 8` camera entities, where `Detection 1` is the newest event.
- `Recent detections` sensor.
- `Detection` event entity.

Each detection camera can expose attributes such as:

```text
event_id
event_type
camera_id
camera_name
timestamp
confidence
zones
has_snapshot
```

### Upgrade note for versions before 0.2.5

Existing Home Assistant entity registry entries keep their entity IDs. If your current dashboard uses IDs such as:

```text
camera.home_unifi_protect_events_detectie_1
```

they should remain valid after upgrading. New installations use English friendly names and may generate English-based entity IDs such as `..._detection_1`.

## Event prioritization

UniFi Protect can emit a generic `motion` event and a classified event for the same activity. This integration applies the following rules within a 5-second window for the same camera:

1. If `motion` arrives first and a smart detection follows, the smart detection replaces the motion item.
2. If a smart detection is already present and `motion` arrives afterwards, the motion item is ignored.
3. Different smart detections are kept as separate events.

Smart detection types currently include:

```text
person
vehicle
animal
package
face
licensePlate
```

## Persistence

The eight most recent detection events and their snapshots are stored with Home Assistant's storage helper. After a Home Assistant restart, these thumbnails are restored automatically.

Only the recent camera slots are persisted to keep storage usage limited.

## Dashboard example

The recent detection camera entities work with standard Home Assistant picture cards. Example:

```yaml
- type: picture-entity
  entity: camera.home_unifi_protect_events_detection_1
  camera_view: auto
  show_name: false
  show_state: false
  aspect_ratio: "1.6:1"
  fit_mode: cover
  tap_action:
    action: more-info
```

Entity IDs can differ depending on the Home Assistant entity registry and upgrade history. Always check **Developer tools → States** for the actual ID.

## Known limitations

- Event parsing depends on the event payloads exposed by the local UniFi Protect Integration API and may need updates when Protect changes its payload format.
- The integration stores snapshots from the time the event is received; it does not currently request historical event thumbnails by event ID.
- Generic motion may still be shown when Protect does not send a classified smart detection within the merge window.
- Persistent snapshots consume Home Assistant `.storage` space, although only the eight recent slots are stored.

## Troubleshooting

### Detection cameras are unavailable after first installation

Recent detection slots are empty until Protect sends events. Walk in front of a camera or trigger another enabled event and the newest slot should populate.

### Snapshots do not appear

Verify that Home Assistant can reach the UniFi console and that the API key has access to Protect. The integration automatically retries a normal-quality snapshot when a high-quality request returns HTTP 400.

### Duplicate MOTION and PERSON/VEHICLE events

The integration merges generic motion with a nearby smart detection for the same camera within five seconds. If duplicates occur outside that interval, open an issue with sanitized event timing details.

## Updating

When installed through HACS, use HACS to update the integration and restart Home Assistant afterwards.

For manual installations, replace the files inside `custom_components/unifi_protect_events/` and restart Home Assistant.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT. See [LICENSE](LICENSE).
