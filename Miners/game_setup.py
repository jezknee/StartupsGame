def create_game(default_companies, no_players, no_humans):
    company_list = create_companies(default_companies)
    player_list = create_players(no_players, no_humans)
    deck = create_deck(company_list)
    deck = prepare_deck(deck, 5)
    deal_hands(deck, 3, player_list)
    return company_list, player_list, deck

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
            player.pickup_strategy = human_pickup_strategy
            player.putdown_strategy = human_putdown_strategy
            humans_created += 1
        elif humans_created == no_humans:
            player = Player(n, 10, [], [], set(), False)
            player.pickup_strategy = random_ai_pickup_strategy
            player.putdown_strategy = random_ai_putdown_strategy
        player_list.append(player)
        n += 1
    return player_list

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
