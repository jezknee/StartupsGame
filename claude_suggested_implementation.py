from gymnasium import Env, spaces
import numpy as np
from abc import ABC, abstractmethod
from enum import Enum

# Your existing Action class would be used here
class Action:
    def __init__(self, action_type, target=None):
        self.type = action_type
        self.target = target
    
    def __str__(self):
        return f"Action({self.type}, {self.target})"

class TurnPhase(Enum):
    RL_PICKUP = "rl_pickup"
    RL_PUTDOWN = "rl_putdown"
    OTHER_PLAYERS = "other_players"

# Core Gymnasium-compliant environment
class StartupsGameEnvironment(Env):
    def __init__(self, total_players, num_humans, default_company_list):
        super().__init__()
        # Initialize game state using your existing functions
        self.company_list, self.player_list, self.deck = self._create_game(default_company_list, total_players, num_humans)
        self.market = []
        self.rl_agent = self._select_rl_agent()
        self.current_phase = TurnPhase.RL_PICKUP
        
        # Set up action space
        self._build_action_mapping()
        self.action_space = spaces.Discrete(len(self.action_mapping))
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, 
                                          shape=(self._get_observation().shape[0],), dtype=np.float32)
    
    def step(self, action_id):
        """Standard Gym interface - only handles RL agent actions"""
        if action_id not in self.action_mapping:
            return self._get_observation(), -10, False, False, {"error": "invalid_action"}
        
        action = self.action_mapping[action_id]
        
        # Execute RL agent's action
        success = self.execute_action(self.rl_agent, action)
        if not success:
            return self._get_observation(), -1, False, False, {"error": "invalid_for_phase"}
        
        # Update phase based on hand size
        self._update_phase_after_rl_action()
        
        # Execute other players if RL agent finished their turn
        if self.current_phase == TurnPhase.OTHER_PLAYERS:
            self._execute_all_other_players()
            self.current_phase = TurnPhase.RL_PICKUP  # Reset for next round
        
        # Calculate reward and check termination
        reward = self._calculate_reward()
        terminated = len(self.deck) == 0
        
        if terminated:
            self._end_game()
        
        self._rebuild_action_mapping()  # Update valid actions
        
        return self._get_observation(), reward, terminated, False, {}
    
    def execute_action(self, player, action):
        """Core game logic - works for any player type"""
        hand_size_before = len(player._hand)
        
        try:
            if action.type == "pickup_deck":
                self._execute_pickup_deck(player)
            elif action.type == "pickup_market":
                self._execute_pickup_market(player, action.target)
            elif action.type == "putdown_shares":
                self._execute_putdown_shares(player, action.target)
            elif action.type == "putdown_market":
                self._execute_putdown_market(player, action.target)
            else:
                return False
            
            return True
        except Exception as e:
            print(f"Action execution failed: {e}")
            return False
    
    def get_valid_actions(self, player=None):
        """Get valid actions for a player (defaults to RL agent)"""
        if player is None:
            player = self.rl_agent
        
        valid_actions = []
        hand_size = len(player._hand)
        
        if hand_size == 3:  # Pickup phase
            # Check deck pickup
            if len(self.deck) > 0:
                coins_needed = sum(1 for card in self.market if not player.check_for_chip(card._company))
                if player._coins >= coins_needed:
                    valid_actions.append(Action("pickup_deck"))
            
            # Check market pickups
            for card in self.market:
                if not player.check_for_chip(card._company):
                    valid_actions.append(Action("pickup_market", card._company))
        
        elif hand_size == 4:  # Putdown phase
            for card in player._hand:
                valid_actions.append(Action("putdown_shares", card._company))
                valid_actions.append(Action("putdown_market", card._company))
        
        return valid_actions
    
    def action_to_id(self, action):
        """Convert Action object to action_id"""
        for action_id, mapped_action in self.action_mapping.items():
            if mapped_action.type == action.type and mapped_action.target == action.target:
                return action_id
        return None
    
    def reset(self, **kwargs):
        """Reset environment for new episode"""
        self.company_list, self.player_list, self.deck = self._create_game(
            self.default_company_list, len(self.player_list), self.num_humans)
        self.market = []
        self.current_phase = TurnPhase.RL_PICKUP
        self._build_action_mapping()
        return self._get_observation(), {}
    
    # Internal methods (simplified - you'd use your existing game logic)
    def _create_game(self, company_list, total_players, num_humans):
        # Use your existing sg.create_game function
        pass
    
    def _execute_pickup_deck(self, player):
        # Use your existing pickup logic
        coins_needed = sum(1 for card in self.market if not player.check_for_chip(card._company))
        player._coins -= coins_needed
        for card in self.market:
            if not player.check_for_chip(card._company):
                card._coins_on += 1
        player._hand.append(self.deck.pop(0))
    
    def _execute_pickup_market(self, player, company_name):
        # Use your existing market pickup logic
        pass
    
    def _execute_putdown_shares(self, player, company_name):
        # Use your existing putdown to shares logic
        pass
    
    def _execute_putdown_market(self, player, company_name):
        # Use your existing putdown to market logic
        pass
    
    def _update_phase_after_rl_action(self):
        hand_size = len(self.rl_agent._hand)
        if self.current_phase == TurnPhase.RL_PICKUP and hand_size == 4:
            self.current_phase = TurnPhase.RL_PUTDOWN
        elif self.current_phase == TurnPhase.RL_PUTDOWN and hand_size == 3:
            self.current_phase = TurnPhase.OTHER_PLAYERS
    
    def _execute_all_other_players(self):
        for player in self.player_list:
            if player == self.rl_agent:
                continue
            
            # Execute pickup
            pickup_action = player.pickup_strategy(player, self.market, self.deck, self.player_list)
            if pickup_action:
                self.execute_action(player, pickup_action)
            
            # Execute putdown
            putdown_action = player.putdown_strategy(player, self.market, self.deck, self.player_list)
            if putdown_action:
                self.execute_action(player, putdown_action)
    
    def _build_action_mapping(self):
        self.action_mapping = {}
        valid_actions = self.get_valid_actions()
        for i, action in enumerate(valid_actions):
            self.action_mapping[i] = action
    
    def _rebuild_action_mapping(self):
        self._build_action_mapping()
        self.action_space = spaces.Discrete(len(self.action_mapping))
    
    def _get_observation(self):
        # Your existing observation logic
        return np.array([1.0, 2.0, 3.0])  # Placeholder
    
    def _calculate_reward(self):
        return -0.01  # Your existing reward logic
    
    def _end_game(self):
        # Your existing end game logic
        pass


