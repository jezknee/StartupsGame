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
from enum import Enum

class StartupsEnv(Env):
    def __init__(self, total_players, num_humans, default_company_list):
        super().__init__()
        self.total_players = total_players
        self.num_humans = num_humans
        self.game_round = 0
        self.default_company_list = default_company_list
        self.company_list, self.player_list, self.deck = sg.create_game(self.default_company_list, self.total_players, self.num_humans)
        self.agent_player = self.random_RL_player_selection()
        self.market = []
        self.state_controller = GameStateController(self.player_list, self.agent_player)
        self._setup_action_space() 
        self.state = self._get_observation()
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self._get_observation().shape[0],), dtype=np.float32)
        
    def step(self, action_id):
        if action_id not in self.action_mapping:
            return self.state, -10, False, False, {"invalid_action": True}

        done = False
        info = {}
        #game_round = 0
        #reward = -0.01
        #rl_player = self.agent_player

        # need to decide what to do about one action in a turn or two actions
        # the issue here is that your function takes one action_id, but you're playing two actions
        # you could pass in 2 action_ids, one from each type
        # but the gym environment won't allow that - either has to be a compound action, or 2 step calls per turn, or a tuple with 2 actions
        #self.game_round += 1
        
        action = self.action_mapping[action_id]  # Predetermined by RL agent
        if not self._return_valid_action_check(action):
            return self.state, -10, True, False, {"invalid_action": True}

        if self.state_controller.get_current_phase() == TurnPhase.RL_PICKUP:
            try:
                sg.execute_pickup(self.agent_player, action, self.market, self.deck)
                self.state_controller._change_phase()
            except:
                return self.state, -10, False, False, {"invalid_action": True}
        elif self.state_controller.get_current_phase() == TurnPhase.RL_PUTDOWN:
            try:
                sg.execute_putdown(self.agent_player, action, self.player_list, self.market, self.company_list)
                self.state_controller._change_phase()
            except:
                return self.state, -10, False, False, {"invalid_action": True}
        elif self.state_controller.get_current_phase() == TurnPhase.OTHER_PLAYERS:
            for p in self.player_list:
                if p != self.agent_player:
                    # need to decide whether random or avoid_loss
                    pickup_action = p.pickup_strategy(p, self.market, self.deck, self.player_list)
                    if pickup_action:
                        sg.execute_pickup(p, pickup_action, self.market, self.deck)
                    putdown_action = p.putdown_strategy(p, self.market, self.deck, self.player_list)
                    if putdown_action:
                        sg.execute_putdown(p, putdown_action, self.player_list, self.market, self.company_list)
                        self.state_controller._change_phase()

        reward = self._calculate_reward(self.agent_player)
        info = {"intermediate_reward": reward}

        terminated = len(self.deck) == 0        

        if terminated:
            sg.end_game_and_score(self.player_list, self.company_list)
            reward += self._calculate_final_reward()
            info = {"final_reward": reward}

        self._setup_action_space()

        return self._get_observation(), reward, terminated, False, info

    def reset(self):
        self.company_list, self.player_list, self.deck = sg.create_game(self.default_company_list, self.total_players, self.num_humans)
        self.market = []
        self.agent_player = self.random_RL_player_selection()
        self.state_controller = GameStateController(self.player_list, self.agent_player)
        self._setup_action_space() 
        self.state = self._get_observation()
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self._get_observation().shape[0],), dtype=np.float32)
        self.game_round = 0
        return self.state, {"info": "Game reset"}

    def _get_observation(self):
        player = self.agent_player
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
        # game phase
        #game_phase = self.state_controller.get_current_phase()

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
        
        obs.append(float(self.state_controller._enumerate_phase()))

        return np.array(obs, dtype=np.float32)


    def render(self):
            pass
    
    def _setup_action_space(self):
        self.player_actions_pick_up = ["pickup_deck", "pickup_market"]
        self.player_actions_put_down = ["putdown_shares", "putdown_market"]
        self.action_mapping = {}
        action_id = 0
        action_list = sg.get_all_game_actions(self.player_actions_pick_up, self.player_actions_put_down, self.company_list)
        #action_list = self._return_valid_actions()
        
        for action in action_list:
            self.action_mapping[action_id] = action
            action_id += 1

        self.action_space = spaces.Discrete(len(self.action_mapping))
        
    def print_action_mapping(self):
        print("Action Space Mapping:")
        for action_id, action in self.action_mapping.items():
            # Assuming Action objects have attributes like .type and .target
            print(f"  Action {action_id}: {action.type} {action.target if hasattr(action, 'target') and action.target else ''}")

    def _return_valid_actions(self):
        choices = []
        if self.state_controller.current_phase == TurnPhase.RL_PICKUP:
            choices = sg.return_all_pickup_choices(self.agent_player, self.market)
        elif self.state_controller.current_phase == TurnPhase.RL_PUTDOWN:
            choices = sg.return_all_putdown_choices(self.agent_player, self.company_list)

        mask = np.zeros(self.action_space.n, dtype=np.int8)
        for action_id, action in self.action_mapping.items():
            if action in choices:
                mask[action_id] = 1
        return mask

    def _return_valid_action_check(self, action):
        choices = []
        if self.state_controller.current_phase == TurnPhase.RL_PICKUP:
            choices = sg.return_all_pickup_choices(self.agent_player, self.market)
        elif self.state_controller.current_phase == TurnPhase.RL_PUTDOWN:
            choices = sg.return_all_putdown_choices(self.agent_player, self.company_list)

        check = False
        for c in choices:
            if action == c:
                check = True    
        return check

    def _calculate_reward(self, player):
        # placeholder - just a sparse reward for now
        # this will be slower, but I don't want to impose strategies
        return -0.01
        """
        # Only reward getting coins
        coin_change = player._coins - prev_coins
        if coin_change > 0:
            reward += coin_change * 0.1  # Gaining coins is always good
            return -0.01

        could add more rewards as training continues, e.g. add coin rewards later
        could compare with the avoid_loss_ai or random_ai
        """

    def _calculate_player_rank(self):
        rl_player = self.agent_player
        sorted_players = sorted(self.player_list, key=lambda p: p._coins, reverse=True)
        rl_player_rank = sorted_players.index(rl_player) if rl_player in sorted_players else -1
        return rl_player_rank

    def _calculate_final_reward(self):
        rl_rank = self._calculate_player_rank()
        reward_for_winning = 10
        total_players = len(self.player_list)
        reward_given_rank = reward_for_winning - (rl_rank / total_players) + self.agent_player._coins * 0.1
        # again, might want to come up with a different function here
        return reward_given_rank

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

        
"""
    def _handle_other_players(self, env):
        Finished = False
        while not Finished:
            for p in self.player_list:
                if p == self.agent_player:
                    continue
                pickup_action = sg.pickup_strategy(p, self.market, self.deck, self.player_list)
                if pickup_action:
                    sg.execute_pickup(p, pickup_action, self.market, self.deck)
                putdown_action = sg.putdown_strategy(p, self.market, self.deck, self.player_list)
                if putdown_action:
                    sg.execute_putdown(p, putdown_action, self.player_list, self.market, self.company_list)
            Finished = True
        self.current_phase = TurnPhase.ROUND_COMPLETE

    def _run_step(self):
        if self.current_phase == TurnPhase.RL_PICKUP:
            action = self.action_mapping[action_id]  # Predetermined by RL agent
            #self.agent_player._take_action(self.market, self.deck, self.player_list)
            self._change_phase()
        elif self.current_phase == TurnPhase.RL_PUTDOWN:
            action = self.action_mapping[action_id]  # Predetermined by RL agent
            #self.agent_player._take_action(self.market, self.deck, self.player_list)
            self._change_phase()
        elif self.current_phase == TurnPhase.OTHER_PLAYERS:
            self._handle_other_players()
            #self._handle_other_players()
        elif self.current_phase == TurnPhase.ROUND_COMPLETE:
            self.game_round += 1
            self.current_phase = TurnPhase.RL_PICKUP
"""
    
