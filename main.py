import base64
import bz2
import hashlib
import hmac
import os
from typing import Optional, List
import uuid
import time
import yaml

from fastapi import FastAPI, UploadFile, HTTPException, Form, File
from pydantic import BaseModel
from enum import Enum

import models
from sqlalchemy.orm import Session
from database import SessionLocal, engine

import utils
import backend

models.Base.metadata.create_all(bind=engine)

class Status(BaseModel):
    msg: Optional[str]
    status: str
    signature: Optional[str]
    submission_id: Optional[uuid.UUID]
    result: Optional[float]
    move: Optional[int]
    state: Optional[list]

class NotebookCompression(str, Enum):
    bz2 = 'application/x-bzip2'
    uncompressed = 'application/x-ipynb+json'

OUTPUT_FOLDER = "./database"

app = FastAPI()
from config import SECRET_KEY, ANSWERS as CONFIG_ANSWERS, API_KEY

# Convert to answers to hashes
ANSWERS = {k: [
        hashlib.sha256(va if isinstance(va, bytes) else va.encode('utf-8')).hexdigest() for va in v
    ] for k, v in CONFIG_ANSWERS.items()
}

@app.get("/")
async def root():
    return "Artificial Intelligence - EDAP01 / TFRP20 automatic submission service."


@app.post("/submit", response_model=Status)
async def submit(stil_id: List[str] = Form(..., max_length=50, regex="^[\w\d_-]*$"),
                 move: int = Form(..., ge=-1, le=6), # -1 encodes a new game request
                 api_key: str = Form(...))->Status:
    """
    Submit move, get state from database and return move and/or end result.
    """

    print(f"Receiving move from: {stil_id}")
    if api_key != API_KEY:
        return Status(status='error', msg='Incorrect API key.')

    # Concatenate stil ids
    stil_id = '+'.join(sorted(stil_id))

    # Submission ID
    uid = uuid.uuid4()

    # Sign user submission
    msg = bytes(str(uid) + stil_id, 'utf-8')

    # Create HMAC with secret key
    signed_ok = hmac.new(SECRET_KEY, msg=msg, digestmod='sha512').hexdigest()

    # TODO: check if game already exists, and load the state for use with action
    state = None

    # make move or start new game, state=None will start a new game
    state, botaction, result, done = backend.play_move(state=state, action=move)
    print(state.tolist())

    # TODO: save state in database together with stil_id and possibly win statistics

    return Status(status='correct', signature=signed_ok, submission_id=uid, result=result, move=botaction)

    # correct_answer = answer_hash in ANSWERS[assignment]
    #
    # # User folder
    # timestamp = time.strftime("%Y_%m_%d-%H_%M_%S")
    # status = 'pass' if correct_answer else 'fail'
    # submission_name = f"{timestamp}-{status}-{uid}"
    # user_folder = os.path.join(OUTPUT_FOLDER, str(assignment), stil_id)
    # os.makedirs(user_folder, exist_ok=True)
    # sub_path = os.path.join(user_folder, submission_name) + '.yml'
    # note_path = os.path.join(user_folder, submission_name) + '.ipynb'
    #
    # # Write submission report to file
    # with open(sub_path, 'w') as f:
    #     yaml.dump({
    #         "Stil-Id": stil_id,
    #         "Assignment": assignment,
    #         "Status": status,
    #         "Time": timestamp,
    #         "Signature": signed_ok,
    #         "Answer": answer,
    #         "Submission-Id": str(uid)
    #     },f, sort_keys=True)
    #
    # # Return HMAC
    # if correct_answer:
    #     return Status(status='correct', signature=signed_ok, submission_id=uid)
    # else:
    #     return Status(status='incorrect', submission_id=uid)
