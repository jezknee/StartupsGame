# UI-Ready Game Implementation Example
# This shows how your existing code would integrate with a UI

import random
from enum import Enum

# Your existing classes (Company, Card, etc.) would stay the same
# I'll just include the modified parts for UI integration

class GameState(Enum):
    PICKUP_PHASE = "pickup"
    PUTDOWN_PHASE = "putdown"
    GAME_OVER = "game_over"
    WAITING = "waiting"

class UIPlayer:
    """UI-enabled player that doesn't use input() calls"""
    def __init__(self, number, coins, hand, shares, chips):
        self._number = number
        self._coins = coins
        self._hand = hand
        self._shares = shares
        self._chips = chips
        self._human = True
        
        # UI state tracking
        self.waiting_for_action = None
        self.valid_choices = []

class UIGameEngine:
    """Game engine that integrates with UI instead of console input"""
    
    def __init__(self, company_list, num_players=4):
        self.company_list = company_list
        self.player_list = self.create_ui_players(num_players)
        self.deck = self.create_deck(company_list)
        self.market = []
        
        # Game state
        self.current_player_index = 0
        self.game_state = GameState.WAITING
        self.game_round = 0
        
        # UI callbacks - these would be set by your UI framework
        self.on_state_changed = None  # Callback for UI updates
        self.on_invalid_action = None  # Callback for error messages
        
    def start_game(self):
        """Initialize and start the game"""
        self.deck = self.prepare_deck(self.deck, 5)
        self.deal_hands(self.deck, 3, self.player_list)
        self.start_next_turn()
        
    def start_next_turn(self):
        """Start the next player's turn"""
        self.game_round += 1
        
        if len(self.deck) == 0:
            self.game_state = GameState.GAME_OVER
            self.notify_ui()
            return
            
        current_player = self.get_current_player()
        self.game_state = GameState.PICKUP_PHASE
        
        # Set what the current player can do
        current_player.waiting_for_action = "pickup"
        current_player.valid_choices = self.get_valid_pickup_choices(current_player)
        
        self.notify_ui()
    
    def get_current_player(self):
        return self.player_list[self.current_player_index]
    
    def get_valid_pickup_choices(self, player):
        """Get list of valid pickup actions for UI to enable/disable buttons"""
        choices = []
        
        # Can always try to pick from deck (validation happens in execution)
        if len(self.deck) > 0:
            coins_required = len(self.market)
            for card in self.market:
                if player.check_for_chip(card._company):
                    coins_required -= 1
            
            if player._coins >= coins_required:
                choices.append({"type": "deck", "cost": coins_required})
        
        # Check each market card
        for i, card in enumerate(self.market):
            if not player.check_for_chip(card._company):
                choices.append({
                    "type": "market_card", 
                    "index": i,
                    "company": card._company,
                    "coins": card._coins_on,
                    "card_object": card
                })
        
        return choices
    
    def get_valid_putdown_choices(self, player):
        """Get list of valid putdown actions"""
        choices = []
        
        for i, card in enumerate(player._hand):
            choices.append({
                "type": "to_shares",
                "card_index": i,
                "company": card._company,
                "card_object": card
            })
            choices.append({
                "type": "to_market", 
                "card_index": i,
                "company": card._company,
                "card_object": card
            })
        
        return choices
    
    # UI Event Handlers - These are called by your UI when user clicks things
    
    def on_deck_clicked(self):
        """Called when player clicks the deck"""
        if self.game_state != GameState.PICKUP_PHASE:
            self.notify_error("Not pickup phase")
            return False
            
        current_player = self.get_current_player()
        
        # Validate this is a legal move
        valid_choices = [c for c in current_player.valid_choices if c["type"] == "deck"]
        if not valid_choices:
            self.notify_error("Cannot pick from deck right now")
            return False
        
        # Execute the pickup
        success = self.execute_pickup_action(current_player, "from deck")
        if success:
            self.advance_to_putdown_phase()
        
        return success
    
    def on_market_card_clicked(self, card_index):
        """Called when player clicks a card in the market"""
        if self.game_state != GameState.PICKUP_PHASE:
            self.notify_error("Not pickup phase")
            return False
            
        if card_index >= len(self.market):
            self.notify_error("Invalid card")
            return False
            
        current_player = self.get_current_player()
        card = self.market[card_index]
        
        # Validate this is a legal move
        valid_choices = [c for c in current_player.valid_choices 
                        if c["type"] == "market_card" and c["index"] == card_index]
        if not valid_choices:
            self.notify_error("Cannot take this card")
            return False
        
        # Execute the pickup
        success = current_player.take_card_from_market_by_choice(
            self.market, card._company, card._coins_on
        )
        
        if success:
            self.advance_to_putdown_phase()
        else:
            self.notify_error("Could not take card")
        
        return success
    
    def on_hand_card_clicked(self, card_index, action_type):
        """Called when player clicks a card in their hand
        action_type should be 'to_shares' or 'to_market'
        """
        if self.game_state != GameState.PUTDOWN_PHASE:
            self.notify_error("Not putdown phase")
            return False
            
        current_player = self.get_current_player()
        
        if card_index >= len(current_player._hand):
            self.notify_error("Invalid card")
            return False
            
        # Validate this is a legal move
        valid_choices = [c for c in current_player.valid_choices 
                        if c["card_index"] == card_index and c["type"] == action_type]
        if not valid_choices:
            self.notify_error("Invalid action for this card")
            return False
        
        card = current_player._hand[card_index]
        
        # Execute the putdown
        success = self.execute_putdown_action(current_player, action_type, card._company)
        
        if success:
            self.advance_to_next_player()
        else:
            self.notify_error("Could not play card")
        
        return success
    
    def advance_to_putdown_phase(self):
        """Move from pickup to putdown phase"""
        current_player = self.get_current_player()
        self.game_state = GameState.PUTDOWN_PHASE
        current_player.waiting_for_action = "putdown"
        current_player.valid_choices = self.get_valid_putdown_choices(current_player)
        self.notify_ui()
    
    def advance_to_next_player(self):
        """Move to next player's turn"""
        self.current_player_index = (self.current_player_index + 1) % len(self.player_list)
        self.start_next_turn()
    
    # Game Logic Functions (adapted from your existing code)
    
    def execute_pickup_action(self, player, action):
        """Your existing pickup logic, adapted"""
        if action == "from deck":
            coins_required = len(self.market)
            for card in self.market:
                if player.check_for_chip(card._company):
                    coins_required -= 1
            
            if player._coins >= coins_required and len(self.deck) > 0:
                player._hand.append(self.deck[0])
                del self.deck[0]
                
                if coins_required != 0:
                    for card in self.market:
                        if not player.check_for_chip(card._company):
                            card._coins_on += 1
                    player._coins -= coins_required
                return True
        
        return False
    
    def execute_putdown_action(self, player, action, card_company):
        """Your existing putdown logic, adapted"""
        # Find the card in player's hand
        chosen_card = None
        for card in player._hand:
            if card._company == card_company:
                chosen_card = card
                break
        
        if chosen_card is None:
            return False
        
        if action == 'to_shares':
            # Find company object
            company_obj = None
            for comp in self.company_list:
                if comp._name == card_company:
                    company_obj = comp
                    break
            
            if company_obj:
                player._shares.append(chosen_card)
                player._hand.remove(chosen_card)
                player.add_chip(company_obj, self.player_list)
                for p in self.player_list:
                    p.remove_chip(company_obj, self.player_list)
                return True
                
        elif action == 'to_market':
            self.market.append(chosen_card)
            player._hand.remove(chosen_card)
            return True
        
        return False
    
    def notify_ui(self):
        """Notify UI that game state has changed"""
        if self.on_state_changed:
            game_data = {
                "current_player": self.current_player_index,
                "game_state": self.game_state.value,
                "round": self.game_round,
                "players": [self.serialize_player(p) for p in self.player_list],
                "market": [self.serialize_card(c) for c in self.market],
                "deck_size": len(self.deck),
                "valid_choices": self.get_current_player().valid_choices if self.game_state in [GameState.PICKUP_PHASE, GameState.PUTDOWN_PHASE] else []
            }
            self.on_state_changed(game_data)
    
    def notify_error(self, message):
        """Notify UI of an error"""
        if self.on_invalid_action:
            self.on_invalid_action(message)
    
    def serialize_player(self, player):
        """Convert player to dictionary for UI"""
        return {
            "number": player._number,
            "coins": player._coins,
            "hand": [self.serialize_card(c) for c in player._hand],
            "shares": [self.serialize_card(c) for c in player._shares],
            "chips": [chip._name for chip in player._chips]
        }
    
    def serialize_card(self, card):
        """Convert card to dictionary for UI"""
        return {
            "company": card._company,
            "coins": card._coins_on
        }
    
    # Your existing helper functions would go here...
    def create_ui_players(self, num_players):
        players = []
        for i in range(1, num_players + 1):
            player = UIPlayer(i, 10, [], [], set())
            players.append(player)
        return players
    
    def create_deck(self, company_list):
        # Your existing create_deck logic
        pass
    
    def prepare_deck(self, deck, cutoff):
        # Your existing prepare_deck logic  
        pass
    
    def deal_hands(self, deck, cutoff, player_list):
        # Your existing deal_hands logic
        pass

