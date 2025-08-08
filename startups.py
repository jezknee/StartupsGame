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
    def take_card_from_market(self, market):
        print("Which card?")
        print(f"Type one of these companies: {get_card_list(market)}")
        company_input = input()
        print(f"Type the coins")
        coins_input = int(input())
        if company_in_market(market, company_input):
            if self.check_for_chip(company_input) == False:  
                completed = False
                for c in market:
                    while completed == False:
                        if c._company == company_input and c._coins_on == coins_input:
                            c_zero = c
                            self._coins += c._coins_on
                            c_zero._coins_on = 0
                            self._hand.append(c_zero)
                            market.remove(c)
                            completed = True
            elif self.check_for_chip(company_input):
                print("You've got the anti-monopoly chip for that company, you can't play it")
        else:
            print("There isn't one of these in the market.")
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

"""
class Market:
    def __init__(self, cards):
        self._cards = cards
    def __str__(self):
        return f"(Cards: {self._cards})"
"""

default_companies = [["Giraffe Beer", 5],["Bowwow Games",6],["Flamingo Soft",7],["Octo Coffee", 8],["Hippo Powertech", 9],["Elephant Mars Travel", 10]]
additional_companies = [["Woofy Railway", 11]]
market = []
player_actions_pick_up = ["from deck", "from market"]
player_actions_put_down = ["to shares", "to market"]
game_stages = ["pick_up", "put_down", "scoring"]

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
        elif humans_created == no_humans:
            player = Player(n, 10, [], [], set(), False)
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

def company_in_market(company_name):
    in_market = False
    completed = False
    while completed == False:
        for card in market:
            if card._company == company_name:
                in_market = True
        completed = True
    return in_market

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

def check_pick_up_from_deck(deck):
    check = True
    if len(deck) == 0:
        check = False
    return check

def check_pick_up_from_market(player, market):
    check = False 
    if len(market) > 0:
        for card in market:
            if check_pick_up_card(player, card):
                check = True
                break 
    return check

def check_pick_up_card(player, card):
    check = True
    if player.check_for_chip(card._company):
        check = False
    return check

def pick_up_action_choice(player, market, deck):
    """Return list of valid pickup actions for the player"""
    choices = []
    
    for action in player_actions_pick_up:
        if action == "from deck":
            if check_pick_up_from_deck(deck):
                coins_required = len(market)
                for card in market:
                    if player.check_for_chip(card._company):
                        coins_required -= 1
                if player._coins >= coins_required:
                    choices.append(action)
                    
        elif action == "from market":
            if check_pick_up_from_market(player, market):
                choices.append(action)
    
    return choices

def put_down_action_choice(player):
    """Return list of valid putdown actions for the player"""
    choices = []
    
    # Player can only put down cards if they have cards in hand
    if len(player._hand) > 0:
        for action in player_actions_put_down:
            choices.append(action)  # Both "to shares" and "to market" are always valid if you have cards
    
    return choices


def picking_up_card(player, action, market, deck):
    choices = pick_up_action_choice(player, market, deck)
    if action in choices:
        if action == "from deck":
            coins_required = len(market)
            for card in market:
                if player.check_for_chip(card._company):
                    coins_required -= 1
            if player._coins >= coins_required:
                player.take_card_from_pile(deck)
                if coins_required != 0:
                    for card in market:
                        if player.check_for_chip(card._company) == False:
                            card._coins_on += 1
                    player._coins -= coins_required
            else:
                print("You don't have enough money to pick up from the market.")
        elif action == "from market":
            if len(market) != 0:
                player.take_card_from_market(market)
            else:
                print("There aren't any cards in the market right now.")
    else:
        print("You can't do that right now.")

def putting_down_card(player, action, player_list, market, company_list):
    if action == 'to shares':
        print(f"Choose a card: {get_card_dictionary(player._hand)}")
        card_company = input()
        for c in player._hand:
            if c._company == card_company:
                chosen_card = c
                break
        company_obj = None
        for comp in company_list:
            if comp._name == card_company:
                company_obj = comp
                break
        player.add_card_to_shares(chosen_card)
        player.add_chip(company_obj, player_list)
        for p in player_list:
            p.remove_chip(company_obj, player_list)
    elif action == 'to market':
        print(f"Choose a card: {get_card_dictionary(player._hand)}")
        card_company = input()
        for c in player._hand:
            if c._company == card_company:
                chosen_card = c
                player._hand.remove(c)
                break
        player.add_card_to_market(chosen_card, market)


def check_for_monopoly(player_list, company):
    # changed this logic because I was adding the first share before checking the monopoly
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
            for p in player_list:
                if p._human:
                    print(f"Player {p._number}: Your turn!")
                    print(f"Your hand is: {get_card_dictionary(p._hand)}")
                    print(f"You have {p._coins} coins")
                    print(f"The market is: {get_card_dictionary(market)}")
                    while True:
                        up_options = pick_up_action_choice(p, market, deck)
                        print(f"Pick up from the deck, or pick up from the market? Type one of '{up_options}.")
                        pick_up_action = input()
                        if pick_up_action in up_options:
                            picking_up_card(p, pick_up_action, market, deck)
                            break 
                        else:
                            print("That's not an option. Please try again.")
                    print(f"Your hand is now: {get_card_dictionary(p._hand)}")
                    print(f"You now have {p._coins} coins")
                    while True:
                        down_options = put_down_action_choice(p)
                        print(f"Put a card into your shares, or put a card into the market. Type one of {down_options}.")
                        put_down_action = input()
                        if put_down_action in down_options:
                            putting_down_card(p, put_down_action, player_list, market, company_list)
                            break
                        else:
                            print("That's not an option. Please try again.")
                    print(f"Your hand is now: {get_card_dictionary(p._hand)}")
                    print(f"Your shares are now: {get_card_dictionary(p._shares)}")
                    print(f"Your anti-monopoly chips are now {p._chips}")
                    print(f"The market is now {get_card_dictionary(market)}")
                elif not p._human:
                    up_choices = pick_up_action_choice(p, market, deck)
                    if len(up_choices) > 0:
                        pick_up_action = random.choice(up_choices)
                        picking_up_card(p, pick_up_action, market, deck)

                    down_choices = put_down_action_choice(p)
                    if len(down_choices) > 0:
                        put_down_action = random.choice(down_choices)
                        putting_down_card(p, put_down_action, player_list, market, company_list)
                        
                    print(f"The market is now {get_card_dictionary(market)}")
                    print(f"Player {p._number}'s shares are now: {get_card_dictionary(p._shares)}")
                    print(f"Player {p._number}'s anti-monopoly chips are now {p._chips}")






        