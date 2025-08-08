import random

class Company:
    def __init__(self, name, total_shares, current_shares):
        self._name = name
        self._total_shares = total_shares
        self._current_shares = current_shares
    def get_share_count(self, player):
        share_count = 0
        for card in player._shares:
            if card._company == self._name:
                share_count += 1
        return share_count
    def get_majority_holder(self, player_list):
        for p in player_list:
            pass
    def __str__(self):
        return f"(Name: {self._name}, Total Shares: {self._total_shares}, Current Shares: {self._current_shares})"

class Player:
    def __init__(self, number, coins, hand, shares, chips, human):
        self._number = number
        self._coins = coins
        self._hand = hand
        self._shares = shares
        self._chips = chips
        self._human = human
    
    def take_card_from_pile(self, deck):
        self._hand.append(deck[0])
        del deck[0]
    
    def take_card_from_market_by_choice(self, market, company_name, coins_amount):
        """Take a specific card from market by company and coins"""
        if not company_in_market(market, company_name):
            return False
        
        if self.check_for_chip(company_name):
            return False
        
        for card in market:
            if card._company == company_name and card._coins_on == coins_amount:
                self._coins += card._coins_on
                card._coins_on = 0
                self._hand.append(card)
                market.remove(card)
                return True
        return False
    
    def add_card_to_shares(self, card):
        self._shares.append(card)
        self._hand.remove(card)
    
    def add_card_to_market(self, card, market):
        market.append(card)
        self._hand.remove(card)
    
    def add_chip(self, company, player_list):
        if check_for_monopoly(player_list, company) == False:
            self._chips.add(company)
        else:
            share_count = company.get_share_count(self)
            max_shares = find_monopoly_value(player_list, company)
            if share_count > max_shares:
                self._chips.add(company)
    
    def remove_chip(self, company, player_list):
        if company in self._chips:
            share_count = company.get_share_count(self)
            max_shares = find_monopoly_value(player_list, company)
            if share_count < max_shares:
                self._chips.remove(company)
    
    def check_for_chip(self, company_name):
        has_monopoly = False
        for chip in self._chips:
            if chip._name == company_name:
                has_monopoly = True 
        return has_monopoly
    
    # Player decision methods - override these for AI players
    def choose_pickup_action(self, market, deck):
        """Choose between 'from deck' or 'from market'. Override for AI players."""
        if not self._human:
            return "from deck"  # Default AI behavior
        
        print("Pick up from the deck, or pick up from the market? Type 'from deck' or 'from market'.")
        return input()
    
    def choose_market_card(self, market):
        """Choose which card to take from market. Override for AI players."""
        if not self._human:
            # Simple AI: take first available card
            available_cards = [c for c in market if not self.check_for_chip(c._company)]
            if available_cards:
                card = available_cards[0]
                return card._company, card._coins_on
            return None, None
        
        print("Which card?")
        print(f"Type one of these companies: {get_card_list(market)}")
        company_input = input()
        print(f"Type the coins")
        coins_input = int(input())
        return company_input, coins_input
    
    def choose_putdown_action(self, market, player_list, company_list):
        """Choose between 'to shares' or 'to market'. Override for AI players."""
        if not self._human:
            return "to shares"  # Default AI behavior
        
        print("Put a card into your shares, or put a card into the market. Type 'to shares' or 'to market'.")
        return input()
    
    def choose_card_from_hand(self, action_type):
        """Choose which card from hand to play. Override for AI players."""
        if not self._human:
            # Simple AI: choose first card
            if self._hand:
                return self._hand[0]._company
            return None
        
        print(f"Choose a card: {get_card_dictionary(self._hand)}")
        return input()
    
    def __str__(self):
        return f"(Player Number: {self._number}, Current Coins: {self._coins}, Hand: {self._hand}, Shares: {self._shares}, Anti-Monopoly Chips: {self._chips}, Human: {self._human})"

