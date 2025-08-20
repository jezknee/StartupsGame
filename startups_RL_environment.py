# the Gym environment class
from gymnasium import Env 
# predefined spaces from Gym
from gymnasium import spaces 
# used to randomize starting positions
import random 
# used for integer datatypes
import numpy as np 
# used for clearing the display in jupyter notebooks from
# IPython.display 
#import clear_output
# used for clearing the display
import os
import startups_AI_game as sg

class StartupsEnv():
    def __init__(self):
        pass
    
    def step(self, action):
            pass

    def reset(self):
        company_list, player_list, deck = sg.create_game(sg.company_list, 4, 1)
        market = []
        return company_list, player_list, deck, market

    def render(self):
            pass