# Player Interface Abstraction
class PlayerInterface(ABC):
    @abstractmethod
    def choose_action(self, game_state, valid_actions):
        pass

class HumanPlayerInterface(PlayerInterface):
    def choose_action(self, game_state, valid_actions):
        print("Your options:")
        for i, action in enumerate(valid_actions):
            print(f"{i}: {action}")
        
        while True:
            try:
                choice = int(input("Choose action number: "))
                if 0 <= choice < len(valid_actions):
                    return valid_actions[choice]
                else:
                    print("Invalid choice, try again")
            except ValueError:
                print("Please enter a number")

class AIPlayerInterface(PlayerInterface):
    def __init__(self, strategy_func):
        self.strategy_func = strategy_func
    
    def choose_action(self, game_state, valid_actions):
        # Convert your existing strategy functions to work with this interface
        # This is where you'd call your avoid_loss_ai or random_ai strategies
        return self.strategy_func(game_state, valid_actions)

class RLPlayerInterface(PlayerInterface):
    def __init__(self, trained_model):
        self.model = trained_model
    
    def choose_action(self, game_state, valid_actions):
        # This would use your trained RL model
        observation = game_state  # Convert to appropriate format
        action_id = self.model.predict(observation)
        return valid_actions[action_id] if action_id < len(valid_actions) else valid_actions[0]


# Game Wrapper for Mixed Games
class GameOrchestrator:
    def __init__(self, env):
        self.env = env
    
    def play_mixed_game(self, player_interfaces):
        """
        player_interfaces: dict mapping Player objects to PlayerInterface objects
        """
        observation, info = self.env.reset()
        
        while True:
            current_player = self.env.rl_agent  # Or determine current player
            interface = player_interfaces[current_player]
            
            if isinstance(interface, RLPlayerInterface):
                # Use standard Gym interface
                valid_actions = self.env.get_valid_actions()
                action = interface.choose_action(observation, valid_actions)
                action_id = self.env.action_to_id(action)
                observation, reward, terminated, truncated, info = self.env.step(action_id)
            else:
                # Use direct action execution
                valid_actions = self.env.get_valid_actions()
                action = interface.choose_action(observation, valid_actions)
                success = self.env.execute_action(current_player, action)
                observation = self.env._get_observation()
                terminated = len(self.env.deck) == 0
            
            if terminated:
                print("Game finished!")
                break


# Example usage:
if __name__ == "__main__":
    # For RL Training - pure Gymnasium interface
    env = StartupsGameEnvironment(total_players=4, num_humans=0, default_company_list=[])
    obs, info = env.reset()
    
    for _ in range(100):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated:
            obs, info = env.reset()
    
    # For Mixed Games
    orchestrator = GameOrchestrator(env)
    player_interfaces = {
        env.player_list[0]: RLPlayerInterface(trained_model=None),  # Your trained model
        env.player_list[1]: HumanPlayerInterface(),
        env.player_list[2]: AIPlayerInterface(lambda gs, va: va[0]),  # Simple AI
    }
    
    # orchestrator.play_mixed_game(player_interfaces)