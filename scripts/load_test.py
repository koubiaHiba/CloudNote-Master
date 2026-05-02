"""
Load test script for CloudNotes.

Usage:
    python scripts/load_test.py [base_url]

Examples:
    python scripts/load_test.py http://localhost:5000
    python scripts/load_test.py https://cloudnotes-app.azurewebsites.net
"""

import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:5000"

session = requests.Session()

results: list[dict] = []


def timed(method: str, url: str, **kwargs):
    t0 = time.perf_counter()
    try:
        res = session.request(method, url, timeout=10, **kwargs)
        elapsed = (time.perf_counter() - t0) * 1000
        results.append({"method": method, "url": url, "status": res.status_code, "ms": elapsed, "ok": res.ok})
        return res
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        results.append({"method": method, "url": url, "status": 0, "ms": elapsed, "ok": False, "error": str(exc)})
        return None


def create_note(i: int):
    return timed("POST", f"{BASE_URL}/api/notes", json={"title": f"Load Test Note {i}", "content": f"Content for note {i}"})


def get_all():
    return timed("GET", f"{BASE_URL}/api/notes")


def update_note(note_id: int, i: int):
    return timed("PUT", f"{BASE_URL}/api/notes/{note_id}", json={"title": f"Updated Note {i}", "content": "Updated content"})


def delete_note(note_id: int):
    return timed("DELETE", f"{BASE_URL}/api/notes/{note_id}")


def run():
    print(f"\nLoad testing: {BASE_URL}\n{'─'*50}")

    # Step 1: Create 20 notes concurrently
    print("Creating 20 notes…")
    created_ids: list[int] = []
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(create_note, i): i for i in range(1, 21)}
        for fut in as_completed(futures):
            res = fut.result()
            if res and res.ok:
                created_ids.append(res.json()["id"])

    # Step 2: Read all notes
    print("Reading all notes…")
    get_all()

    # Step 3: Update 5 random notes
    print("Updating 5 notes…")
    to_update = random.sample(created_ids, min(5, len(created_ids)))
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = [ex.submit(update_note, nid, i) for i, nid in enumerate(to_update)]
        for fut in as_completed(futures):
            fut.result()

    # Step 4: Delete 10 random notes
    print("Deleting 10 notes…")
    to_delete = random.sample(created_ids, min(10, len(created_ids)))
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = [ex.submit(delete_note, nid) for nid in to_delete]
        for fut in as_completed(futures):
            fut.result()

    # Step 5: Read all notes again
    print("Final read…")
    get_all()

    # ── Summary ──────────────────────────────────────────────────────────────────
    total     = len(results)
    errors    = [r for r in results if not r["ok"]]
    ok_times  = [r["ms"] for r in results if r["ok"]]
    avg_ms    = sum(ok_times) / len(ok_times) if ok_times else 0
    min_ms    = min(ok_times) if ok_times else 0
    max_ms    = max(ok_times) if ok_times else 0

    print(f"\n{'─'*50}")
    print(f"{'Total requests':<28} {total}")
    print(f"{'Successful':<28} {total - len(errors)}")
    print(f"{'Errors':<28} {len(errors)}")
    print(f"{'Avg response time':<28} {avg_ms:.1f} ms")
    print(f"{'Min response time':<28} {min_ms:.1f} ms")
    print(f"{'Max response time':<28} {max_ms:.1f} ms")

    if errors:
        print("\nFailed requests:")
        for e in errors[:5]:
            print(f"  {e['method']} {e['url']} → {e.get('status', 'N/A')} ({e.get('error', '')})")

    print(f"\nDashboard: {BASE_URL}/dashboard")
    print(f"Metrics:   {BASE_URL}/metrics")


if __name__ == "__main__":
    run()
