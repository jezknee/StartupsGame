import random
import time
import copy
#import startups_RL_environment

class Company:
    def __init__(self, name, total_shares):
        self._name = name
        self._total_shares = total_shares
        #self._current_shares = current_shares
    def get_share_count(self, player):
        share_count = 0
        for card in player._shares:
            if card._company == self._name:
                share_count += 1
        return share_count
    def get_sim_share_count(self, player):
        share_count = 0
        for card in player._simulate_shares:
            if card._company == self._name:
                share_count += 1
        return share_count

    def get_majority_holder(self, player_list):
        company_shares_dictionary = {p: self.get_share_count(p) for p in player_list}
        
        if not company_shares_dictionary:
            return None
        
        # Count how many times the maximum value appears
        max_value = max(company_shares_dictionary.values())
        max_count = list(company_shares_dictionary.values()).count(max_value)
        
        return max(company_shares_dictionary, key=company_shares_dictionary.get) if max_count == 1 else None

    def get_sim_majority_holder(self, player_list):
        company_shares_dictionary = {p: self.get_sim_share_count(p) for p in player_list}
        
        if not company_shares_dictionary:
            return None
        
        # Count how many times the maximum value appears
        max_value = max(company_shares_dictionary.values())
        max_count = list(company_shares_dictionary.values()).count(max_value)
        
        return max(company_shares_dictionary, key=company_shares_dictionary.get) if max_count == 1 else None

    def __eq__(self, other):
        if isinstance(other, Company):
            return self._name == other._name
        return NotImplemented
    def __hash__(self):
        return hash(self._name)  # hash based only on name
    def __str__(self):
        return f"(Name: {self._name}, Total Shares: {self._total_shares})"

class Player:
    def __init__(self, number, coins, hand, shares, chips, human):
        self._number = number
        self._coins = coins
        self._starting_coins = coins
        self._simulate_coins = coins
        self._hand = hand
        self._shares = shares
        self._simulate_shares = shares
        self._chips = chips
        self._human = human
        self._sim_hand = []
        self._last_pickup = None
    def take_card_from_pile(self, deck):
        self._hand.append(deck[0])
        self._last_pickup = deck[0]
        del deck[0]
    def take_card_from_market(self, market, company_name):
        # take card of given company with most coins
        if company_in_market(market, company_name):
            if not self.check_for_chip(company_name):
                best_card = None
                max_coins = -1
                completed = False
                for c in market:
                    """while completed == False:"""
                    if c._company == company_name and c._coins_on > max_coins:
                        best_card = c
                        max_coins = c._coins_on
                
                if best_card:
                    self._coins += best_card._coins_on
                    market.remove(best_card)
                    best_card._coins_on = 0
                    self._hand.append(best_card)
                    self._last_pickup = best_card

            elif self.check_for_chip(company_name):
                pass

        else:
            pass
    def add_card_to_shares(self, card):
        self._shares.append(card)
        self._hand.remove(card)
        self._last_pickup = None
    def simulate_add_card_to_shares(self, card):
        self._simulate_shares.append(card)
    def add_card_to_market(self, card, market):
        market.append(card)
        self._hand.remove(card)
        self._last_pickup = None
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
    def check_for_picked_up(self, company_name):
        picked_up = False
        if self._last_pickup is not None and self._last_pickup._company == company_name:
            picked_up = True
        return picked_up
    def put_hand_in_shares(self):
        hand_copy = self._hand.copy()
        for card in hand_copy:
            self.add_card_to_shares(card)
    def simulate_put_hand_in_shares(self):
        hand_copy = self._hand.copy()
        self._simulate_shares = self._shares.copy()
        for card in hand_copy:
            self.simulate_add_card_to_shares(card)
    def simulate_put_sim_hand_in_shares(self):
        hand_copy = self._sim_hand.copy()
        self._simulate_shares = self._shares.copy()
        for card in hand_copy:
            self.simulate_add_card_to_shares(card)
    def __str__(self):
        return f"(Player Number: {self._number}, Current Coins: {self._coins}, Hand: {self._hand}, Shares: {self._shares}, Anti-Monopoly Chips: {self._chips}, Human: {self._human})"