class TurnPhase(Enum):
    RL_PICKUP = "rl_pickup"
    RL_PUTDOWN = "rl_putdown" 
    OTHER_PLAYERS = "other_players"
    ROUND_COMPLETE = "round_complete"

class GameStateController:
    def __init__(self, player_list, agent_player):
        self.player_list = player_list
        self.agent_player = agent_player
        self.current_player_index = 0
        self.current_phase = self.get_starting_phase()
        self.other_players_completed = 0
        #self.env = env
        self.game_round = 0
        self.current_phase = self.get_starting_phase()

    def get_current_phase(self):
        return self.current_phase
    
    def get_starting_phase(self):
        if self.player_list[0] == self.agent_player:
            return TurnPhase.RL_PICKUP
        else:
            return TurnPhase.OTHER_PLAYERS

    def _advance_to_next_player(self):
        if self.current_player_index == len(self.player_list) - 1:
            self.current_player_index = 0
        else:
            self.current_player_index += 1

        if self.player_list[self.current_player_index] == self.agent_player:
            self.current_phase = TurnPhase.RL_PICKUP
        else:
            self.current_phase = TurnPhase.OTHER_PLAYERS

    def _enumerate_phase(self):
        phase_mapping = {
        TurnPhase.RL_PICKUP: 1,
        TurnPhase.RL_PUTDOWN: 2,
        TurnPhase.OTHER_PLAYERS: 3,
        TurnPhase.ROUND_COMPLETE: 4
    }
        return phase_mapping.get(self.current_phase, 0)

    def _change_phase(self):
        hand_size = len(self.agent_player._hand)
        if self.current_phase == TurnPhase.RL_PICKUP and hand_size == 4:
            self.current_phase = TurnPhase.RL_PUTDOWN
        elif self.current_phase == TurnPhase.RL_PUTDOWN and hand_size == 3:
            self.current_phase = TurnPhase.OTHER_PLAYERS
        elif self.current_phase == TurnPhase.OTHER_PLAYERS:
            self._advance_to_next_player()