# Example of how a UI framework would use this:

class MockUI:
    """Example of how your UI (React, tkinter, pygame, etc.) would integrate"""
    
    def __init__(self):
        # Initialize your UI components here
        self.game_engine = None
    
    def start_new_game(self):
        # Create companies (your existing logic)
        companies = []  # Your company creation logic here
        
        self.game_engine = UIGameEngine(companies, 4)
        
        # Set up callbacks
        self.game_engine.on_state_changed = self.update_ui
        self.game_engine.on_invalid_action = self.show_error
        
        # Start the game
        self.game_engine.start_game()
    
    def update_ui(self, game_data):
        """Called whenever game state changes"""
        print(f"UI Update: Player {game_data['current_player']} turn")
        print(f"Phase: {game_data['game_state']}")
        print(f"Valid actions: {len(game_data['valid_choices'])}")
        
        # Here you would update your UI components:
        # - Update player hands display
        # - Enable/disable clickable elements based on valid_choices
        # - Update market display
        # - Show current player indicator
        
    def show_error(self, message):
        """Called when player tries invalid action"""
        print(f"Error: {message}")
        # Show error message in UI
    
    def on_deck_button_clicked(self):
        """Your UI's deck button click handler"""
        if self.game_engine:
            success = self.game_engine.on_deck_clicked()
            if not success:
                # UI could show some feedback here
                pass
    
    def on_market_card_clicked(self, card_index):
        """Your UI's market card click handler"""
        if self.game_engine:
            success = self.game_engine.on_market_card_clicked(card_index)
    
    def on_hand_card_to_shares_clicked(self, card_index):
        """Player clicked a hand card to put in shares"""
        if self.game_engine:
            success = self.game_engine.on_hand_card_clicked(card_index, "to_shares")
    
    def on_hand_card_to_market_clicked(self, card_index):
        """Player clicked a hand card to put in market"""
        if self.game_engine:
            success = self.game_engine.on_hand_card_clicked(card_index, "to_market")

# Usage example:
if __name__ == "__main__":
    ui = MockUI()
    ui.start_new_game()
    
    # Simulate some UI interactions:
    # ui.on_deck_button_clicked()
    # ui.on_hand_card_to_shares_clicked(0)