class Card:
    def __init__(self, company, coins_on):
        self._company = company
        self._coins_on = coins_on
    def __eq__(self, other):
        if isinstance(other, Card):
            return self._company == other._company
        return NotImplemented
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

class Action:
    def __init__(self, action_type, target=None):
        self.type = action_type   # e.g., "pickup_deck", "pickup_market", "putdown_shares"
        self.target = target      # e.g., company name
    def __str__(self):
        return f"Action Type: {self.type}, Card: {self.target}"
    def __eq__(self, other):
        if isinstance(other, Action):
            return self.type == other.type and self.target == other.target
        return NotImplemented


default_companies = [["Giraffe Beer", 5],["Bowwow Games",6],["Flamingo Soft",7],["Octo Coffee", 8],["Hippo Powertech", 9],["Elephant Mars Travel", 10]]
additional_companies = [["Woofy Railway", 11]]
market = []
player_actions_pick_up = ["pickup_deck", "pickup_market"]
player_actions_put_down = ["putdown_shares", "putdown_market"]
game_stages = ["pick_up", "put_down", "scoring"]

def create_companies(starting_company_list):
    company_objects = []
    for c in starting_company_list:
        company = Company(c[0], c[1])
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
    assign_avoid_loss_strategy_to = random.choice([2,4])
    while n <= no_players:
        if humans_created < no_humans:
            player = Player(n, 10, [], [], set(), True)
            player.pickup_strategy = human_pickup_strategy
            player.putdown_strategy = human_putdown_strategy
            humans_created += 1
        elif humans_created == no_humans:
            player = Player(n, 10, [], [], set(), False)
            if n == assign_avoid_loss_strategy_to:
                player.pickup_strategy = avoid_loss_ai_pickup_strategy
                player.putdown_strategy = avoid_loss_ai_putdown_strategy
            else:
                player.pickup_strategy = random_ai_pickup_strategy
                player.putdown_strategy = random_ai_putdown_strategy
        player_list.append(player)
        n += 1
    return player_list



def build_bot_pool(pool_size_per_strategy=3):
    pool = []
    for strat_name, (pickup, putdown) in STRATEGIES.items():
        for i in range(pool_size_per_strategy):
            player = Player(-1, 10, [], [], set(), False)  # temp number, fixed later
            player.pickup_strategy = pickup
            player.putdown_strategy = putdown
            pool.append(player)
    return pool

def create_players_RL_old(no_players, no_humans):
    player_list = []
    n = 1
    humans_created = 0
    #assign_RL_strategy_to = random.choice([1,4])
    assign_avoid_loss_strategy_to = random.choice([0,6])
    assign_avoid_loss_strategy_to_2 = 9 #random.choice([1,4])
    assign_avoid_loss_strategy_to_3 = 9 #random.choice([1,4])
    #assign_avoid_loss_strategy_to_4 = 9 #random.choice([1,4])
    assign_gain_money_strategy_to_1 = random.choice([0,6])
    #assign_gain_money_strategy_to_2 = random.choice([1,4])
    assign_seek_loss_strategy_to_1 = random.choice([0,4]) #random.choice(range(len(player_list)))
    assign_same_cards_strategy_to_1 = random.choice([0,4]) #random.choice(range(len(player_list)))
    while n <= no_players:
        if humans_created < no_humans:
            player = Player(n, 10, [], [], set(), True)
            player.pickup_strategy = human_pickup_strategy
            player.putdown_strategy = human_putdown_strategy
            humans_created += 1
        elif humans_created == no_humans:
            player = Player(n, 10, [], [], set(), False)
            if n == assign_avoid_loss_strategy_to or n == assign_avoid_loss_strategy_to_2 or n == assign_avoid_loss_strategy_to_3:
                player.pickup_strategy = avoid_loss_ai_pickup_strategy
                player.putdown_strategy = avoid_loss_ai_putdown_strategy
            elif n == assign_gain_money_strategy_to_1:
                player.pickup_strategy = gain_money_ai_pickup_strategy
                player.putdown_strategy = lose_unwanted_cards_ai_putdown_strategy
            elif n == assign_seek_loss_strategy_to_1:
                player.pickup_strategy = seek_loss_ai_pickup_strategy
                player.putdown_strategy = seek_loss_ai_putdown_strategy
            elif n == assign_same_cards_strategy_to_1:
                player.pickup_strategy = same_cards_ai_pickup_strategy
                player.putdown_strategy = same_cards_ai_putdown_strategy
            else:
                player.pickup_strategy = random_ai_pickup_strategy
                player.putdown_strategy = random_ai_putdown_strategy
        player_list.append(player)
        n += 1
    return player_list

