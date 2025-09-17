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
import s1_game_optimise_for_RL as sg
from enum import Enum

class StartupsEnv(Env):
    def __init__(self, total_players, num_humans, default_company_list):
        super().__init__()
        self.total_players = total_players
        self.num_humans = num_humans
        self.game_round = 0
        self.default_company_list = default_company_list
        self.company_list, self.player_list, self.deck, self.starting_deck = sg.create_game_RL(self.default_company_list, self.total_players, self.num_humans)
        self.agent_player = self.random_RL_player_selection()
        self.other_players = [p for p in self.player_list if p != self.agent_player]
        self.market = []
        self.state_controller = GameStateController(self.player_list, self.agent_player)
        self._setup_action_space() 
        self.state = self._get_observation()
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self._get_observation().shape[0],), dtype=np.float32)
        
    def step(self, action_id):
        reward = 0
        done = False
        info = {}
        g_round = 0
        
        # First, handle other players' turns until it's the RL agent's turn
        while (self.state_controller.get_current_phase() == TurnPhase.OTHER_PLAYERS):
            self._execute_other_players_turn()
        
        # Now it should be the RL agent's turn
        current_phase = self.state_controller.get_current_phase()
        #print(f"Step starting - Current phase: {current_phase}, Hand size: {len(self.agent_player._hand)}")

        if self.state_controller.get_current_phase() not in [TurnPhase.RL_PICKUP, TurnPhase.RL_PUTDOWN]:
            return self.state, reward, False, True, {"error": "Not RL agent's turn"}
        
        # Validate the action
        if action_id not in self.action_mapping:
            return self.state, reward-10, False, True, {"invalid_action": True}
        
        action = self.action_mapping[action_id]
        stop = False
        
        # Execute RL agent's turn
        if self.state_controller.get_current_phase() == TurnPhase.RL_PICKUP and stop == False:
            g_round += 1
            if not self._return_valid_action_check(action):
                #print(f"Invalid pickup action attempted: {action}")
                return self.state, reward-10, False, True, {"invalid_action": True}
            try:
                #print(f"Executing action {action} in phase {current_phase}")
                #print(f"Hand size before action: {len(self.agent_player._hand)}")
        
                sg.execute_pickup(self.agent_player, action, self.market, self.deck)
                reward += self._calculate_reward(self.agent_player,g_round)
                #reward += 0.1
                #print(f"Pickup executed. New hand size: {len(self.agent_player._hand)}")
                stop = True
            except:
                #print(f"Error executing pickup: {e}")
                return self.state, -1, False, True, {"invalid_action": True}
                
        elif self.state_controller.get_current_phase() == TurnPhase.RL_PUTDOWN and stop == False:
            if not self._return_valid_action_check(action):
                #print(f"Invalid putdown action attempted: {action}")
                return self.state, reward-1, False, True, {"invalid_action": True}
            try:
                sg.execute_putdown(self.agent_player, action, self.player_list, self.market, self.company_list)
                #reward += 0.1
                #print(f"Putdown executed. New hand size: {len(self.agent_player._hand)}")
                reward += self._calculate_reward(self.agent_player,g_round)
                stop = True
                
            except:
                return self.state, -1, False, True, {"invalid_action": True}
        
        # After RL agent's turn, execute remaining other players if needed
        self.state_controller._change_phase()
        while (self.state_controller.get_current_phase() == TurnPhase.OTHER_PLAYERS):
            self._execute_other_players_turn()

        #reward -= (g_round / 50 if g_round > 10 else 0)
        #reward += self._calculate_reward(self.agent_player,g_round)
        info = {"intermediate_reward": reward}
        
        terminated = len(self.deck) == 0        
        
        if terminated:
            sg.end_game_and_score(self.player_list, self.company_list)
            reward += self._calculate_final_reward()
            info = {"final_reward": reward}
        
        self._setup_action_space()
        self.state = self._get_observation()
        
        return self.state, reward, terminated, False, info

    def reset(self):
        self.company_list, self.player_list, self.deck, self.starting_deck = sg.create_game_RL(self.default_company_list, self.total_players, self.num_humans)
        self.market = []
        self.game_round = 0
        self.agent_player = self.random_RL_player_selection()
        self.other_players = [p for p in self.player_list if p != self.agent_player]
        self.state_controller = GameStateController(self.player_list, self.agent_player)
        self._setup_action_space() 
        self.state = self._get_observation()
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self._get_observation().shape[0],), dtype=np.float32)
        return self.state, {"info": "Game reset"}

    def reward_and_return(self, g_round):
        reward += self._calculate_reward(self.agent_player,g_round)
        info = {"intermediate_reward": reward}
        
        terminated = len(self.deck) == 0        
        
        if terminated:
            sg.end_game_and_score(self.player_list, self.company_list)
            reward += self._calculate_final_reward()
            info = {"final_reward": reward}
        
        self._setup_action_space()
        self.state = self._get_observation()
        
        return self.state, reward, terminated, False, info

    def _get_observation(self):
        player = self.agent_player
        self.other_players = [p for p in self.player_list if p != self.agent_player]
        # player_coins
        player_coins = player._coins
        # player_hand
        player_hand = list(player._hand) # might want to include card values?
        # player_shares
        player_shares = list(player._shares)
        # player chips
        player_chips = set(player._chips)
        #market cards
        market_cards = list(self.market)
        # market card coins
        market_card_coins = [card._coins_on for card in market_cards]
        # other player shares
        other_player_shares = [list(player._shares) for player in self.other_players]
        # other player coins
        other_player_coins = [player._coins for player in self.other_players]
        # other player chips
        other_player_chips = [list(player._chips) for player in self.other_players]
        # other player hand - REMOVE LATER
        #ther_player_hand = [player._hand for player in self.other_players]
        # game phase
        #game_phase = self.state_controller.get_current_phase()

        # Convert to RL-friendly format - other_player_handREMOVE LATER
        return self._convert_to_numeric_observation(player_coins, player_hand, player_shares, player_chips, market_cards, market_card_coins, other_player_shares, other_player_coins, other_player_chips) # , other_player_hand

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
        for other_player in self.other_players:
            obs.append(float(other_player._coins))
            
            other_shares = sg.get_card_dictionary(other_player._shares)
            for company in self.company_list:
                obs.append(float(other_shares.get(company._name, 0)))

            other_chips = sg.get_company_set(other_player)
            for company in self.company_list:
                obs.append(1.0 if company._name in other_chips else 0.0)
            
            # REMOVE LATER in training, this should be hidden
           #other_hand = sg.get_card_dictionary(other_player._hand)
           #for company in self.company_list:
                #bs.append(float(other_hand.get(company._name, 0)))
        
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
        #print("Action Space Mapping:")
        for action_id, action in self.action_mapping.items():
            pass
            # Assuming Action objects have attributes like .type and .target
            #print(f"  Action {action_id}: {action.type} {action.target if hasattr(action, 'target') and action.target else ''}")

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
        # I think your action is returning [type, target] where target is a card object
        # and maybe you're comparing it to something where the target is a company
        #print(f"Checking validity of action: {action}")
        if self.state_controller.current_phase == TurnPhase.RL_PICKUP:
            choices = sg.return_all_pickup_choices(self.agent_player, self.market)
            #print(f"Available pickup choices: {[(i.type, i.target) for i in choices]}")
            #print(f"Agent hand: {[(i._company) for i in self.agent_player._hand]}")
            #print(f"Agent shares: {[(i.type, i.target) for i in self.agent_player._shares]}")
        elif self.state_controller.current_phase == TurnPhase.RL_PUTDOWN:
            choices = sg.return_all_putdown_choices(self.agent_player, self.company_list)
            #print(f"Available putdown choices: {[(i.type, i.target) for i in choices]}")
            #print(f"Agent hand: {[(i._company) for i in self.agent_player._hand]}")
            #print(f"Agent shares: {[(i[0], i[1]) for i in self.agent_player._shares]}")

        action_company = action.target._company if hasattr(action.target, '_company') else getattr(action.target, '_name', action.target)

        check = False
        for c in choices:
            choice_company = c.target._company if hasattr(c.target, '_company') else getattr(c.target, '_name', c.target)
            if action == c:
                check = True
            elif str(action) == str(c):
                check = True
            elif action.type == c.type and action_company == choice_company:
                check = True
            #elif action[0] == c[0] and action[1] == c[1]:
            #check = True
        #print(f"Action valid: {check}")
        return check

    def get_valid_actions(self, state):
        choices = self.action_mapping.items()
        valid_actions = [action_id for action_id, action in self.action_mapping.items() if self._return_valid_action_check(action)]

        #for c in choices:
                #print("Choice:", c[0], c[1], "in action_mapping?", c in valid_actions)
        #print("Phase:", self.state_controller.get_current_phase())
        #if len(valid_actions) == 0:
            #print("BUG: No valid actions found!")
            #print("Choices returned:", choices)
            #print("Action mapping values:", list(self.action_mapping.values())[:10])
            
        return valid_actions

    def _calculate_reward(self, player, game_round):
        # placeholder - just a sparse reward for now
        # this will be slower, but I don't want to impose strategies
        #reward = self.more_cards_reward(game_round) - 0.001
        reward = (sg.simulate_end_game_and_score(self.player_list, self.company_list, self.agent_player, self.starting_deck) - self.agent_player._starting_coins)
        #reward += self._get_coins_for_score() * 0.01
        return reward

    def more_cards_reward(self,game_round):
        reward = 0
        c_dict = dict()
        highest_shares = dict()
        for comp in self.default_company_list:
            company = comp[0]
            highest_shares[company] = 0
            c_dict[company] = 0
            for p in self.player_list:
                shares_dict = sg.get_card_dictionary(p._shares)
                if shares_dict.get(company, 0) > highest_shares.get(company, 0) and p != self.agent_player:
                    highest_shares[company] = shares_dict[company]

        for card in self.agent_player._hand:
            company_name = card._company
            count_card_for_player = sg.count_card(self.agent_player, company_name)
            c_dict[company_name] = int(count_card_for_player)

        for key, value in c_dict.items():
            if highest_shares.get(key, 0) > value and value > 0:
                reward -= (0.1 * value + (game_round * 0.1))
            elif highest_shares.get(key, 0) == (value - 1) and highest_shares.get(key, 0) > 0:
                reward += (0.1 * highest_shares.get(key, 0) + (game_round * 0.1))
            elif highest_shares.get(key, 0) == (value - 2) and highest_shares.get(key, 0) > 0:
                reward += (0.05 * highest_shares.get(key, 0) + (game_round * 0.2))

        for default_c in self.default_company_list:
            for key, value in c_dict.items():
                if default_c == key:
                    if value == int(default_c[1]):
                        reward -= 0.05 * int(default_c[1])
                        
        return reward


    def _execute_other_players_turn(self):
        """Execute one other player's turn and advance the game state"""
        current_player = None
        
        # Find the current non-RL player
        for i, p in enumerate(self.player_list):
            if i == self.state_controller.current_player_index and p != self.agent_player:
                current_player = p
                break
        
        if current_player is None:
            # If no current player found, advance to next
            self.state_controller._advance_to_next_player()
            return
        
        # Execute the current player's turn
        pickup_action = current_player.pickup_strategy(current_player, self.market, self.deck, self.player_list)
        if pickup_action:
            sg.execute_pickup(current_player, pickup_action, self.market, self.deck)
        
        putdown_action = current_player.putdown_strategy(current_player, self.market, self.deck, self.player_list)
        if putdown_action:
            sg.execute_putdown(current_player, putdown_action, self.player_list, self.market, self.company_list)
        
        # Advance to next player
        self.state_controller._advance_to_next_player()

    def _calculate_player_rank(self):
        rl_player = self.agent_player
        sorted_players = sorted(self.player_list, key=lambda p: p._coins, reverse=True)
        rl_player_rank = sorted_players.index(rl_player) if rl_player in sorted_players else -1
        return rl_player_rank

    def _get_coins_for_score(self):
        return self.agent_player._coins

    def _calculate_final_reward(self):
        rl_rank = self._calculate_player_rank() # 0 is best
        reward_for_winning = 10
        if rl_rank == 0:
            reward_given_rank = reward_for_winning + 0.1 * self.agent_player._coins
        #elif rl_rank == len(self.player_list) - 1:
        #    reward_given_rank = -5 + 0.1 * self.agent_player._coins
        else:
            reward_given_rank = 0 + 0.1 * self.agent_player._coins
        #total_players = len(self.player_list)
        #reward_given_rank = (reward_for_winning / (2**rl_rank)) + (self.agent_player._coins / total_players)
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
        """Advance to the next player in turn order"""
        self.current_player_index = (self.current_player_index + 1) % len(self.player_list)
        
        if self.player_list[self.current_player_index] == self.agent_player:
            # If it's the RL agent's turn, set appropriate phase
            #if len(self.agent_player._hand) < 4:
            #print(f"RL agent's turn. Hand size: {len(self.agent_player._hand)}")
            self.current_phase = TurnPhase.RL_PICKUP
            #else:
            #self.current_phase = TurnPhase.RL_PUTDOWN
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
        #print(f"Changing phase. Current phase: {self.current_phase}, Hand size: {hand_size}")
        if self.current_phase == TurnPhase.RL_PICKUP and hand_size == 4:
            self.current_phase = TurnPhase.RL_PUTDOWN
        elif self.current_phase == TurnPhase.RL_PUTDOWN and hand_size == 3:
            self.current_phase = TurnPhase.OTHER_PLAYERS
        elif self.current_phase == TurnPhase.OTHER_PLAYERS:
            self._advance_to_next_player()
        #print(f"New phase: {self.current_phase}, Hand size: {hand_size}")

