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
    def __init__(self, total_players, num_humans):
        self.total_players = total_players
        self.num_humans = num_humans
        self.game_round = 0
        self.company_list, self.player_list, self.deck = sg.create_game(company_list, self.total_players, self.num_humans)
        self.market = []
        #self.state = 
        #self.observation_space =
        #self.action_space =
        #pass
    
    def step(self, action):
            pass
            #return reward, done, info

    def reset(self, company_list):
        self.company_list, self.player_list, self.deck = sg.create_game(company_list, self.total_players, self.num_humans)
        self.market = []
        self.game_round = 0
        #return self._get_observation()
        

    def render(self):
            pass
    
    def _setup_action_space(self):
        # 19 discrete actions (0 through 18)
        self.player_actions_pick_up = ["from deck", "from market"]
        self.player_actions_put_down = ["to shares", "to market"]
        self.action_space = spaces.Discrete(19)
        self.action_mapping = {}
        action_id = 0

        action_list = sg.get_all_game_actions(self.player_actions_pick_up, self.player_actions_put_down, self.company_list)
        for action in action_list:
            self.action_mapping[action_id] = action
            action_id += 1
        
    def print_action_mapping(self):
        print("Action Space Mapping:")
        for idx, (action_type, target) in self.action_mapping.items():
            print(f"  Action {idx}: {action_type} {target if target else ''}")