def create_players_RL(no_players, no_humans):
    player_list = []
    
    # First add human players
    if no_humans > 0:
        for n in range(1, no_humans + 1):
            player = Player(n, 10, [], [], set(), True)
            player.pickup_strategy = human_pickup_strategy
            player.putdown_strategy = human_putdown_strategy
            player_list.append(player)
    
    # Build AI pool and sample
    ai_pool = build_bot_pool(pool_size_per_strategy=5)  # generate more than enough AIs
    chosen_ai = random.sample(ai_pool, no_players - no_humans)
    
    # Assign correct player numbers to AIs and add them
    for i, ai in enumerate(chosen_ai, start=no_humans + 1):
        ai._number = i
        player_list.append(ai)
    
    return player_list


def assign_player_strategy(strategy, num, strategy_dict):
    strat_list = []
    i = 1
    while i <= num:
        priority = random.choice([0,100])
        strat_list.append(priority)
        i += 1
    strategy_dict[strategy] = strat_list

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

def simulate_deal_hands(start_deck, cutoff, player_list, skip_player):
    sim_deck = copy.deepcopy(start_deck)
    counter = 0

    known_cards = []
    known_cards.extend(skip_player._hand)  # RL agent knows their own hand
    for p in player_list:
        known_cards.extend(p._shares)  # All shares are visible
    
    known_cards_dict = get_card_dictionary(known_cards)
    deck_dict = get_card_dictionary(sim_deck)

    # Remove known cards from deck
    remaining_deck = []
    for card in sim_deck:
        known_count = known_cards_dict.get(card._company, 0)
        deck_count = deck_dict.get(card._company, 0)
        if known_count < deck_count:
            remaining_deck.append(card)
            known_cards_dict[card._company] = known_cards_dict.get(card._company, 0) + 1
    
    random.shuffle(remaining_deck)

    for p in player_list:
        p._sim_hand = []

    while counter < cutoff:
        for p in player_list:
            if p != skip_player and len(remaining_deck) > 0:
                p._sim_hand.append(remaining_deck[0])
                del remaining_deck[0]
        counter += 1

def company_in_market(market, company_name):
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

def get_company_set(player):
    company_set = set()
    for company in player._chips:
        company_name = company._name
        company_set.add(company_name)
    return company_set

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

def check_put_down_card_to_market(player, card):
    check = True
    if card not in player._hand:
        check = False
    elif card._company == player._last_pickup._company:
        check = False
    return check

def get_all_game_actions(player_actions_pick_up, player_actions_put_down, company_list):
    # gets whole list of actions, whether possible or not
    # returns tuples of (action_type, target_company)
    # fix the inconsistency - pickup_market, not "from market"
    actions = []
    actions.append(Action("pickup_deck", None))  # "from deck" has no target
    for i in player_actions_pick_up:
        if i == "pickup_market":
            for c in company_list:
                actions.append(Action(i, c))

    for i in player_actions_put_down:
        for c in company_list:
            actions.append(Action(i, c))
            
    return actions

def pick_up_action_choice(player, market, deck):
    """Return list of valid pickup actions for the player"""
    choices = []
    
    for action in player_actions_pick_up:
        if action == "pickup_deck":
            if check_pick_up_from_deck(deck):
                coins_required = len(market)
                for card in market:
                    if player.check_for_chip(card._company):
                        coins_required -= 1
                if player._coins >= coins_required:
                    choices.append(action)
                    
        elif action == "pickup_market":
            if check_pick_up_from_market(player, market):
                valid_cards_exist = False
                for card in market:
                    if check_pick_up_card(player, card):
                        valid_cards_exist = True
                        break
                if valid_cards_exist:
                    choices.append(action)
    
    return choices

def put_down_action_choice(player):
    """Return list of valid putdown actions for the player"""
    choices = []
    if len(player._hand) > 0:
        for action_type in player_actions_put_down:
            if action_type == "putdown_shares":
                choices.append(action_type)
            elif check_put_down_card_to_market(player, action_type):
                choices.append(action_type)

    return choices

