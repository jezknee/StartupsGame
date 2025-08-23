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

class StartupsEnv(Env):
    def __init__(self, total_players, num_humans, default_company_list):
        super().__init__()
        self.total_players = total_players
        self.num_humans = num_humans
        self.game_round = 0
        self.company_list, self.player_list, self.deck = sg.create_game(default_company_list, self.total_players, self.num_humans)
        self.market = []
        self.current_phase ="pickup"
        self._setup_action_space() 
        self.state = self._get_observation()
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self._get_observation().shape[0],), dtype=np.float32)
        self.agent_player = self.random_RL_player_selection()

    def step(self, action):
            pass
            #return reward, done, info

    def reset(self):
        self.company_list, self.player_list, self.deck = sg.create_game(company_list, self.total_players, self.num_humans)
        self.market = []
        self.current_phase ="pickup"
        self._setup_action_space() 
        self.state = self._get_observation()
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self._get_observation().shape[0],), dtype=np.float32)
        self.game_round = 0
        return self._get_observation()
    
    def _get_observation(self):
        player = self.player_list[0]
        # player_coins
        player_coins = player._coins
        # player_hand
        player_hand = player._hand # might want to include card values?
        # player_shares
        player_shares = player._shares
        # player chips
        player_chips = player._chips
        #market cards
        market_cards = self.market
        # market card coins
        market_card_coins = [card._coins_on for card in market_cards]
        # other player shares
        other_player_shares = [player._shares for player in self.player_list[1:]]
        # other player coins
        other_player_coins = [player._coins for player in self.player_list[1:]]
        # other player chips
        other_player_chips = [player._chips for player in self.player_list[1:]]

        # Convert to RL-friendly format
        return self._convert_to_numeric_observation(player_coins, player_hand, player_shares, player_chips, market_cards, market_card_coins, other_player_shares, other_player_coins, other_player_chips)

    def _convert_to_numeric_observation(self, player_coins, player_hand, player_shares, player_chips, market_cards, market_card_coins, other_player_shares, other_player_coins, other_player_chips):
        obs = []
        obs.append(float(player_coins))
        
        # Convert hand to counts
        player_hand_dict = sg.get_card_dictionary(player_hand)
        for company in self.company_list:
            obs.append(float(player_hand_dict.get(company._name, 0)))
        
        player_shares_dict = sg.get_card_dictionary(player_shares)
        for company in self.company_list:
            obs.append(float(player_shares_dict.get(company._name, 0)))

        company_set = set()
        for company in player_chips:
            company_name = company._name
            company_set.add(company_name)
        for company in self.company_list:
            obs.append(1.0 if company._name in company_set else 0.0)

        market_cards_dict = sg.get_card_dictionary(market_cards)
        for company in self.company_list:
            obs.append(float(market_cards_dict.get(company._name, 0)))

        # Market card coins - max coins per company
        for company in self.company_list:
            max_coins = max([card._coins_on for card in self.market 
                            if card._company == company._name] + [0])
            obs.append(float(max_coins))
        
        # Other players (same pattern for each)
        for other_player in self.player_list[1:]:
            obs.append(float(other_player._coins))
            
            other_shares = sg.get_card_dictionary(other_player._shares)
            for company in self.company_list:
                obs.append(float(other_shares.get(company._name, 0)))

            other_chips = sg.get_company_set(other_player)
            for company in self.company_list:
                obs.append(1.0 if company._name in other_chips else 0.0)

        return np.array(obs, dtype=np.float32)


    def render(self):
            pass
    
    def _setup_action_space(self):
        # 19 discrete actions (0 through 18)
        self.player_actions_pick_up = ["from deck", "from market"]
        self.player_actions_put_down = ["to shares", "to market"]
        self.action_mapping = {}
        action_id = 0
        #action_list = sg.get_all_game_actions(self.player_actions_pick_up, self.player_actions_put_down, self.company_list)
        action_list = self._return_valid_actions()
        self.action_space = spaces.Discrete(len(action_list))
        for action in action_list:
            self.action_mapping[action_id] = action
            action_id += 1
        
    def print_action_mapping(self):
        print("Action Space Mapping:")
        for action_id, action in self.action_mapping.items():
            # Assuming Action objects have attributes like .type and .target
            print(f"  Action {action_id}: {action.type} {action.target if hasattr(action, 'target') and action.target else ''}")

    def _return_valid_actions(self):
        player = self.player_list[0]
        if self.current_phase == "pickup":
            choices = sg.return_all_pickup_choices(player, self.market)
        elif self.current_phase == "putdown":
            choices = sg.return_all_putdown_choices(player, self.company_list)
        return choices
    
    def random_RL_player_selection(self):
        random_choice = random.choice(range(len(self.player_list)))
        agent_player = None
        counter = 0
        for player in self.player_list:
            if counter == random_choice:
                agent_player = player
            counter += 1
        agent_player._human = False 
        agent_player.pickup_strategy = None 
        agent_player.putdown_strategy = None
        return agent_player
    
