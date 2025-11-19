import urllib.request
import json

try:
    with urllib.request.urlopen("http://localhost:8000/") as response:
        data = response.read().decode("utf-8")
        print("Status Code:", response.getcode())
        print("Response:", json.loads(data))
except Exception as e:
    print("Error:", e)

try:
    with urllib.request.urlopen("http://localhost:8000/docs") as response:
        data = response.read().decode("utf-8")
        print("Docs Status Code:", response.getcode())
        print("Docs Response (first 200 chars):", data[:200])
except Exception as e:
    print("Docs Error:", e)

# Test the leave requests endpoint
try:
    req = urllib.request.Request(
        "http://localhost:8000/api/admin/leave/requests", headers={"accept": "application/json"}
    )
    with urllib.request.urlopen(req) as response:
        data = response.read().decode("utf-8")
        print("Leave Requests Status Code:", response.getcode())
        print("Leave Requests Response:", json.loads(data))
except Exception as e:
    print("Leave Requests Error:", e)