def picking_up_card(player, action, market, deck):
    choices = pick_up_action_choice(player, market, deck)
    if action in choices:
        if action == "pickup_deck":
            coins_required = len(market)
            for card in market:
                if player.check_for_chip(card._company):
                    coins_required -= 1
            if player._coins >= coins_required:
                player.take_card_from_pile(deck)
                if coins_required != 0:
                    for card in market:
                        if not player.check_for_chip(card._company):
                            card._coins_on += 1
                    player._coins -= coins_required
            else:
                pass
        elif action == "pickup_market":
            if len(market) != 0:
                company_input = input_card_for_pick_up(player, market)
                player.take_card_from_market(market, company_input)
            else:
                pass
                
    else:
        pass
        

def putting_down_card(player, action, player_list, market, company_list, card_company):
    if action == 'putdown_shares':
        chosen_card = None
        company_name = card_company._name if hasattr(card_company, '_name') else card_company
        for c in player._hand:
            if c._company == company_name:
                chosen_card = c
                break
        company_obj = None
        for company in company_list:
            if company._name == company_name:
                company_obj = company
                break
        player.add_card_to_shares(chosen_card)
        player.add_chip(company_obj, player_list)
        for p in player_list:
            p.remove_chip(company_obj, player_list)
    elif action == 'putdown_market':
        company_name = card_company._name if hasattr(card_company, '_name') else card_company
        
        chosen_card = None
        for c in player._hand:
            if c._company == company_name:
                chosen_card = c
                break
        if chosen_card is None:
            return False
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

def input_card_for_pick_up(player, market):
    card_choices = []
    if player._human:
        pass

    for card in market:
        if check_pick_up_card(player, card):
            card_choices.append(card)
    if player._human:
        pass

    elif not player._human:
        card_to_choose = random.choice(card_choices)
        company_input = card_to_choose._company
        #coins_input = card_to_choose._coins_on
    return company_input

def return_all_pickup_choices(player, market):
    actions = []
    coins_required = len(market)
    for card in market:
        if player.check_for_chip(card._company):
            coins_required -= 1
    if player._coins >= coins_required:
        actions.append(Action("pickup_deck"))  # target stays None by design
    for card in market:
        if check_pick_up_card(player, card):
            actions.append(Action("pickup_market", card._company))
    return actions

def return_all_putdown_choices(player, market):
    actions = []
    hand_cards = []
    for c in player._hand:
        hand_cards.append(c)
    for s in hand_cards:
        actions.append(Action("putdown_shares", s._company))
        if not player.check_for_picked_up(s._company):
            actions.append(Action("putdown_market", s._company))
    return actions

def input_card_for_put_down(player):
    card_choices = []
    if player._human:
        pass

    for card in player._hand:
        card_choices.append(card)

    if player._human:
        card_company = ""
        while True:
            card_company = input()
            check = False
            for c in player._hand:
                if c._company == card_company:
                    check = True
                    break 
            if check:
                break
            else: 
                pass
                

    elif not player._human:
        card_chosen = random.choice(card_choices)
        card_company = card_chosen._company

    return card_company

def create_game(default_companies, no_players, no_humans):
    company_list = create_companies(default_companies)
    player_list = create_players(no_players, no_humans)
    deck = create_deck(company_list)
    deck = prepare_deck(deck, 5)
    deal_hands(deck, 3, player_list)
    return company_list, player_list, deck

def create_game_RL(default_companies, no_players, no_humans):
    company_list = create_companies(default_companies)
    player_list = create_players_RL(no_players, no_humans)
    deck = create_deck(company_list)
    starting_deck = copy.deepcopy(deck)
    deck = prepare_deck(deck, 5)
    deal_hands(deck, 3, player_list)
    return company_list, player_list, deck, starting_deck

def empty_hands(player_list):
    for player in player_list:
        player.put_hand_in_shares()

def simulate_empty_hands(player_list):
    for player in player_list:
        player.simulate_put_hand_in_shares()

def simulate_empty_sim_hands(player_list):
    for player in player_list:
        player.simulate_put_sim_hand_in_shares()

