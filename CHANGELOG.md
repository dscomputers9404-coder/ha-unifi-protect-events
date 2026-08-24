# Changelog

All notable changes to UniFi Protect Events are documented here.

## 0.2.5

- Prepared the repository structure and documentation for HACS distribution.
- Changed source/config-flow text and default friendly names to English.
- Added explicit English translations while retaining Dutch translations.
- Added HACS and Hassfest GitHub Action workflows.
- Added MIT license and expanded documentation.
- Kept entity unique IDs unchanged for upgrade compatibility.

## 0.2.4

- Persist the eight most recent detection events and JPEG snapshots using Home Assistant storage.
- Restore recent thumbnails automatically after a Home Assistant restart.

## 0.2.3

- Smart detections replace generic motion events from the same camera within a 5-second merge window.
- Generic motion is ignored when it arrives shortly after a smart detection from the same camera.

## 0.2.2

- Increased recent detection camera slots to eight.

## 0.2.1

- Added normal-quality snapshot fallback when high-quality snapshots return HTTP 400.

## 0.2.0

- Added recent detection camera entities with event snapshots.
