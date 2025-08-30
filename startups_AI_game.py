import random
import time
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

    def get_majority_holder(self, player_list):
        company_shares_dictionary = {p: self.get_share_count(p) for p in player_list}
        
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
        self._hand = hand
        self._shares = shares
        self._chips = chips
        self._human = human
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
                print("You've got the anti-monopoly chip for that company, you can't play it")

        else:
            print("There isn't one of these in the market.")
    def add_card_to_shares(self, card):
        self._shares.append(card)
        self._hand.remove(card)
        self._last_pickup = None
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

    
def create_players_RL(no_players, no_humans):
    player_list = []
    n = 1
    humans_created = 0
    #assign_RL_strategy_to = random.choice([1,4])
    assign_avoid_loss_strategy_to = random.choice([1,4])
    assign_avoid_loss_strategy_to_2 = random.choice([1,4])
    assign_avoid_loss_strategy_to_3 = random.choice([1,4])
    assign_avoid_loss_strategy_to_4 = random.choice([1,4])
    while n <= no_players:
        if humans_created < no_humans:
            player = Player(n, 10, [], [], set(), True)
            player.pickup_strategy = human_pickup_strategy
            player.putdown_strategy = human_putdown_strategy
            humans_created += 1
        elif humans_created == no_humans:
            player = Player(n, 10, [], [], set(), False)
            if n == assign_avoid_loss_strategy_to or n == assign_avoid_loss_strategy_to_2 or n == assign_avoid_loss_strategy_to_3 or n == assign_avoid_loss_strategy_to_4:
                player.pickup_strategy = avoid_loss_ai_pickup_strategy
                player.putdown_strategy = avoid_loss_ai_putdown_strategy
            else:
                player.pickup_strategy = random_ai_pickup_strategy
                player.putdown_strategy = random_ai_putdown_strategy
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
                print("You don't have enough money to pick up from the deck.")
        elif action == "pickup_market":
            if len(market) != 0:
                company_input = input_card_for_pick_up(player, market)
                player.take_card_from_market(market, company_input)
            else:
                print("There aren't any cards in the market right now.")
    else:
        print("You can't do that right now.")

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
        print(f"DEBUG: Attempting to put down {company_name} to market")
        print(f"DEBUG: Player's hand: {[(c._company, type(c._company)) for c in player._hand]}")
        print(f"DEBUG: Looking for company: {card_company} (type: {type(card_company)})")
        
        chosen_card = None
        for c in player._hand:
            if c._company == company_name:
                chosen_card = c
                break
        if chosen_card is None:
            print(f"No '{company_name}' in hand to put to market.")
            print(f"Hand contents: {[c._company for c in player._hand]}")
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
        print("Which card?")
    for card in market:
        if check_pick_up_card(player, card):
            card_choices.append(card)
    if player._human:
        print(f"Type one of these companies: {get_card_list(card_choices)}")
        company_input = input()
        #print(f"Type the coins")
        #coins_input = int(input())
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
        print(f"Choose a card: {get_card_dictionary(player._hand)}")

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
                print("That's not an option. Please try again.")

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

def empty_hands(player_list):
    for player in player_list:
        player.put_hand_in_shares()

def find_winner_simple(player_list):
    """Find the player with the most coins"""
    if not player_list:
        return None
    
    winner = max(player_list, key=lambda player: player._coins)
    return winner

def human_turn_start_messages(p, market):
    print(f"Player {p._number}: Your turn!")
    print(f"Your hand is: {get_card_dictionary(p._hand)}")
    print(f"You have {p._coins} coins")
    print(f"The market is: {get_card_dictionary(market)}")
    print(f"Your shares are: {get_card_dictionary(p._shares)}")
    print(f"Your anti-monopoly chips are now {get_company_set(p)}")

def human_turn_end_messages(p, market):
    print(f"Your hand is now: {get_card_dictionary(p._hand)}")
    print(f"Your shares are now: {get_card_dictionary(p._shares)}")
    print(f"Your anti-monopoly chips are now {get_company_set(p)}")
    print(f"The market is now {get_card_dictionary(market)}")

def ai_end_turn_messages(p, market):
    print(f"The market is now {get_card_dictionary(market)}")
    print(f"Player {p._number}'s shares are now: {get_card_dictionary(p._shares)}")
    print(f"Player {p._number}'s anti-monopoly chips are now {get_company_set(p)}")

def human_pickup_strategy(player, market, deck, player_list):
    human_turn_start_messages(player, market)
    up_options = pick_up_action_choice(player, market, deck)
    print(f"Pick up from the deck, or pick up from the market? Type one of {up_options}.")
    while True:
        choice = input().strip().lower()
        if choice in up_options:
            if choice == "pickup_market":
                target_company = input_card_for_pick_up(player, market)
                return Action("pickup_market", target_company)
            else:
                return Action("pickup_deck")
        else:
            print("That's not an option. Please try again.")