"""
def get_all_visible_cards(player, player_list, starting_deck):
    all_visible_cards = dict()
    starting_dict = get_card_dictionary(starting_deck)
    for p in player_list:
        for c in p._shares:
            all_visible_cards.append(c)

    count_card_in_shares = 0
    count_card_in_hand = 0
    for s in player._shares:
        if s._company == company:
            count_card_in_shares += 1
"""


def find_winner_simple(player_list):
    """Find the player with the most coins"""
    if not player_list:
        return None
    
    winner = max(player_list, key=lambda player: player._coins)
    return winner

def human_turn_start_messages(p, market):
    pass

def human_turn_end_messages(p, market):
    pass

def ai_end_turn_messages(p, market):
    pass

def human_pickup_strategy(player, market, deck, player_list):
    human_turn_start_messages(player, market)
    up_options = pick_up_action_choice(player, market, deck)
    
    while True:
        choice = input().strip().lower()
        if choice in up_options:
            if choice == "pickup_market":
                target_company = input_card_for_pick_up(player, market)
                return Action("pickup_market", target_company)
            else:
                return Action("pickup_deck")
        else:
            pass
            

def human_putdown_strategy(player, market, deck, player_list):
    
    down_options = put_down_action_choice(player)
    
    while True:
        choice = input().strip().lower()
        if choice in down_options:
            target_company = input_card_for_put_down(player)
            action_type = "putdown_shares" if choice == "putdown_shares" else "putdown_market"
            if action_type == "putdown_market":
                if not check_put_down_card_to_market(player, target_company):
                    
                    continue
            return Action(action_type, target_company)
        else:
            pass
            
    human_turn_end_messages(p, market)

def random_ai_pickup_strategy(player, market, deck, player_list):
    choices = pick_up_action_choice(player, market, deck)
    if not choices:
        
        return None
    choice = random.choice(choices)
    if choice == "pickup_market":
        target_company = input_card_for_pick_up(player, market)
        action_type = "pickup_market"
        
        return Action(action_type, target_company)
    else:
        return Action("pickup_deck")

def random_ai_putdown_strategy(player, market, deck, player_list):
    choices = put_down_action_choice(player)
    if not choices:
        return None
    while True:
        choice = random.choice(choices)
        target_company = input_card_for_put_down(player)
        if choices == "putdown_market":
            if not check_put_down_card_to_market(player, target_company):
                continue
        
        action_type = "putdown_shares" if choice == "putdown_shares" else "putdown_market"
        return Action(action_type, target_company)

def count_card(player, company):
    count_card_in_shares = 0
    count_card_in_hand = 0
    for s in player._shares:
        if s._company == company:
            count_card_in_shares += 1
    for h in player._hand:
        # may want to make the hand a list of card objects in future, quite confusing
        if h._company == company:
            count_card_in_hand += 1
    return count_card_in_shares + count_card_in_hand

def avoid_loss_ai_pickup_strategy(player, market, deck, player_list):
    choices = return_all_pickup_choices(player, market)
    good_choices = []
    bad_choices = []
    for c in choices:
        #if c.target is None:
        #    continue
        if c.type == "pickup_deck":
            good_choices.append(c)
        if c.type == "pickup_market" and c.target is not None:
            company_name = c.target
            count_card_for_player = count_card(player, company_name)
            for p in player_list:
                shares_dict = get_card_dictionary(p._shares)
                if shares_dict.get(company_name, 0) > (count_card_for_player + 1):
                    bad_choices.append(c)
                else:
                    good_choices.append(c)

    if len(good_choices) == 0:
        good_choices = bad_choices

    choice = random.choice(good_choices)

    return choice

def avoid_loss_ai_putdown_strategy(player, market, deck, player_list):
    choices = return_all_putdown_choices(player, market)

    good_choices = []
    bad_choices = []
    for c in choices:
        company_name = c.target
        count_card_for_player = count_card(player, company_name)
        for p in player_list:
            shares_dict = get_card_dictionary(p._shares)
            if c.type == "putdown_market":
                if shares_dict.get(company_name, 0) == count_card_for_player - 1 and shares_dict.get(company_name, 0) > 0:
                    bad_choices.append(c)
                else:
                    good_choices.append(c)
            elif c.type == "putdown_shares":
                if shares_dict.get(company_name, 0) >= count_card_for_player:
                    bad_choices.append(c)
                else:
                    good_choices.append(c)
            else:
                good_choices.append(c)

    if len(good_choices) == 0:
        good_choices = bad_choices
    
    choice = random.choice(good_choices)

    return choice

