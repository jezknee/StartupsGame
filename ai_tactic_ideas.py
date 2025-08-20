def tactic_prefer_majority_pickup(player, market, deck, player_list):
    """Return Action if it helps become majority shareholder."""
    for card in market:
        if not player.check_for_chip(card._company):
            # Check if picking it up gives majority
            count_player = count_card(player, card._company)
            max_other = max(count_card(p, card._company) for p in player_list if p != player)
            if count_player + 1 > max_other:
                return Action("pickup_market", card._company)
    return None

def tactic_prevent_opponent_majority(player, market, deck, player_list):
    """Return Action if it blocks someone else from getting majority."""
    for card in market:
        for p in player_list:
            if p != player:
                count_other = count_card(p, card._company)
                count_player = count_card(player, card._company)
                if count_other + 1 > count_player + 1:  # opponent could get ahead
                    return Action("pickup_market", card._company)
    return None


def composite_pickup_strategy(player, market, deck, player_list):
    tactics = [
        tactic_prefer_majority_pickup,
        tactic_prevent_opponent_majority,
        random_pickup_tactic
    ]
    for tactic in tactics:
        action = tactic(player, market, deck, player_list)
        if action is not None:
            return action
    return None



# tactics.py

def tactic_random_pickup(player, market, deck, player_list):
    """Just picks a random valid pickup."""
    choices = return_all_pickup_choices(player, market)
    return random.choice(choices) if choices else None

def tactic_random_putdown(player, market, deck, player_list):
    """Just picks a random valid putdown."""
    choices = return_all_putdown_choices(player, market)
    return random.choice(choices) if choices else None

def tactic_prefer_majority_pickup(player, market, deck, player_list):
    """Pick up a card if it gives you majority shareholder status."""
    for c in return_all_pickup_choices(player, market):
        if c.type == "pickup_market":
            count_player = count_card(player, c.target)
            max_other = max(count_card(p, c.target) for p in player_list if p != player)
            if count_player + 1 > max_other:
                return c
    return None

def tactic_block_opponent_majority(player, market, deck, player_list):
    """Pick a card to stop opponent from gaining majority."""
    for c in return_all_pickup_choices(player, market):
        if c.type == "pickup_market":
            for opponent in player_list:
                if opponent != player:
                    count_other = count_card(opponent, c.target)
                    count_player = count_card(player, c.target)
                    if count_other + 1 > count_player + 1:
                        return c
    return None


# ai_strategies.py
def composite_strategy(tactics):
    def strategy(player, market, deck, player_list):
        for tactic in tactics:
            action = tactic(player, market, deck, player_list)
            if action is not None:
                return action
        return None
    return strategy


from tactics import (
    tactic_random_pickup,
    tactic_random_putdown,
    tactic_prefer_majority_pickup,
    tactic_block_opponent_majority
)
from ai_strategies import composite_strategy

def create_players(no_players, no_humans):
    player_list = []
    for n in range(1, no_players + 1):
        human = n <= no_humans
        p = Player(n, 10, [], [], set(), human)
        if human:
            p.pickup_strategy = human_pickup_strategy
            p.putdown_strategy = human_putdown_strategy
        else:
            # Example: AI that tries to get majority, block opponents, then random
            p.pickup_strategy = composite_strategy([
                tactic_prefer_majority_pickup,
                tactic_block_opponent_majority,
                tactic_random_pickup
            ])
            p.putdown_strategy = composite_strategy([
                tactic_random_putdown  # You can add smarter putdown tactics later
            ])
        player_list.append(p)
    return player_list


# tactics.py  (continued)

def tactic_putdown_to_complete_majority(player, market, deck, player_list):
    """Put down a card into shares if it will give you majority shareholder status."""
    for c in return_all_putdown_choices(player, market):
        if c.type == "putdown_shares":
            count_player = count_card(player, c.target)
            max_other = max(count_card(p, c.target) for p in player_list if p != player)
            if count_player + 1 > max_other:
                return c
    return None

def tactic_putdown_to_block_market_gain(player, market, deck, player_list):
    """
    Avoid putting a card into the market if it could give someone majority.
    Will choose shares instead in such a case.
    """
    safe_choices = []
    risky_choices = []
    for c in return_all_putdown_choices(player, market):
        if c.type == "putdown_market":
            risky = False
            for opponent in player_list:
                if opponent != player:
                    count_other = count_card(opponent, c.target)
                    if count_other + 1 > count_card(player, c.target):
                        risky = True
                        break
            if risky:
                risky_choices.append(c)
            else:
                safe_choices.append(c)
        else:
            safe_choices.append(c)

    if safe_choices:
        return random.choice(safe_choices)
    elif risky_choices:
        return random.choice(risky_choices)
    return None

def tactic_random_putdown(player, market, deck, player_list):
    """Just pick any valid putdown at random."""
    choices = return_all_putdown_choices(player, market)
    return random.choice(choices) if choices else None


from tactics import (
    tactic_random_pickup,
    tactic_random_putdown,
    tactic_prefer_majority_pickup,
    tactic_block_opponent_majority,
    tactic_putdown_to_complete_majority,
    tactic_putdown_to_block_market_gain
)
from ai_strategies import composite_strategy

def create_players(no_players, no_humans):
    player_list = []
    for n in range(1, no_players + 1):
        human = n <= no_humans
        p = Player(n, 10, [], [], set(), human)
        if human:
            p.pickup_strategy = human_pickup_strategy
            p.putdown_strategy = human_putdown_strategy
        else:
            # Personality 1: Aggressive monopolist
            p.pickup_strategy = composite_strategy([
                tactic_prefer_majority_pickup,
                tactic_block_opponent_majority,
                tactic_random_pickup
            ])
            p.putdown_strategy = composite_strategy([
                tactic_putdown_to_complete_majority,
                tactic_putdown_to_block_market_gain,
                tactic_random_putdown
            ])
        player_list.append(p)
    return player_list

def tactic_new_behavior(...):
    # Analyze game state
    return Action(...) or None