def human_putdown_strategy(player, market, deck, player_list):
    print(f"Your hand is now: {get_card_dictionary(player._hand)}")
    print(f"You now have {player._coins} coins")
    down_options = put_down_action_choice(player)
    print(f"Put a card into your shares, or put a card into the market. Type one of {down_options}.")
    while True:
        choice = input().strip().lower()
        if choice in down_options:
            target_company = input_card_for_put_down(player)
            action_type = "putdown_shares" if choice == "putdown_shares" else "putdown_market"
            if action_type == "putdown_market":
                if not check_put_down_card_to_market(player, target_company):
                    print("You can't put that card into the market. Please choose again.")
                    continue
            return Action(action_type, target_company)
        else:
            print("That's not an option. Please try again.")
    human_turn_end_messages(p, market)

def random_ai_pickup_strategy(player, market, deck, player_list):
    choices = pick_up_action_choice(player, market, deck)
    if not choices:
        print(f"Player {player._number} cannot pick up any cards.")
        return None
    choice = random.choice(choices)
    if choice == "pickup_market":
        target_company = input_card_for_pick_up(player, market)
        action_type = "pickup_market"
        print(f"Player {player._number} picks up from market.")
        return Action(action_type, target_company)
    else:
        print(f"Player {player._number} picks up from deck.")
        return Action("pickup_deck")

def random_ai_putdown_strategy(player, market, deck, player_list):
    #time.sleep(1)
    choices = put_down_action_choice(player)
    if not choices:
        print(f"Player {player._number} cannot put down any cards.")
        return None
    while True:
        choice = random.choice(choices)
        target_company = input_card_for_put_down(player)
        if choices == "putdown_market":
            if not check_put_down_card_to_market(player, target_company):
                print("You can't put that card into the market. Please choose again.")
                continue
        
        print(f"Player {player._number} puts down {target_company} {choice}.")
        action_type = "putdown_shares" if choice == "putdown_shares" else "putdown_market"
        return Action(action_type, target_company)
    #time.sleep(1)

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
    #time.sleep(1)
    choices = return_all_pickup_choices(player, market)
    #print(choices)
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
    #print("Pickup:")
    #print("Good choices:")
    #print([str(g) for g in good_choices])
    #print("Bad choices:")
    #print([str(b) for b in bad_choices])
    if len(good_choices) == 0:
        good_choices = bad_choices

    choice = random.choice(good_choices)
    #print(f"Chosen pickup action: {choice}")
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
    print("Putdown:")
    print("Good choices:")
    print([str(g) for g in good_choices])
    print("Bad choices:")
    print([str(b) for b in bad_choices])
    if len(good_choices) == 0:
        good_choices = bad_choices
    
    choice = random.choice(good_choices)
    print(f"Chosen putdown action: {choice}")
    return choice

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
    #print("DEBUG market contents:", [(type(c._company), c._company) for c in market])
    #print("DEBUG shares contents:", [(type(c._company), c._company) for c in p._shares])
    ai_end_turn_messages(player, market)
    #time.sleep(1)

def end_game_and_score(player_list, company_list):
    print("The game has finished. Each player's cards are added to their shares.")
    empty_hands(player_list)
    for p in player_list:
        print(f"Player {p._number}'s shares are now: {get_card_dictionary(p._shares)}")
        time.sleep(1)
    for company in company_list:
        majority_shareholder = company.get_majority_holder(player_list)
        if majority_shareholder is not None:
            print(f"The majority shareholder in {company._name} is Player {majority_shareholder._number}")
            #time.sleep(1)
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
            print(f"No majority shareholder for {company._name}.")
            #time.sleep(1)

    for p in player_list:
            print(f"Player {p._number}'s coins are now: {p._coins}")
            #time.sleep(1)
    
    winner = find_winner_simple(player_list)
    print(f"The winner is: {winner._number}")

        
if __name__ == "__main__":
    #create_game(company_list, 4, 1)
    
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
                print(f"--- Player {p._number}'s turn ---")
        
                pickup_action = p.pickup_strategy(p, market, deck, player_list)
                if pickup_action:
                    execute_pickup(p, pickup_action, market, deck)

                putdown_action = p.putdown_strategy(p, market, deck, player_list)
                if putdown_action:
                    execute_putdown(p, putdown_action, player_list, market, company_list)
                    # might need to charge this for putting down to market - it's getting company from the function definition
                    # but we've specified an action, which already includes the selected company

    end_game_and_score(player_list, company_list)





        