def seek_loss_ai_pickup_strategy(player, market, deck, player_list):
    choices = return_all_pickup_choices(player, market)
    good_choices = []
    bad_choices = []
    for c in choices:
        #if c.target is None:
        #    continue
        if c.type == "pickup_deck":
            bad_choices.append(c)
        if c.type == "pickup_market" and c.target is not None:
            company_name = c.target
            count_card_for_player = count_card(player, company_name)
            for p in player_list:
                shares_dict = get_card_dictionary(p._shares)
                if shares_dict.get(company_name, 0) > (count_card_for_player + 1):
                    good_choices.append(c)
                else:
                    bad_choices.append(c)

    if len(good_choices) == 0:
        good_choices = bad_choices

    choice = random.choice(good_choices)

    return choice

def seek_loss_ai_putdown_strategy(player, market, deck, player_list):
    choices = return_all_putdown_choices(player, market)

    good_choices = []
    bad_choices = []
    for c in choices:
        company_name = c.target
        count_card_for_player = count_card(player, company_name)
        for p in player_list:
            shares_dict = get_card_dictionary(p._shares)
            if c.type == "putdown_market":
                if shares_dict.get(company_name, 0) == count_card_for_player - 1 and shares_dict.get(company_name, 0) > 0:
                    good_choices.append(c)
                else:
                    bad_choices.append(c)
            elif c.type == "putdown_shares":
                if shares_dict.get(company_name, 0) >= count_card_for_player:
                    good_choices.append(c)
                else:
                    bad_choices.append(c)
            else:
                bad_choices.append(c)

    if len(good_choices) == 0:
        good_choices = bad_choices
    
    choice = random.choice(good_choices)

    return choice

def same_cards_ai_pickup_strategy(player, market, deck, player_list):
    choices = return_all_pickup_choices(player, market)
    good_choices = []
    bad_choices = []
    for c in choices:
        #if c.target is None:
        #    continue
        if c.type == "pickup_deck":
            bad_choices.append(c)
        if c.type == "pickup_market" and c.target is not None:
            company_name = c.target
            count_card_for_player = count_card(player, company_name)
            if count_card_for_player > 0:
                good_choices.append(c)
            else:
                bad_choices.append(c)

    if len(good_choices) == 0:
        good_choices = bad_choices

    choice = random.choice(good_choices)

    return choice

def same_cards_ai_putdown_strategy(player, market, deck, player_list):
    choices = return_all_putdown_choices(player, market)

    good_choices = []
    bad_choices = []
    ok_choices = []
    for c in choices:
        company_name = c.target
        count_card_for_player = count_card(player, company_name)
        if count_card_for_player > 0:
            if c.type == "putdown_market":
                bad_choices.append(c)
            elif c.type == "putdown_shares":
                good_choices.append(c)
        else:
            ok_choices.append(c)

    if len(good_choices) == 0 and len(ok_choices) != 0:
        good_choices = ok_choices
    elif len(good_choices) == 0 and len(ok_choices) == 0:
        good_choices = bad_choices
    
    choice = random.choice(good_choices)

    return choice

def different_cards_ai_pickup_strategy(player, market, deck, player_list):
    choices = return_all_pickup_choices(player, market)
    good_choices = []
    bad_choices = []
    ok_choices = []
    for c in choices:
        #if c.target is None:
        #    continue
        if c.type == "pickup_deck":
            ok_choices.append(c)
        if c.type == "pickup_market" and c.target is not None:
            company_name = c.target
            count_card_for_player = count_card(player, company_name)
            if count_card_for_player > 1:
                bad_choices.append(c)
            elif count_card_for_player > 0:
                ok_choices.append(c)
            else:
                good_choices.append(c)

    if len(good_choices) == 0 and len(ok_choices) != 0:
        good_choices = ok_choices
    elif len(good_choices) == 0 and len(ok_choices) == 0:
        good_choices = bad_choices

    choice = random.choice(good_choices)

    return choice

