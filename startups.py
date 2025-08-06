import random

class Company:
    def __init__(self, name, total_shares, current_shares):
        self._name = name
        self._total_shares = total_shares
        self._current_shares = current_shares
    def __str__(self):
        return f"(Name: {self._name}, Total Shares: {self._total_shares}, Current Shares: {self._current_shares})"

class Player:
    def __init__(self, number, coins, hand, human):
        self._number = number
        self._coins = coins
        self._hand = hand
        self._human = human
    def __str__(self):
        return f"(Player Number: {self._number}, Current Coins: {self._coins}, Hand: {self._hand}, Human: {self._human})"

class Card:
    def __init__(self, company):
        self._company = company
    def __str__(self):
        return f"(Card Type: {self._company})"

class Market:
    def __init__(self, cards):
        self._cards = cards
    def __str__(self):
        return f"(Cards: {self._cards})"

default_companies = [["Giraffe Beer", 5],["Bowwow Games",6],["Flamingo Soft",7],["Octo Coffee", 8],["Hippo Powertech", 9],["Elephant Mars Travel", 10]]
additional_companies = [["Woofy Railway", 11]]


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
            new_card = Card(company._name)
            deck.append(new_card)
            n += 1
    return deck

def create_players(no_players, no_humans):
    player_list = []
    n = 1
    humans_created = 0
    while n <= no_players:
        if humans_created < no_humans:
            player = Player(n, 10, [], True)
            humans_created += 1
        elif humans_created == no_humans:
            player = Player(n, 10, [], False)
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

if __name__ == "__main__":
    company_list = create_companies(default_companies)
    player_list = create_players(4, 1)
    deck = create_deck(company_list)
    print_game_status(company_list)
    print_player_status(player_list)
    print("Deck at start:")
    print(len(deck))
    deck = prepare_deck(deck, 5)
    print("Deck after prep:")
    print(len(deck))
    deal_hands(deck, 3, player_list)
    print("Players after dealing")
    print_player_status(player_list)
    print("Deck after dealing:")
    print(len(deck))
    






        