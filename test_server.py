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
