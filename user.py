import os
import requests

STIL_ID = ["da20example-s"]
MOVE = 3
API_KEY = "nyckel"

res = requests.post("http://localhost:8000/submit",
                    data={
                        "stil_id": STIL_ID,
                        "move": MOVE,
                        "api_key": API_KEY,
                    })

print(res)
print(res.json())

print(res.json()['status'])
