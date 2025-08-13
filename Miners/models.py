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
        company_shares_dictionary = {p: self.get_share_count(p) for p in player_list}
        
        if not company_shares_dictionary:
            return None
        
        # Count how many times the maximum value appears
        max_value = max(company_shares_dictionary.values())
        max_count = list(company_shares_dictionary.values()).count(max_value)
        
        return max(company_shares_dictionary, key=company_shares_dictionary.get) if max_count == 1 else None

    def __eq__(self, other):
        return self._name == other._name
    def __hash__(self):
        return hash(self._name)  # hash based only on name
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

            elif self.check_for_chip(company_name):
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

class Action:
    def __init__(self, action_type, target=None):
        self.type = action_type   # e.g., "pickup_deck", "pickup_market", "putdown_shares"
        self.target = target      # e.g., company name