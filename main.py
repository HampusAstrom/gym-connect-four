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
from pydantic import BaseModel, Json
from enum import Enum

import models
from models import StudentGame
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import json
import numpy as np

import utils
import backend
from threading import Lock

lock = Lock()

models.Base.metadata.create_all(bind=engine)

class Status(BaseModel):
    msg: Optional[str]
    status: bool
    result: Optional[float]
    botmove: Optional[int]
    state: Optional[List[List[int]]]

class Student(BaseModel):
    msg: Optional[str]
    status: bool
    stil_id: Optional[str]
    played: Optional[int]
    won: Optional[int]
    lost: Optional[int]
    streak: Optional[int]
    total_reward: Optional[float]

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app = FastAPI()
from config import API_KEY, TEACHER_KEY

@app.get("/")
async def root():
    return "Artificial Intelligence - EDAP01 / TFRP20 automatic submission service."

@app.post("/student")
async def student(stil_id: str = Form(..., max_length=50, regex="^[\w\d_-]*$"),
                  teacher_key: str = Form(...),
                  db: Session = Depends(get_db))->Student:
    """
    Get ?all? database entried for a given stil_id
    """
    print(f"Receiving check on: {stil_id}")
    if teacher_key != TEACHER_KEY:
        return Student(status=False, msg='Incorrect teacher key.')
    #entries = db.query(StudentGame).filter(StudentGame.stil_id.contains(stil_id))
    entries = db.query(StudentGame).filter(StudentGame.stil_id.contains(stil_id)).all()
    print(entries)
    return Student(status=False)

def game_done(stgame, result):
    stgame.running = False
    stgame.state = None
    stgame.played = stgame.played + 1
    if result == 1:
        stgame.won = stgame.won + 1
        stgame.streak = stgame.streak + 1
    elif result == 0.5:
        stgame.streak = stgame.streak + 1
    elif result < 0:
        stgame.lost = stgame.lost + 1
        stgame.streak = 0
    stgame.total_reward = stgame.total_reward + result

@app.post("/move", response_model=Status)
async def move(stil_id: List[str] = Form(..., max_length=50, regex="^[\w\d_-]*$"),
                 move: int = Form(..., ge=-1, le=6), # -1 encodes a new game request
                 api_key: str = Form(...),
                 db: Session = Depends(get_db))->Status:
    """
    Submit move, get state from database and return move and/or end result.
    """

    print(f"Receiving move from: {stil_id}")
    if api_key != API_KEY:
        return Status(status=False, msg='Incorrect API key.')

    # Concatenate stil ids
    stil_id = '+'.join(sorted(stil_id))

    # check if game already exists, and load the state for use with action
    state = None
    with lock:
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
            stgame.lost = 0
            stgame.streak = 0
            stgame.total_reward = 0

        if move == -1:
            if stgame.running:
                game_done(stgame, -1)
                db.add(stgame)
                db.commit()
            return Status(status=True, msg='New game initiated, you start. Make your move')

        # make move or start new game, state=None will start a new game
        state, botaction, result, done = backend.play_move(state=state, action=move)

        # save state in database
        jstate=json.dumps(state.tolist())
        stgame.state = jstate

        # If game is over update statistics and reset stuff in db
        if done:
            game_done(stgame, result)

        db.add(stgame)
        db.commit()

        # return with error and penalize average results if faulty move it played
        if result == -10:
            return Status(status=False, msg='Impossible move.')

        return Status(status=True,
                      result=result,
                      botmove=botaction,
                      state=state.tolist())
