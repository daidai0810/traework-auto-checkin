import requests, json, sys, os

BASE_URL = "https://api.trae.cn/trae/api/v2/ug"
STATUS_URL = BASE_URL + "/checkin_credits/status"
CLAIM_URL = BASE_URL + "/checkin_credits/claim"

def get_headers(token):
    return {"Authorization": "Bearer " + token, "Content-Type": "application/json"}

def check_status(token):
    try:
        r = requests.post(STATUS_URL, headers=get_headers(token), timeout=30)
        return r.json()
    except Exception as e:
        print("Error:", e)
        return None

def claim_credits(token):
    try:
        r = requests.post(CLAIM_URL, headers=get_headers(token), timeout=30)
        return r.json()
    except Exception as e:
        print("Error:", e)
        return None

def main():
    token = os.environ.get("TRAE_ACCESS_TOKEN")
    if not token:
        print("Error: TRAE_ACCESS_TOKEN not set")
        sys.exit(1)
    print("TraeWork Auto Checkin")
    status = check_status(token)
    if not status or status.get("code") != 0:
        print("Failed to check status")
        sys.exit(1)
    data = status.get("data", {})
    if data.get("checked_in") or data.get("isCheckedIn"):
        print("Already checked in today")
        return
    print("Claiming credits...")
    result = claim_credits(token)
    if result and result.get("code") == 0:
        print("Checkin successful!")
        print(json.dumps(result, ensure_ascii=False))
    else:
        print("Checkin failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
