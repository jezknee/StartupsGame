import pytest
from startups import *

# Test classes and their initialization
class TestCompany:
    def test_company_creation(self):
        company = Company("Test Corp", 10, 0)
        assert company._name == "Test Corp"
        assert company._total_shares == 10
        assert company._current_shares == 0

    def test_company_str(self):
        company = Company("Test Corp", 10, 5)
        expected = "(Name: Test Corp, Total Shares: 10, Current Shares: 5)"
        assert str(company) == expected

class TestPlayer:
    def test_player_creation_human(self):
        player = Player(1, 10, [], True)
        assert player._number == 1
        assert player._coins == 10
        assert player._hand == []
        assert player._human == True

    def test_player_creation_ai(self):
        player = Player(2, 15, ["card1"], False)
        assert player._number == 2
        assert player._coins == 15
        assert player._hand == ["card1"]
        assert player._human == False

    def test_player_str(self):
        player = Player(1, 10, [], True)
        expected = "(Player Number: 1, Current Coins: 10, Hand: [], Human: True)"
        assert str(player) == expected

class TestCard:
    def test_card_creation(self):
        card = Card("Giraffe Beer")
        assert card._company == "Giraffe Beer"

    def test_card_equality(self):
        card1 = Card("Giraffe Beer")
        card2 = Card("Giraffe Beer")
        card3 = Card("Bowwow Games")
        assert card1 == card2
        assert card1 != card3

    def test_card_str(self):
        card = Card("Giraffe Beer")
        expected = "(Card Type: Giraffe Beer)"
        assert str(card) == expected

# Test utility functions
class TestUtilityFunctions:
    def test_create_companies(self):
        test_companies = [["Company A", 5], ["Company B", 7]]
        companies = create_companies(test_companies)
        
        assert len(companies) == 2
        assert companies[0]._name == "Company A"
        assert companies[0]._total_shares == 5
        assert companies[0]._current_shares == 0
        assert companies[1]._name == "Company B"
        assert companies[1]._total_shares == 7

    def test_create_deck(self):
        companies = [Company("Test Corp", 3, 0), Company("Another Corp", 2, 0)]
        deck = create_deck(companies)
        
        assert len(deck) == 5  # 3 + 2 cards
        # Check that all cards are Card objects
        assert all(isinstance(card, Card) for card in deck)
        # Check card distribution
        test_corp_cards = [card for card in deck if card._company == "Test Corp"]
        another_corp_cards = [card for card in deck if card._company == "Another Corp"]
        assert len(test_corp_cards) == 3
        assert len(another_corp_cards) == 2

    def test_create_players_all_human(self):
        players = create_players(3, 3)
        
        assert len(players) == 3
        assert all(player._human == True for player in players)
        assert all(player._coins == 10 for player in players)
        assert all(len(player._hand) == 0 for player in players)
        # Check player numbers
        assert players[0]._number == 1
        assert players[1]._number == 2
        assert players[2]._number == 3

    def test_create_players_mixed(self):
        players = create_players(4, 2)
        
        assert len(players) == 4
        assert players[0]._human == True
        assert players[1]._human == True
        assert players[2]._human == False
        assert players[3]._human == False

    def test_create_players_no_humans(self):
        players = create_players(3, 0)
        
        assert len(players) == 3
        assert all(player._human == False for player in players)

    def test_prepare_deck(self, mock_shuffle):
        # Create a test deck
        test_deck = [Card("A"), Card("B"), Card("C"), Card("D"), Card("E")]
        
        # Test with cutoff of 2
        result = prepare_deck(test_deck, 2)
        
        # Should return deck[2:] which is the last 3 cards
        assert len(result) == 3
        mock_shuffle.assert_called_once()

    def test_deal_hands(self):
        # Create test data
        companies = [Company("Test", 10, 0)]
        deck = create_deck(companies)
        players = create_players(2, 2)
        
        initial_deck_size = len(deck)
        
        # Deal 3 cards to each player
        deal_hands(deck, 3, players)
        
        # Each player should have 3 cards
        assert len(players[0]._hand) == 3
        assert len(players[1]._hand) == 3
        
        # Deck should be reduced by 6 cards (3 cards * 2 players)
        assert len(deck) == initial_deck_size - 6
        
        # All cards in hands should be Card objects
        all_hand_cards = players[0]._hand + players[1]._hand
        assert all(isinstance(card, Card) for card in all_hand_cards)

# Integration test
class TestGameIntegration:
    def test_full_game_setup(self):
        # Test the main game setup process
        default_companies = [["Giraffe Beer", 5], ["Bowwow Games", 6]]
        
        # Create companies
        company_list = create_companies(default_companies)
        assert len(company_list) == 2
        
        # Create players
        player_list = create_players(4, 1)
        assert len(player_list) == 4
        assert player_list[0]._human == True
        assert all(not player._human for player in player_list[1:])
        
        # Create and prepare deck
        deck = create_deck(company_list)
        expected_deck_size = 5 + 6  # Total shares from both companies
        assert len(deck) == expected_deck_size
        
        # Prepare deck (simulate cutting off top 5 cards)
        prepared_deck = prepare_deck(deck.copy(), 5)
        assert len(prepared_deck) == expected_deck_size - 5
        
        # Deal hands
        deal_hands(prepared_deck, 3, player_list)
        
        # Verify dealing worked correctly
        total_cards_dealt = sum(len(player._hand) for player in player_list)
        assert total_cards_dealt == 12  # 3 cards * 4 players
        assert len(prepared_deck) == expected_deck_size - 5 - 12

# Edge case tests
class TestEdgeCases:
    def test_empty_company_list(self):
        companies = create_companies([])
        assert len(companies) == 0
        
        deck = create_deck(companies)
        assert len(deck) == 0

    def test_company_with_zero_shares(self):
        companies = create_companies([["Zero Corp", 0]])
        deck = create_deck(companies)
        assert len(deck) == 0

    def test_single_player(self):
        players = create_players(1, 1)
        assert len(players) == 1
        assert players[0]._human == True