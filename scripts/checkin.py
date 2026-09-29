#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trae CN / TRAE SOLO CN daily auto check-in.

Calls the official check-in API using the Cloud-IDE-JWT auth scheme.
Requires env vars: TRAE_ACCESS_TOKEN, TRAE_DEVICE_ID, TRAE_REGION (optional).
"""

import json
import os
import sys

import requests

API_BASE = "https://api.trae.cn/trae/api/v2/ug/checkin_credits"
REQ_SOURCE = 1


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

    # Step 1: check status
    print("[1/2] Checking status...")
    try:
        r = requests.post(f"{API_BASE}/status", headers=headers, json=body, timeout=30)
        r.raise_for_status()
        status = unwrap(r.json())
        print(f"  Response: {json.dumps(status, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error checking status: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Body: {e.response.text[:300]}")
        sys.exit(1)

    if status.get("code", 0) != 0 and "code" in status:
        print(f"API error: {status.get('message', 'unknown')}")
        sys.exit(1)

    if status.get("checked_in"):
        print(f"Already checked in today. Credits: {status.get('credits', '?')}")
        return

    if not status.get("enable", True):
        print(f"Check-in not enabled: {json.dumps(status, ensure_ascii=False)[:200]}")
        sys.exit(1)

    # Step 2: claim credits
    print("[2/2] Claiming credits...")
    try:
        r = requests.post(f"{API_BASE}/claim", headers=headers, json=body, timeout=30)
        r.raise_for_status()
        claim = r.json()
        print(f"  Response: {json.dumps(claim, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error claiming credits: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Body: {e.response.text[:300]}")
        sys.exit(1)

    if claim.get("code") == 0:
        print("Check-in successful!")
    else:
        print(f"Check-in failed: {claim.get('message', json.dumps(claim, ensure_ascii=False)[:200])}")
        sys.exit(1)

    # Verify
    try:
        r = requests.post(f"{API_BASE}/status", headers=headers, json=body, timeout=30)
        after = unwrap(r.json())
        print(f"Current credits: {after.get('credits', '?')}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
