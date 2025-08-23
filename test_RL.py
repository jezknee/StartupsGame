import startups_RL_environment as sr
import startups_AI_game as sg

default_companies = [["Giraffe Beer", 5],["Bowwow Games",6],["Flamingo Soft",7],["Octo Coffee", 8],["Hippo Powertech", 9],["Elephant Mars Travel", 10]]
market = []
player_actions_pick_up = ["from deck", "from market"]
player_actions_put_down = ["to shares", "to market"]
game_stages = ["pick_up", "put_down", "scoring"]

company_list = sg.create_companies(default_companies)

env = sr.StartupsEnv(4,0, default_companies)
"""
company_list, player_list, deck, market = env.reset(company_list) 
print(company_list)
print(player_list)
print(deck)
print(market)
"""
#all_actions = sg.get_all_game_actions(player_actions_pick_up, player_actions_put_down, company_list)
#print(all_actions)
print(env.print_action_mapping())
print(env.state)