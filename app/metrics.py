from collections import deque
from datetime import datetime, timezone
from time import time

_start_time: float = time()

_total_requests: int = 0
_requests_by_method: dict[str, int] = {}
_requests_by_status: dict[int, int] = {}
_notes_created_total: int = 0
_notes_deleted_total: int = 0
_response_time_sum: float = 0.0
_response_time_count: int = 0

# Last 10 requests — each entry: {method, path, status, ms, ts}
_activity_log: deque = deque(maxlen=10)


def record_request(method: str, path: str, status: int, elapsed_ms: float) -> None:
    global _total_requests, _response_time_sum, _response_time_count
    _total_requests += 1
    _requests_by_method[method] = _requests_by_method.get(method, 0) + 1
    _requests_by_status[status] = _requests_by_status.get(status, 0) + 1
    _response_time_sum += elapsed_ms
    _response_time_count += 1
    _activity_log.appendleft({
        "method": method,
        "path": path,
        "status": status,
        "ms": round(elapsed_ms, 2),
        "ts": datetime.now(timezone.utc).isoformat(),
    })


def increment_notes_created() -> None:
    global _notes_created_total
    _notes_created_total += 1


def increment_notes_deleted() -> None:
    global _notes_deleted_total
    _notes_deleted_total += 1


def snapshot(note_count: int) -> dict:
    avg = (_response_time_sum / _response_time_count) if _response_time_count else 0.0
    uptime = time() - _start_time
    return {
        "total_requests": _total_requests,
        "requests_by_method": dict(_requests_by_method),
        "requests_by_status": {str(k): v for k, v in _requests_by_status.items()},
        "notes_created_total": _notes_created_total,
        "notes_deleted_total": _notes_deleted_total,
        "average_response_time_ms": round(avg, 2),
        "uptime_seconds": round(uptime, 1),
        "current_note_count": note_count,
        "activity_log": list(_activity_log),
    }
