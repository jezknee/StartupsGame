import random

# ===============================
# Domain classes
# ===============================

class Company:
    def __init__(self, name, total_shares, current_shares):
        self._name = name
        self._total_shares = total_shares
        self._current_shares = current_shares

    def get_share_count(self, player):
        return sum(1 for card in player._shares if card._company == self._name)

    def get_majority_holder(self, player_list):
        if not player_list:
            return None
        shares = {p: self.get_share_count(p) for p in player_list}
        max_value = max(shares.values())
        if list(shares.values()).count(max_value) == 1:
            return max(shares, key=shares.get)
        return None

    def __eq__(self, other):
        return self._name == other._name

    def __hash__(self):
        return hash(self._name)

    def __str__(self):
        return f"(Name: {self._name}, Total Shares: {self._total_shares}, Current Shares: {self._current_shares})"


class Card:
    def __init__(self, company, coins_on):
        self._company = company
        self._coins_on = coins_on

    def __eq__(self, other):
        return self._company == other._company

    def __str__(self):
        return f"(Card Type: {self._company})"


class Player:
    def __init__(self, number, coins, hand, shares, chips, controller):
        self._number = number
        self._coins = coins
        self._hand = hand
        self._shares = shares
        self._chips = chips
        self.controller = controller

    def take_card_from_pile(self, deck):
        if deck:
            self._hand.append(deck.pop(0))

    def take_card_from_market(self, market, company_name):
        best_card = None
        max_coins = -1
        for c in market:
            if c._company == company_name and c._coins_on > max_coins and not self.check_for_chip(company_name):
                best_card = c
                max_coins = c._coins_on
        if best_card:
            self._coins += best_card._coins_on
            market.remove(best_card)
            best_card._coins_on = 0
            self._hand.append(best_card)

    def add_card_to_shares(self, card):
        self._shares.append(card)
        self._hand.remove(card)

    def add_card_to_market(self, card, market):
        market.append(card)
        self._hand.remove(card)

    def add_chip(self, company, player_list):
        if not check_for_monopoly(player_list, company):
            self._chips.add(company)
        else:
            if company.get_share_count(self) > find_monopoly_value(player_list, company):
                self._chips.add(company)

    def remove_chip(self, company, player_list):
        if company in self._chips:
            if company.get_share_count(self) < find_monopoly_value(player_list, company):
                self._chips.remove(company)

    def check_for_chip(self, company_name):
        return any(chip._name == company_name for chip in self._chips)

    def put_hand_in_shares(self):
        for card in self._hand[:]:
            self.add_card_to_shares(card)

    def __str__(self):
        return f"(Player {self._number}, Coins: {self._coins}, Hand: {self._hand}, Shares: {self._shares})"


# ===============================
# Game setup helpers
# ===============================

def create_companies(starting_list):
    return [Company(name, total, 0) for name, total in starting_list]

def create_deck(companies):
    return [Card(c._name, 0) for c in companies for _ in range(c._total_shares)]

def create_players(no_players, no_humans):
    players = []
    for i in range(1, no_players+1):
        if i <= no_humans:
            controller = HumanController()
        else:
            controller = RandomAIController()
        players.append(Player(i, 10, [], [], set(), controller))
    return players

def deal_hands(deck, cards_each, players):
    for _ in range(cards_each):
        for p in players:
            p._hand.append(deck.pop(0))


# ===============================
# Game logic helpers
# ===============================

def get_card_dictionary(cards):
    d = {}
    for card in cards:
        d[card._company] = d.get(card._company, 0) + 1
    return d

def get_company_set(player):
    return {c._name for c in player._chips}

def check_for_monopoly(players, company):
    return sum(company.get_share_count(p) for p in players) > 1

def find_monopoly_value(players, company):
    return max(company.get_share_count(p) for p in players)

def pick_up_action_choice(player, market, deck):
    choices = []
    if deck and player._coins >= len(market):
        choices.append("from deck")
    if any(not player.check_for_chip(c._company) for c in market):
        choices.append("from market")
    return choices

def put_down_action_choice(player):
    return ["to shares", "to market"] if player._hand else []


# ===============================
# Controllers
# ===============================

class PlayerController:
    def choose_pick_up_action(self, player, market, deck): ...
    def choose_put_down_action(self, player): ...
    def choose_card_for_pick_up(self, player, market): ...
    def choose_card_for_put_down(self, player): ...

class HumanController(PlayerController):
    def choose_pick_up_action(self, player, market, deck):
        options = pick_up_action_choice(player, market, deck)
        print(f"Pick up options: {options}")
        return input("> ").strip()

    def choose_put_down_action(self, player):
        options = put_down_action_choice(player)
        print(f"Put down options: {options}")
        return input("> ").strip()

    def choose_card_for_pick_up(self, player, market):
        print(f"Market: {get_card_dictionary(market)}")
        return input("Choose company: ").strip()

    def choose_card_for_put_down(self, player):
        print(f"Hand: {get_card_dictionary(player._hand)}")
        return input("Choose company: ").strip()

class RandomAIController(PlayerController):
    def choose_pick_up_action(self, player, market, deck):
        options = pick_up_action_choice(player, market, deck)
        return random.choice(options) if options else None

    def choose_put_down_action(self, player):
        options = put_down_action_choice(player)
        return random.choice(options) if options else None

    def choose_card_for_pick_up(self, player, market):
        valid = [c for c in market if not player.check_for_chip(c._company)]
        return random.choice(valid)._company if valid else None

    def choose_card_for_put_down(self, player):
        return random.choice(player._hand)._company if player._hand else None


# ===============================
# Game loop
# ===============================

if __name__ == "__main__":
    default_companies = [["Giraffe Beer", 5],["Bowwow Games",6],["Flamingo Soft",7]]
    market = []
    companies = create_companies(default_companies)
    players = create_players(4, 1)
    deck = create_deck(companies)
    random.shuffle(deck)
    deal_hands(deck, 3, players)

    finished = False
    round_num = 0

    while not finished:
        round_num += 1
        print(f"\n--- Round {round_num} ---")
        if not deck:
            finished = True
            break

        for p in players:
            print(f"\nPlayer {p._number}'s turn")
            up_action = p.controller.choose_pick_up_action(p, market, deck)
            if up_action == "from deck":
                p.take_card_from_pile(deck)
            elif up_action == "from market":
                company = p.controller.choose_card_for_pick_up(p, market)
                p.take_card_from_market(market, company)

            down_action = p.controller.choose_put_down_action(p)
            if down_action:
                company = p.controller.choose_card_for_put_down(p)
                chosen_card = next((c for c in p._hand if c._company == company), None)
                if chosen_card:
                    if down_action == "to shares":
                        comp_obj = next(c for c in companies if c._name == company)
                        p.add_card_to_shares(chosen_card)
                        p.add_chip(comp_obj, players)
                        for other in players:
                            other.remove_chip(comp_obj, players)
                    elif down_action == "to market":
                        p.add_card_to_market(chosen_card, market)

    print("\nGame over!")
    for p in players:
        p.put_hand_in_shares()
        print(f"Player {p._number} shares: {get_card_dictionary(p._shares)}")