def different_cards_ai_putdown_strategy(player, market, deck, player_list):
    choices = return_all_putdown_choices(player, market)

    good_choices = []
    bad_choices = []
    ok_choices = []
    for c in choices:
        company_name = c.target
        count_card_for_player = count_card(player, company_name)
        if count_card_for_player > 1:
            if c.type == "putdown_market":
                good_choices.append(c)
            elif c.type == "putdown_shares":
                bad_choices.append(c)
        elif count_card_for_player == 1:
            if c.type == "putdown_shares":
                bad_choices.append(c)
            else:
                ok_choices.append(c)
        else:
            ok_choices.append(c)

    if len(good_choices) == 0 and len(ok_choices) != 0:
        good_choices = ok_choices
    elif len(good_choices) == 0 and len(ok_choices) == 0:
        good_choices = bad_choices
    
    choice = random.choice(good_choices)

    return choice

def gain_money_ai_pickup_strategy(player, market, deck, player_list):
    choices = return_all_pickup_choices(player, market)

    good_choices = []
    ok_choices = []
    bad_choices = []
    for c in choices:
        #if c.target is None:
        #    continue
        if c.type == "pickup_deck" and len(choices) > 1:
            bad_choices.append(c)
        elif c.type == "pickup_deck":
            good_choices.append(c)
        else:
            if c.type == "pickup_market" and c.target is not None:
                for card in market:
                    if card._company == c.target:
                        ok_choices.append(c)
                        if card._coins_on > 1:
                            good_choices.append(c)
                        break

    if len(good_choices) == 0:
        good_choices = ok_choices
    elif len(good_choices) == 0 and len(ok_choices) == 0:
        good_choices = bad_choices

    choice = random.choice(good_choices)

    return choice

def lose_unwanted_cards_ai_putdown_strategy(player, market, deck, player_list):
    choices = return_all_putdown_choices(player, market)

    good_choices = []
    ok_choices = []
    bad_choices = []
    for c in choices:
        company_name = c.target
        count_card_for_player = count_card(player, company_name)
        count_card_in_market = get_card_dictionary(market).get(company_name, 0)
        for p in player_list:
            shares_dict = get_card_dictionary(p._shares)
            if c.type == "putdown_market":
                if count_card_for_player > 1:
                    bad_choices.append(c)
                elif count_card_in_market > 0:
                    good_choices.append(c)
                else:
                    ok_choices.append(c)
            elif c.type == "putdown_shares":
                if shares_dict.get(company_name, 0) >= count_card_for_player:
                    bad_choices.append(c)
                else:
                    good_choices.append(c)
            else:
                good_choices.append(c)

    if len(good_choices) == 0:
        good_choices = ok_choices
    elif len(good_choices) == 0 and len(ok_choices) == 0:
        good_choices = bad_choices
    
    choice = random.choice(good_choices)

    return choice

STRATEGIES = {
    "random": (random_ai_pickup_strategy, random_ai_putdown_strategy),
    "random_2": (random_ai_pickup_strategy, random_ai_putdown_strategy),
    "avoid_loss": (avoid_loss_ai_pickup_strategy, avoid_loss_ai_putdown_strategy),
    "avoid_loss_2": (avoid_loss_ai_pickup_strategy, avoid_loss_ai_putdown_strategy),
    "seek_loss": (seek_loss_ai_pickup_strategy, seek_loss_ai_putdown_strategy),
    "same_cards": (same_cards_ai_pickup_strategy, same_cards_ai_putdown_strategy),
    "different_cards": (different_cards_ai_pickup_strategy, different_cards_ai_putdown_strategy),
    "gain_money": (gain_money_ai_pickup_strategy, lose_unwanted_cards_ai_putdown_strategy),
    "avoid_seek": (avoid_loss_ai_pickup_strategy, seek_loss_ai_putdown_strategy),
    "seek_avoid": (seek_loss_ai_pickup_strategy, avoid_loss_ai_putdown_strategy),
    "money_same": (gain_money_ai_pickup_strategy, same_cards_ai_putdown_strategy),
    "gain_random": (gain_money_ai_pickup_strategy, random_ai_putdown_strategy),
    "random_avoid": (random_ai_pickup_strategy, avoid_loss_ai_putdown_strategy)
}

def execute_pickup(player, action, market, deck):
    if action.type == "pickup_deck":
        picking_up_card(player, "pickup_deck", market, deck)
    elif action.type == "pickup_market":
        picking_up_card(player, "pickup_market", market, deck)
    