"""
    def is_rl_agent_turn(self):
        return self.current_phase in [TurnPhase.RL_PICKUP, TurnPhase.RL_PUTDOWN]
            
    def get_next_other_player(self):
        if self.current_phase != TurnPhase.OTHER_PLAYERS:
            return None
            
        other_players = [p for p in self.player_list if p != self.agent_player]
        
        if self.other_players_completed < len(other_players):
            return other_players[self.other_players_completed]
        else:
            return None
    
    def advance_after_other_player_turn(self):
        if self.current_phase == TurnPhase.OTHER_PLAYERS:
            self.other_players_completed += 1
            other_players = [p for p in self.player_list if p != self.agent_player]

            if self.other_players_completed >= len(other_players):
                # All other players finished
                self.current_phase = TurnPhase.ROUND_COMPLETE
    
    def advance_to_next_round(self):
        # error here - still assumes RL player goes first
        # need len(player_list) to be done
        if self.current_phase == TurnPhase.ROUND_COMPLETE:
            self.round_number += 1
            self.current_phase = TurnPhase.RL_PICKUP
            self.other_players_completed = 0
    
    def should_execute_other_players(self):
        return self.current_phase == TurnPhase.OTHER_PLAYERS
    
    def is_round_complete(self):
        return self.current_phase == TurnPhase.ROUND_COMPLETE
    def _terminate_game(self):
"""
"""
class ActionMaskWrapper(gym.Wrapper):
    def step(self, action_id):
        mask = self.env._return_valid_actions(return_mask=True)

        if mask[action_id] == 0:
            # Invalid → resample uniformly from valid actions
            valid_ids = np.where(mask == 1)[0]
            action_id = np.random.choice(valid_ids)
            invalid_action = True
        else:
            invalid_action = False

        obs, reward, terminated, truncated, info = self.env.step(action_id)
        info["invalid_action"] = invalid_action
        return obs, reward, terminated, truncated, info
"""