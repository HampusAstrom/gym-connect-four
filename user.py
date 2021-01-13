import os
import requests

STIL_ID = ["da20example-s"]
ASSIGNMENT = 1
ANSWER = "hej"
API_KEY = "nyckel"

res = requests.post("http://localhost:8000/submit",
                    data={
                        "stil_id": STIL_ID,
                        "assignment": ASSIGNMENT,
                        "answer": ANSWER,
                        "api_key": API_KEY,
                    })

print(res.json())