"""
def trained_agent_pickup_strategy(player, market, deck, player_list, trained_agent):
    #Use trained RL agent for pickup decisions
    # Create temporary environment to get state
    temp_env = StartupsEnv(len(player_list), 0, sg.default_companies)
    temp_env.player_list = player_list
    temp_env.market = market
    temp_env.deck = deck
    temp_env.agent_player = player
    temp_env.state_controller.current_phase = TurnPhase.RL_PICKUP
    
    # Get state and valid actions
    state = temp_env._get_observation()
    valid_actions = temp_env.get_valid_actions(state)
    
    if not valid_actions:
        return None
    
    # Get action from trained agent (no exploration)
    action_id = trained_agent.predict(state, valid_actions, deterministic=True)
    
    # Return the actual action
    return temp_env.action_mapping[action_id]

def trained_agent_putdown_strategy(player, market, deck, player_list, trained_agent):
    #Use trained RL agent for putdown decisions
    # Create temporary environment to get state
    temp_env = StartupsEnv(len(player_list), 0, sg.default_companies)
    temp_env.player_list = player_list
    temp_env.market = market
    temp_env.deck = deck
    temp_env.agent_player = player
    temp_env.state_controller.current_phase = TurnPhase.RL_PUTDOWN
    
    # Get state and valid actions
    state = temp_env._get_observation()
    valid_actions = temp_env.get_valid_actions(state)
    
    if not valid_actions:
        return None
    
    # Get action from trained agent (no exploration)
    action_id = trained_agent.predict(state, valid_actions, deterministic=True)
    
    # Return the actual action
    return temp_env.action_mapping[action_id]
"""
# Then in your create_players_RL function, just add this option:
"""
def create_players_with_static_opponent(no_players, no_humans, trained_agent=None):
    #Modified player creation that can use a trained agent as one player
    player_list = []
    n = 1
    humans_created = 0
    assign_trained_agent_to = random.choice(range(2, no_players + 1)) if trained_agent else None
    
    while n <= no_players:
        if humans_created < no_humans:
            player = Player(n, 10, [], [], set(), True)
            player.pickup_strategy = human_pickup_strategy
            player.putdown_strategy = human_putdown_strategy
            humans_created += 1
        elif n == assign_trained_agent_to and trained_agent is not None:
            # This player uses the trained agent
            player = Player(n, 10, [], [], set(), False)
            player.pickup_strategy = lambda p, m, d, pl: trained_agent_pickup_strategy(p, m, d, pl, trained_agent)
            player.putdown_strategy = lambda p, m, d, pl: trained_agent_putdown_strategy(p, m, d, pl, trained_agent)
        else:
            # Regular AI player
            player = Player(n, 10, [], [], set(), False)
            player.pickup_strategy = random_ai_pickup_strategy
            player.putdown_strategy = random_ai_putdown_strategy
        
        player_list.append(player)
        n += 1
    
    return player_list
"""