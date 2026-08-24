import asyncio, json, logging
from datetime import UTC, datetime
from aiohttp import ClientError, ClientResponseError, WSServerHandshakeError

from .const import CAMERAS_PATH, EVENTS_WS_PATH, SUPPORTED_EVENT_TYPES
from .models import ProtectDetection

_LOGGER = logging.getLogger(__name__)

class ProtectApiError(Exception): pass
class ProtectAuthError(ProtectApiError): pass
class ProtectConnectionError(ProtectApiError): pass

class ProtectApiClient:
    def __init__(self, session, host, api_key, verify_ssl):
        self._session = session
        self._host = host.strip().rstrip("/")
        if not self._host.startswith(("http://", "https://")):
            self._host = f"https://{self._host}"
        self._api_key = api_key
        self._verify_ssl = verify_ssl
        self._cameras = {}
        self._stopped = False

    @property
    def headers(self):
        return {"X-API-Key": self._api_key, "Accept": "application/json"}

    def _ssl(self):
        return True if self._verify_ssl else False

    async def async_get_cameras(self):
        try:
            async with self._session.get(
                f"{self._host}{CAMERAS_PATH}",
                headers=self.headers, ssl=self._ssl(), timeout=15
            ) as response:
                if response.status in (401, 403):
                    raise ProtectAuthError("API key rejected")
                response.raise_for_status()
                payload = await response.json()
        except ProtectAuthError:
            raise
        except (ClientResponseError, ClientError, asyncio.TimeoutError) as err:
            raise ProtectConnectionError(str(err)) from err

        self._cameras = {
            str(x["id"]): str(x.get("name", x["id"]))
            for x in payload if isinstance(x, dict) and x.get("id")
        }
        return dict(self._cameras)

    async def async_get_snapshot(self, camera_id):
        headers = dict(self.headers)
        headers["Accept"] = "image/jpeg"

        # Not every Protect camera supports high-quality snapshots.
        # Try HQ first and fall back to a normal snapshot on HTTP 400.
        for high_quality in (True, False):
            quality = "true" if high_quality else "false"
            url = (
                f"{self._host}/proxy/protect/integration/v1/"
                f"cameras/{camera_id}/snapshot?highQuality={quality}"
            )

            try:
                async with self._session.get(
                    url, headers=headers, ssl=self._ssl(), timeout=15
                ) as response:
                    if response.status == 200:
                        return await response.read()

                    if response.status == 400 and high_quality:
                        _LOGGER.debug(
                            "HQ snapshot not supported for %s; trying normal snapshot",
                            camera_id,
                        )
                        continue

                    _LOGGER.warning(
                        "Snapshot HTTP %s for %s (highQuality=%s)",
                        response.status,
                        camera_id,
                        quality,
                    )
                    return None

            except (ClientError, asyncio.TimeoutError) as err:
                _LOGGER.warning("Snapshot failed for %s: %s", camera_id, err)
                return None

        return None

    async def async_listen(self, callback):
        self._stopped = False
        ws_url = self._host.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
        ws_url += EVENTS_WS_PATH
        delay = 2

        while not self._stopped:
            try:
                async with self._session.ws_connect(
                    ws_url, headers=self.headers, ssl=self._ssl(),
                    heartbeat=30, receive_timeout=90
                ) as websocket:
                    _LOGGER.info("Connected to UniFi Protect event feed")
                    delay = 2
                    async for message in websocket:
                        if self._stopped:
                            break
                        if message.type.name == "TEXT":
                            detection = self._parse_event(message.data)
                            if detection:
                                if detection.camera_id:
                                    detection.snapshot = await self.async_get_snapshot(
                                        detection.camera_id
                                    )
                                await callback(detection)
                        elif message.type.name in {"CLOSE", "CLOSED", "ERROR"}:
                            break
            except WSServerHandshakeError as err:
                _LOGGER.error("WebSocket handshake failed: %s", err)
                return
            except (ClientError, asyncio.TimeoutError, OSError) as err:
                _LOGGER.warning("Event feed disconnected (%s); retrying in %ss", err, delay)

            if not self._stopped:
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)

    def stop(self):
        self._stopped = True

    def _parse_event(self, raw):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return None
        item = payload.get("item")
        if not isinstance(item, dict):
            return None

        event_type = self._extract_event_type(item)
        if not event_type:
            return None

        event_id = str(item.get("id") or item.get("eventId") or
                       f"{event_type}-{int(datetime.now(tz=UTC).timestamp()*1000)}")
        camera_id = self._extract_camera_id(item)

        return ProtectDetection(
            event_id=event_id,
            event_type=event_type,
            camera_id=camera_id,
            camera_name=self._cameras.get(camera_id) if camera_id else None,
            timestamp=self._extract_timestamp(item),
            confidence=self._extract_confidence(item),
            zones=self._extract_zones(item),
            raw=payload,
        )

    @staticmethod
    def _extract_event_type(item):
        candidates = [
            item.get("type"), item.get("eventType"),
            item.get("smartDetectType"), item.get("objectType")
        ]
        if isinstance(item.get("smartDetectTypes"), list):
            candidates.extend(item["smartDetectTypes"])
        attrs = item.get("attributes")
        if isinstance(attrs, dict):
            candidates.extend([attrs.get("objectType"), attrs.get("type")])

        preferred = {"person","vehicle","animal","package","face","licensePlate","ring","motion"}
        for value in candidates:
            if isinstance(value, str) and value in preferred:
                return value
        for value in candidates:
            if isinstance(value, str) and value in SUPPORTED_EVENT_TYPES:
                return value
        return None

    @staticmethod
    def _extract_camera_id(item):
        for key in ("camera", "cameraId", "device", "deviceId"):
            value = item.get(key)
            if isinstance(value, str) and value:
                return value
            if isinstance(value, dict) and value.get("id"):
                return str(value["id"])
        return None

    @staticmethod
    def _extract_timestamp(item):
        for key in ("start","timestamp","clockBestWall","clock_best_wall","createdAt"):
            value = item.get(key)
            if isinstance(value, (int,float)):
                seconds = value/1000 if value > 10_000_000_000 else value
                return datetime.fromtimestamp(seconds, tz=UTC)
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace("Z","+00:00"))
                except ValueError:
                    pass
        return datetime.now(tz=UTC)

    @staticmethod
    def _extract_confidence(item):
        if isinstance(item.get("confidence"), (int,float)):
            return item["confidence"]
        attrs = item.get("attributes")
        if isinstance(attrs, dict) and isinstance(attrs.get("confidence"), (int,float)):
            return attrs["confidence"]
        return None

    @staticmethod
    def _extract_zones(item):
        for obj in (item, item.get("attributes") if isinstance(item.get("attributes"),dict) else {}):
            for key in ("zone","zones"):
                if isinstance(obj.get(key), list):
                    return obj[key]
        return []
