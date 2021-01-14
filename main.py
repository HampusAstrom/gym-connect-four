import base64
import bz2
import hashlib
import hmac
import os
from typing import Optional, List
import uuid
import time
import yaml

from fastapi import FastAPI, UploadFile, HTTPException, Form, File, Depends
from pydantic import BaseModel
from enum import Enum

import models
from models import StudentGame
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import json
import numpy as np

import utils
import backend

models.Base.metadata.create_all(bind=engine)

class Status(BaseModel):
    msg: Optional[str]
    status: str
    signature: Optional[str]
    submission_id: Optional[uuid.UUID]
    result: Optional[float]
    botmove: Optional[int]
    state: Optional[list]

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app = FastAPI()
from config import API_KEY, SECRET_KEY

@app.get("/")
async def root():
    return "Artificial Intelligence - EDAP01 / TFRP20 automatic submission service."


@app.post("/submit", response_model=Status)
async def submit(stil_id: List[str] = Form(..., max_length=50, regex="^[\w\d_-]*$"),
                 move: int = Form(..., ge=-1, le=6), # -1 encodes a new game request
                 api_key: str = Form(...),
                 db: Session = Depends(get_db))->Status:
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

    # check if game already exists, and load the state for use with action
    state = None
    stgame = db.query(StudentGame).filter(StudentGame.stil_id == stil_id).first()
    if stgame is not None:
        if stgame.running: # If a game is running, load it
            jstate = stgame.state
            state = np.array(json.loads(jstate))
        else: # If not, we are staring a new game
            stgame.running = True
    else:
        # make new StudentGame entry if none exists
        stgame = StudentGame()
        stgame.stil_id = stil_id
        stgame.running = True
        stgame.state = None
        stgame.played = 0
        stgame.won = 0
        stgame.streak = 0
        stgame.total_reward = 0


    # make move or start new game, state=None will start a new game
    state, botaction, result, done = backend.play_move(state=state, action=move)

    # save state in database
    jstate=json.dumps(state.tolist())
    stgame.state = jstate

    # If game is over update statistics and reset stuff in db
    if done:
        stgame.running = False
        stgame.state = None
        stgame.played = stgame.played + 1
        if result == 1:
            stgame.won = stgame.won + 1
            stgame.streak = stgame.streak + 1
        else:
            stgame.streak = 0
        stgame.total_reward = stgame.total_reward + result


    db.add(stgame)
    db.commit()

    return Status(status='correct', signature=signed_ok, submission_id=uid, result=result, botmove=botaction)