class Card:
    def __init__(self, company, coins_on):
        self._company = company
        self._coins_on = coins_on
    def __eq__(self, other):
        return self._company == other._company
    def __str__(self):
        return f"(Card Type: {self._company})"
    def in_market(self, market):
        in_market = False
        completed = False
        while completed == False:
            for card in market:
                if card._company == self._company:
                    in_market = True
            completed = True
        return in_market

# AI Player class that extends Player with different decision making
class AIPlayer(Player):
    def __init__(self, number, coins, hand, shares, chips):
        super().__init__(number, coins, hand, shares, chips, False)
    
    def choose_pickup_action(self, market, deck):
        """AI logic for choosing pickup action"""
        # More sophisticated AI could analyze market conditions here
        if len(market) == 0 or len(deck) < 5:  # Example: prefer deck when market empty or deck running low
            return "from deck"
        return "from market"
    
    def choose_market_card(self, market):
        """AI logic for choosing market card"""
        available_cards = [c for c in market if not self.check_for_chip(c._company)]
        if available_cards:
            # Could add logic to prefer certain companies or cheaper cards
            card = available_cards[0]
            return card._company, card._coins_on
        return None, None
    
    def choose_putdown_action(self, market, player_list, company_list):
        """AI logic for choosing putdown action"""
        # Could analyze whether to build shares or manipulate market
        return "to shares"
    
    def choose_card_from_hand(self, action_type):
        """AI logic for choosing card from hand"""
        if not self._hand:
            return None
        # Could add logic to choose strategically
        return self._hand[0]._company

default_companies = [["Giraffe Beer", 5],["Bowwow Games",6],["Flamingo Soft",7],["Octo Coffee", 8],["Hippo Powertech", 9],["Elephant Mars Travel", 10]]
additional_companies = [["Woofy Railway", 11]]
market = []
player_actions = ["from deck", "to shares", "from market", "to market"]

def create_companies(starting_company_list):
    company_objects = []
    for c in starting_company_list:
        company = Company(c[0], c[1], 0)
        company_objects.append(company)
    return company_objects

def create_deck(company_list):
    deck = []
    for company in company_list:
        n = 1
        while n <= company._total_shares:
            new_card = Card(company._name, 0)
            deck.append(new_card)
            n += 1
    return deck

def create_players(no_players, no_humans):
    player_list = []
    n = 1
    humans_created = 0
    while n <= no_players:
        if humans_created < no_humans:
            player = Player(n, 10, [], [], set(), True)
            humans_created += 1
        else:
            # Create AI player
            player = AIPlayer(n, 10, [], [], set())
        player_list.append(player)
        n += 1
    return player_list

def print_game_status(company_list):
    for i in company_list:
        print(i)

def print_player_status(player_list):
    for i in player_list:
        print(i)

def print_deck(deck):
    for i in deck:
        print(i)

def shuffle_deck(deck):
    random.shuffle(deck)

def prepare_deck(deck, cutoff):
    shuffle_deck(deck)
    return deck[cutoff:]

def deal_hands(deck, cutoff, player_list):
    counter = 0
    while counter < cutoff:
        for p in player_list:
            p._hand.append(deck[0])
            del deck[0]
        counter += 1

def company_in_market(market, company_name):
    for card in market:
        if card._company == company_name:
            return True
    return False

def get_card_dictionary(card_list):
    card_dictionary = dict()
    for card in card_list:
        company = card._company
        card_dictionary[company] = card_dictionary.get(company, 0) + 1
    return card_dictionary

def get_card_list(list):
    card_list = []
    for card in list:
        company = card._company
        coins = card._coins_on
        card_list.append([company, coins])
    return card_list 

