#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trae CN / TRAE SOLO CN daily auto check-in.

Calls the official check-in API using the Cloud-IDE-JWT auth scheme.
Requires env vars: TRAE_ACCESS_TOKEN, TRAE_DEVICE_ID, TRAE_REGION (optional).
"""

import json
import os
import sys
import time

import requests

API_BASE = "https://api.trae.cn/trae/api/v2/ug/checkin_credits"
REQ_SOURCE = 1
MAX_RETRIES = 3
RETRY_DELAY = 20  # seconds


def get_headers(token, device_id, region):
    headers = {
        "Authorization": f"Cloud-IDE-JWT {token}",
        "Content-Type": "application/json",
        "x-device-id": device_id,
    }
    if region:
        headers["X-User-Region"] = region
    return headers


def unwrap(resp):
    if "checked_in" not in resp and isinstance(resp.get("data"), dict) and "checked_in" in resp["data"]:
        return resp["data"]
    return resp


def post(path, headers, body):
    r = requests.post(f"{API_BASE}/{path}", headers=headers, json=body, timeout=30)
    r.raise_for_status()
    return unwrap(r.json())


def attempt(headers, body):
    """One full attempt. Returns (ok, reason)."""
    # Step 1: check status
    try:
        status = post("status", headers, body)
    except Exception as e:
        detail = ""
        if hasattr(e, "response") and e.response is not None:
            detail = f" | body={e.response.text[:200]}"
        return False, f"status request failed: {e}{detail}"

    print(f"  status: {json.dumps(status, ensure_ascii=False)}")

    if status.get("code", 0) != 0:
        return False, f"API error: {status.get('message', 'unknown')}"

    if status.get("checked_in"):
        return True, f"already checked in (credits={status.get('credits', '?')})"

    if not status.get("enable", True):
        return False, "check-in disabled for this account"

    # Step 2: claim
    try:
        claim = post("claim", headers, body)
    except Exception as e:
        detail = ""
        if hasattr(e, "response") and e.response is not None:
            detail = f" | body={e.response.text[:200]}"
        return False, f"claim request failed: {e}{detail}"

    print(f"  claim: {json.dumps(claim, ensure_ascii=False)}")

    if claim.get("code") == 0:
        try:
            after = post("status", headers, body)
            return True, f"claimed successfully (credits={after.get('credits', '?')})"
        except Exception:
            return True, "claimed successfully"

    return False, f"claim rejected: {claim.get('message', json.dumps(claim, ensure_ascii=False)[:200])}"


def main():
    token = os.environ.get("TRAE_ACCESS_TOKEN")
    device_id = os.environ.get("TRAE_DEVICE_ID", "")
    region = os.environ.get("TRAE_REGION", "CN")

    if not token:
        print("Error: TRAE_ACCESS_TOKEN not set")
        sys.exit(1)
    if not device_id:
        print("Error: TRAE_DEVICE_ID not set")
        sys.exit(1)

    headers = get_headers(token, device_id, region)
    body = {"req_source": REQ_SOURCE}

    print("=== Trae CN Auto Check-in ===")

    last_reason = ""
    for i in range(1, MAX_RETRIES + 1):
        print(f"[Attempt {i}/{MAX_RETRIES}]")
        try:
            ok, reason = attempt(headers, body)
        except Exception as e:
            ok, reason = False, f"unexpected error: {e}"

        if ok:
            print(f"Result: {reason}")
            print("Check-in successful!")
            return

        last_reason = reason
        print(f"Result: {reason}")
        if i < MAX_RETRIES:
            print(f"Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)

    print(f"Check-in failed after {MAX_RETRIES} attempts: {last_reason}")
    sys.exit(1)


if __name__ == "__main__":
    main()
