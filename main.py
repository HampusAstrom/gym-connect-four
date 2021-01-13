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

import utils


class Status(BaseModel):
    msg: Optional[str]
    status: str
    signature: Optional[str]
    submission_id: Optional[uuid.UUID]


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
    return "EDAN20 automatic submission service."


@app.post("/submit", response_model=Status)
async def submit(stil_id: List[str] = Form(..., max_length=50, regex="^[\w\d_-]*$"),
                 assignment: int = Form(...),
                 answer: str = Form(...),
                 api_key: str = Form(...),
                 notebook_format: NotebookCompression = Form(default=NotebookCompression.bz2),
                 notebook_file: UploadFile = File(...))->Status:
    """
    Submit answers, verify and return signature if correct.

    notebook_format defaults to bzip2 compressed format!
    """

    print(f"Receiving submission from: {stil_id}")
    if api_key != API_KEY:
        return Status(status='error', msg='Incorrect API key.')

    # Concatenate stil ids
    stil_id = '+'.join(sorted(stil_id))

    # Check answer
    answer_hash = hashlib.sha256(bytes(answer, 'utf-8')).hexdigest()
    if assignment not in ANSWERS:
        return Status(status='error', msg='Incorrect assignment code.')

    correct_answer = answer_hash in ANSWERS[assignment]

    # Unpack notebook
    try:
        notebook_content = await notebook_file.read()
        if notebook_format == NotebookCompression.bz2:
            notebook = bz2.decompress(notebook_content)
        else:
            notebook = notebook_content
    except:
        return Status(status='error', msg='Failed to read notebook.')

    # Submission ID
    uid = uuid.uuid4()

    # Sign user submission
    msg = bytes(hashlib.sha512(notebook).hexdigest() + str(uid) + str(assignment) + stil_id, 'utf-8')

    # Create HMAC with secret key
    signed_ok = hmac.new(SECRET_KEY, msg=msg, digestmod='sha512').hexdigest()

    # User folder
    timestamp = time.strftime("%Y_%m_%d-%H_%M_%S")
    status = 'pass' if correct_answer else 'fail'
    submission_name = f"{timestamp}-{status}-{uid}"
    user_folder = os.path.join(OUTPUT_FOLDER, str(assignment), stil_id)
    os.makedirs(user_folder, exist_ok=True)
    sub_path = os.path.join(user_folder, submission_name) + '.yml'
    note_path = os.path.join(user_folder, submission_name) + '.ipynb'

    # Write submission report to file
    with open(sub_path, 'w') as f:
        yaml.dump({
            "Stil-Id": stil_id,
            "Assignment": assignment,
            "Status": status,
            "Time": timestamp,
            "Signature": signed_ok,
            "Answer": answer,
            "Submission-Id": str(uid)
        },f, sort_keys=True)

    # Store submitted notebook
    with open(note_path, 'wb') as f:
        f.write(notebook)

    # Return HMAC
    if correct_answer:
        return Status(status='correct', signature=signed_ok, submission_id=uid)
    else:
        return Status(status='incorrect', submission_id=uid)
