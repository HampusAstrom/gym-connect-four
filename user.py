import os
import requests
import numpy as np

STIL_ID = ["da20example-s1"]
MOVE = 6
API_KEY = "nyckel"
TEACHER_KEY = '123'

# server adress online: https://vilde.cs.lth.se/edap01-4inarow/docs

res = requests.post("http://localhost:8000/move",
                    data={
                        "stil_id": STIL_ID,
                        "move": MOVE, # -1 singnals the system to start a new game. any running game is counted as a loss
                        "api_key": API_KEY,
                    })

print(res)
print(res.json())

print(res.json()['botmove'])
print(np.array(res.json()['state']))

res = requests.post("http://localhost:8000/student",
                    data={
                        "stil_id": STIL_ID[0],
                        "teacher_key": TEACHER_KEY,
                    })

print(res.json())
