import gym
import random
import backend
from gym_connect_four import ConnectFourEnv

env: ConnectFourEnv = gym.make("ConnectFour-v0")

# per request stuff
#backend.play_move(env, action=0)
#backend.play_move(env, action=1)
if state is not None: # the case for when the user wants to start a new game
  state, botaction, result, done = backend.play_move(state=state, action=botaction)
else: # continue existing game
  state, botaction, result, done = backend.play_move(action=botaction)
print(result)
