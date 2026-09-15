#!/usr/bin/env python3
"""
Validates the LegiScan API for Clean Slate Watch.

Answers the four questions Phase 1 left open about this source:
  1. Does the API answer with a real key, or does Cloudflare block it?
  2. Does it cover the four pilot states with current sessions?
  3. Does full-text search surface the record-sealing bills we care about?
  4. Does change_hash work as a "what moved since yesterday" signal?

Reads the key from ~/.clean-slate-watch.env — never from the command line,
so it stays out of shell history and process listings.
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.legiscan.com/"
ENV_FILE = Path.home() / ".clean-slate-watch.env"
PILOTS = ["VA", "IL", "MI", "TX"]

# Terms that appear in record-sealing legislation. Deliberately loose —
# the point is recall; a model narrows the shortlist later.
QUERIES = [
    "clean slate",
    "automatic expungement",
    "sealing criminal records",
]


def load_key():
    if not ENV_FILE.exists():
        sys.exit(f"No key file at {ENV_FILE}. See the setup command.")
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("LEGISCAN_API_KEY="):
            key = line.split("=", 1)[1].strip().strip("'\"")
            if key and key != "paste_key_here":
                return key
    sys.exit(f"LEGISCAN_API_KEY not set in {ENV_FILE}")


def call(key, op, **params):
    """One API call. Returns (status_label, payload_or_error, seconds)."""
    qs = urllib.parse.urlencode({"key": key, "op": op, **params})
    req = urllib.request.Request(
        f"{API}?{qs}",
        headers={"User-Agent": "clean-slate-watch/0.1 (feasibility test)"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read().decode("utf-8", "replace")
            elapsed = time.time() - t0
    except Exception as e:
        return "NETWORK", str(e), time.time() - t0

    if "<html" in raw[:200].lower():
        hint = "Cloudflare challenge" if "just a moment" in raw.lower() else "HTML, not JSON"
        return "BLOCKED", hint, elapsed
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return "BADJSON", raw[:160], elapsed
    if data.get("status") != "OK":
        return "APIERROR", data.get("alert", {}).get("message", raw[:160]), elapsed
    return "OK", data, elapsed


def redact(key):
    return f"{key[:4]}…{key[-4:]} ({len(key)} chars)"


def main():
    key = load_key()
    print(f"key loaded: {redact(key)}\n")

    # --- 1 & 2: reachability and session coverage -------------------------
    print("=" * 74)
    print("1. REACHABILITY + SESSION COVERAGE")
    print("=" * 74)
    sessions = {}
    for st in PILOTS:
        status, payload, secs = call(key, "getSessionList", state=st)
        if status != "OK":
            print(f"  {st}  {status:<9} {str(payload)[:60]}")
            continue
        rows = payload.get("sessions", [])
        current = sorted(rows, key=lambda s: s.get("year_end", 0), reverse=True)[:1]
        sessions[st] = current[0] if current else None
        s = sessions[st]
        print(
            f"  {st}  OK  {secs:4.1f}s  {len(rows):>3} sessions  "
            f"latest: {s.get('session_name','?')[:42]} "
            f"(id {s.get('session_id')}, {s.get('year_start')}-{s.get('year_end')})"
        )

    if not sessions:
        sys.exit("\nNo state answered. Stop here — LegiScan is not usable as a source.")

    # --- 3: does search find the bills that matter? -----------------------
    print("\n" + "=" * 74)
    print("3. FULL-TEXT SEARCH — does it surface record-sealing bills?")
    print("=" * 74)
    seen = {}
    for st in PILOTS:
        if st not in sessions:
            continue
        for q in QUERIES:
            status, payload, secs = call(key, "getSearch", state=st, query=q, year=2)
            if status != "OK":
                print(f"  {st} “{q}” -> {status}: {str(payload)[:50]}")
                continue
            res = payload.get("searchresult", {})
            summary = res.pop("summary", {})
            hits = [v for v in res.values() if isinstance(v, dict)]
            print(f"  {st} “{q}” -> {summary.get('count','?')} total, page 1 = {len(hits)}")
            for h in hits[:4]:
                num = h.get("bill_number", "?")
                title = re.sub(r"\s+", " ", h.get("title", ""))[:64]
                print(f"       {h.get('relevance',0):>3}%  {num:<9} {title}")
                seen.setdefault((st, num), h)
            time.sleep(0.4)

    # --- 4: change_hash as a daily delta signal ---------------------------
    print("\n" + "=" * 74)
    print("4. CHANGE_HASH — the daily 'what moved' signal")
    print("=" * 74)
    va = sessions.get("VA")
    if va:
        status, payload, secs = call(key, "getMasterListRaw", id=va["session_id"])
        if status == "OK":
            ml = payload.get("masterlist", {})
            bills = [v for k, v in ml.items() if k != "session"]
            with_hash = sum(1 for b in bills if b.get("change_hash"))
            print(f"  VA session {va['session_id']}: {len(bills)} bills in {secs:.1f}s")
            print(f"  {with_hash}/{len(bills)} carry a change_hash")
            print("  sample:")
            for b in bills[:3]:
                print(f"       {b.get('number','?'):<9} {b.get('change_hash','')[:32]}")
            print("\n  -> Store these. Tomorrow, re-pull and diff: any bill whose hash")
            print("     changed is the only one worth fetching in full. 1 call/state/day.")
        else:
            print(f"  getMasterListRaw -> {status}: {str(payload)[:80]}")

    print("\n" + "=" * 74)
    print(f"VERDICT: {len(sessions)}/{len(PILOTS)} pilot states reachable, "
          f"{len(seen)} distinct candidate bills found")
    print("=" * 74)


if __name__ == "__main__":
    main()
