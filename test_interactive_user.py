import gym
import random
import test_interactive as backend
from gym_connect_four import ConnectFourEnv

env: ConnectFourEnv = gym.make("ConnectFour-v0")

# per request stuff
#backend.play_move(env, action=0)
#backend.play_move(env, action=1)
done = False
state = None
while True:
  # dummy stuff used for testing, including loop
  if done:
    break
  avmoves = env.available_moves()
  if not avmoves:
    break
  botaction = random.choice(list(avmoves))

  if state is not None: # the case for when the user wants to start a new game
    state, botaction, result, done = backend.play_move(env, state=state, action=botaction)
  else: # continue existing game
    state, botaction, result, done = backend.play_move(env, action=botaction)
print(result)