# Refactored action functions - now player agnostic
def execute_pickup_action(player, action, market, deck):
    """Execute pickup action based on player's choice"""
    if action == "from deck":
        coins_required = len(market)
        for card in market:
            if player.check_for_chip(card._company):
                coins_required -= 1
        
        if player._coins >= coins_required:
            if len(deck) > 0:
                player.take_card_from_pile(deck)
                if coins_required != 0:
                    for card in market:
                        if player.check_for_chip(card._company) == False:
                            card._coins_on += 1
                    player._coins -= coins_required
                return True
        else:
            if player._human:
                print("You don't have enough money to pick up from the deck.")
            return False
            
    elif action == "from market":
        if len(market) == 0:
            if player._human:
                print("There aren't any cards in the market right now.")
            return False
        
        company_name, coins_amount = player.choose_market_card(market)
        if company_name is None:
            return False
            
        success = player.take_card_from_market_by_choice(market, company_name, coins_amount)
        if not success and player._human:
            if player.check_for_chip(company_name):
                print("You've got the anti-monopoly chip for that company, you can't play it")
            else:
                print("There isn't one of these in the market.")
        return success
    
    return False

def execute_putdown_action(player, action, player_list, market, company_list):
    """Execute putdown action based on player's choice"""
    card_company = player.choose_card_from_hand(action)
    if card_company is None:
        return False
    
    # Find the chosen card
    chosen_card = None
    for c in player._hand:
        if c._company == card_company:
            chosen_card = c
            break
    
    if chosen_card is None:
        return False
    
    if action == 'to shares':
        # Find company object
        company_obj = None
        for comp in company_list:
            if comp._name == card_company:
                company_obj = comp
                break
        
        if company_obj:
            player.add_card_to_shares(chosen_card)
            player.add_chip(company_obj, player_list)
            for p in player_list:
                p.remove_chip(company_obj, player_list)
            return True
            
    elif action == 'to market':
        player.add_card_to_market(chosen_card, market)
        return True
    
    return False

def check_for_monopoly(player_list, company):
    monopoly = False
    shares_total = 0
    for p in player_list:
        player_shares = company.get_share_count(p)
        shares_total += player_shares
    if shares_total > 1:
        monopoly = True
    return monopoly

def find_monopoly_value(player_list, company):
    max_shares = 0
    for p in player_list:
        player_shares = company.get_share_count(p)
        if player_shares > max_shares:
            max_shares = player_shares
    return max_shares

def play_turn(player, market, deck, player_list, company_list):
    """Play a single turn for any player type"""
    if player._human:
        print(f"Player {player._number}: Your turn!")
        print(f"Your hand is: {get_card_dictionary(player._hand)}")
        print(f"You have {player._coins} coins")
        print(f"The market is: {get_card_dictionary(market)}")
    
    # Pickup phase
    pickup_action = player.choose_pickup_action(market, deck)
    execute_pickup_action(player, pickup_action, market, deck)
    
    if player._human:
        print(f"Your hand is now: {get_card_dictionary(player._hand)}")
        print(f"You now have {player._coins} coins")
    
    # Putdown phase  
    putdown_action = player.choose_putdown_action(market, player_list, company_list)
    execute_putdown_action(player, putdown_action, player_list, market, company_list)
    
    if player._human:
        print(f"Your hand is now: {get_card_dictionary(player._hand)}")
        print(f"Your shares are now: {get_card_dictionary(player._shares)}")
        print(f"Your anti-monopoly chips are now {player._chips}")
        print(f"The market is now {get_card_dictionary(market)}")
    else:
        print(f"Player {player._number}'s shares are now: {get_card_dictionary(player._shares)}")
        print(f"Player {player._number}'s anti-monopoly chips are now {player._chips}")
        print(f"The market is now {get_card_dictionary(market)}")

if __name__ == "__main__":
    company_list = create_companies(default_companies)
    player_list = create_players(4, 1)
    deck = create_deck(company_list)
    deck = prepare_deck(deck, 5)
    deal_hands(deck, 3, player_list)
    
    Finished = False
    game_round = 0
    
    while not Finished:
        game_round += 1
        print(f"Game Round: {game_round}")
        
        if len(deck) == 0:
            Finished = True
        else:
            for player in player_list:
                play_turn(player, market, deck, player_list, company_list)
                
                # Remove this test condition when ready for full game
                if game_round > 5:  # Limit rounds for testing
                    Finished = True
                    break