def execute_putdown(player, action, player_list, market, company_list):
    if action.type == "putdown_shares":
        putting_down_card(player, "putdown_shares", player_list, market, company_list, action.target)
    elif action.type == "putdown_market":
        putting_down_card(player, "putdown_market", player_list, market, company_list, action.target)
    ai_end_turn_messages(player, market)

def end_game_and_score(player_list, company_list):
    empty_hands(player_list)

    for company in company_list:
        majority_shareholder = company.get_majority_holder(player_list)
        if majority_shareholder is not None:
            total_coins = 0
            
            for p in player_list:
                if p != majority_shareholder:
                    player_shares_dict = get_card_dictionary(p._shares)
                    if company._name in player_shares_dict:  # Check if company exists in player's shares
                        coins = player_shares_dict[company._name]  # Use company._name, not company_name
                        p._coins -= coins
                        total_coins += coins
            
            # Give 3x the collected coins to majority shareholder
            total_coins = total_coins * 3
            majority_shareholder._coins += total_coins
        else:
            pass
    
    winner = find_winner_simple(player_list)

def simulate_end_game_and_score(player_list, company_list, player, starting_deck):
    #simulate_empty_hands(player_list)
    simulate_deal_hands(starting_deck, 3, player_list, player)
    simulate_empty_sim_hands(player_list)
    for p in player_list:
        p._simulate_coins = p._coins
    
    for company in company_list:
        majority_shareholder = company.get_sim_majority_holder(player_list)
        if majority_shareholder is not None:
            simulate_total_coins = 0
            
            for p in player_list:
                if p != majority_shareholder:
                    player_shares_dict = get_card_dictionary(p._shares)
                    if company._name in player_shares_dict:  # Check if company exists in player's shares
                        coins = player_shares_dict[company._name]  # Use company._name, not company_name
                        p._simulate_coins -= coins
                        simulate_total_coins += coins
            
            # Give 3x the collected coins to majority shareholder
            simulate_total_coins = simulate_total_coins * 3
            majority_shareholder._simulate_coins += simulate_total_coins
        else:
            pass
    # could estimate average value per card, then remove three cards with average closest to zero

    winner = max(player_list, key=lambda player: player._simulate_coins)
    loser = min(player_list, key=lambda player: player._simulate_coins)
    average_coins = sum(p._simulate_coins for p in player_list) / len(player_list)
    distance_from_average = player._simulate_coins - average_coins

    win_value = 0
    if player == winner:
        win_value = 5
    elif player == loser:
        win_value = -5

    return (0.1 * player._simulate_coins) + (0.2 * distance_from_average) + win_value
    """
    def expected_gain_per_suit(player_list, company_list, player):
        for company in company_list:
            majority_shareholder = company.get_majority_holder(player_list)
            if majority_shareholder is None:
                gain_total_coins = 0
            elif majority_shareholder is not None:
                gain_total_coins = 0
                
                for p in player_list:
                    if p != majority_shareholder:
                        player_shares_dict = get_card_dictionary(p._shares)
                        if company._name in player_shares_dict:  # Check if company exists in player's shares
                            coins = player_shares_dict[company._name]  # Use company._name, not company_name
                            p._simulate_coins -= coins
                            simulate_total_coins += coins
    """

        
if __name__ == "__main__":
    #create_game(company_list, 4, 1)
    
    company_list = create_companies(default_companies)
    player_list = create_players_RL(4, 1)
    deck = create_deck(company_list)
    deck = prepare_deck(deck, 5)
    deal_hands(deck, 3, player_list)
    
    Finished = False
    game_round = 0
    while not Finished:
        game_round += 1
        if len(deck) == 0:
            Finished = True
        else:
            for p in player_list:
        
                pickup_action = p.pickup_strategy(p, market, deck, player_list)
                if pickup_action:
                    execute_pickup(p, pickup_action, market, deck)

                putdown_action = p.putdown_strategy(p, market, deck, player_list)
                if putdown_action:
                    execute_putdown(p, putdown_action, player_list, market, company_list)
                    # might need to charge this for putting down to market - it's getting company from the function definition
                    # but we've specified an action, which already includes the selected company

    end_game_and_score(player_list, company_list)





        