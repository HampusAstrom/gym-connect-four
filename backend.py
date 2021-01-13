import gym
import random
import numpy as np
from gym_connect_four import ConnectFourEnv

env: ConnectFourEnv = gym.make("ConnectFour-v0")

def play_move(state=None, action=-1):
   env.reset(board=state)
   result = 0 # 0 while not done, loss = -1, win = +1, draw = +0.5, error = -10
   DRAW = 0.5
   ERROR = -10

   # if action is equal to -1 reset to empty and determine first player
   # TODO

   # students turn
   avmoves = env.available_moves()
   if not avmoves:
      result = DRAW
      return state, -1, result, True
   if action not in avmoves:
      result = ERROR
      return state, -1, result, True
   state, reward, done, _ = env.step(action)
   print(state)
   # print(done)
   if done:
      return state, -1, reward, done

   # change board format to the other player
   env.change_player()

   # bots turn
   avmoves = env.available_moves()
   if not avmoves:
      result = DRAW
      return state, -1, result, True
   botaction = random.choice(list(avmoves))
   state, reward, done, _ = env.step(botaction)
   print(state)
   # print(botaction)
   # print(done)
   print()

   # change board format to the other player
   env.change_player()
   if done:
      if reward == 1: # reward is always in current players view
         reward = -1
   return state, botaction, reward, done
