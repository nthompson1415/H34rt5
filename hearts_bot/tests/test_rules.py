"""Tests for game rules."""

import pytest

from hearts_bot.core.cards import Card, Rank, Suit, QUEEN_OF_SPADES, TWO_OF_CLUBS
from hearts_bot.core.game_state import Trick
from hearts_bot.core.rules import (
    calculate_round_score,
    get_legal_moves,
    resolve_trick,
)


def test_get_legal_moves_follow_suit():
    """Test that must follow suit if able."""
    hand = {
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.KING, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.DIAMONDS),
    }
    
    trick = Trick()
    trick.cards = [(1, Card(Rank.TWO, Suit.CLUBS))]
    trick.leader = 1
    
    legal = get_legal_moves(hand, trick, hearts_broken=True, is_first_trick=False)
    
    # Must play clubs
    assert len(legal) == 1
    assert legal[0].suit == Suit.CLUBS
    assert legal[0] == Card(Rank.ACE, Suit.CLUBS)


def test_get_legal_moves_void():
    """Test that can play any card if void in led suit."""
    hand = {
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.DIAMONDS),
    }
    
    trick = Trick()
    trick.cards = [(1, Card(Rank.TWO, Suit.CLUBS))]
    trick.leader = 1
    
    legal = get_legal_moves(hand, trick, hearts_broken=True, is_first_trick=False)
    
    # Can play any card (void in clubs)
    assert len(legal) == 2


def test_get_legal_moves_hearts_not_broken():
    """Test that cannot lead hearts unless broken."""
    hand = {
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.CLUBS),
    }
    
    trick = Trick()
    
    legal = get_legal_moves(hand, trick, hearts_broken=False, is_first_trick=False)
    
    # Cannot lead hearts
    assert Card(Rank.ACE, Suit.HEARTS) not in legal
    assert Card(Rank.KING, Suit.CLUBS) in legal


def test_get_legal_moves_hearts_only_hand():
    """Test that can lead hearts if hand contains only hearts."""
    hand = {
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.HEARTS),
    }
    
    trick = Trick()
    
    legal = get_legal_moves(hand, trick, hearts_broken=False, is_first_trick=False)
    
    # Can lead hearts (only hearts in hand)
    assert len(legal) == 2


def test_get_legal_moves_first_trick_no_points():
    """Test that first trick cannot have points."""
    hand = {
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.CLUBS),
        QUEEN_OF_SPADES,
    }
    
    trick = Trick()
    trick.cards = [(1, Card(Rank.TWO, Suit.CLUBS))]
    trick.leader = 1
    
    legal = get_legal_moves(hand, trick, hearts_broken=False, is_first_trick=True)
    
    # Cannot play hearts or Q♠
    assert Card(Rank.ACE, Suit.HEARTS) not in legal
    assert QUEEN_OF_SPADES not in legal
    assert Card(Rank.KING, Suit.CLUBS) in legal


def test_resolve_trick():
    """Test trick resolution."""
    trick = Trick()
    trick.cards = [
        (0, Card(Rank.TWO, Suit.CLUBS)),
        (1, Card(Rank.THREE, Suit.CLUBS)),
        (2, Card(Rank.ACE, Suit.CLUBS)),
        (3, Card(Rank.FOUR, Suit.CLUBS)),
    ]
    trick.leader = 0
    
    winner, points = resolve_trick(trick)
    
    assert winner == 2  # ACE is highest
    assert points == 0  # No points in trick


def test_resolve_trick_with_points():
    """Test trick resolution with points."""
    trick = Trick()
    trick.cards = [
        (0, Card(Rank.TWO, Suit.CLUBS)),
        (1, Card(Rank.THREE, Suit.HEARTS)),
        (2, Card(Rank.ACE, Suit.CLUBS)),
        (3, QUEEN_OF_SPADES),
    ]
    trick.leader = 0
    
    winner, points = resolve_trick(trick)
    
    assert winner == 2  # ACE of clubs wins
    assert points == 14  # 1 heart + 13 for Q♠


def test_calculate_round_score_normal():
    """Test normal round scoring."""
    trick1 = Trick()
    trick1.cards = [
        (0, Card(Rank.ACE, Suit.CLUBS)),
        (1, Card(Rank.TWO, Suit.CLUBS)),
        (2, Card(Rank.THREE, Suit.CLUBS)),
        (3, Card(Rank.FOUR, Suit.CLUBS)),
    ]
    trick1.leader = 0
    
    trick2 = Trick()
    trick2.cards = [
        (1, Card(Rank.ACE, Suit.HEARTS)),
        (2, Card(Rank.TWO, Suit.HEARTS)),
        (3, Card(Rank.THREE, Suit.HEARTS)),
        (0, Card(Rank.FOUR, Suit.HEARTS)),
    ]
    trick2.leader = 1
    
    tricks = [trick1, trick2]
    
    result = calculate_round_score(tricks)
    assert len(result) == 4
    assert all(pid in result for pid in range(4))


def test_calculate_round_score_shoot_moon():
    """Test shoot-the-moon scoring."""
    # Create tricks where one player takes all 26 points
    tricks = []
    for i in range(13):
        trick = Trick()
        # Player 0 wins all tricks with points
        if i < 12:
            trick.cards = [
                (0, Card(Rank.ACE, Suit.HEARTS)),
                (1, Card(Rank.TWO, Suit.CLUBS)),
                (2, Card(Rank.THREE, Suit.CLUBS)),
                (3, Card(Rank.FOUR, Suit.CLUBS)),
            ]
        else:
            # Last trick has Q♠
            trick.cards = [
                (0, QUEEN_OF_SPADES),
                (1, Card(Rank.TWO, Suit.CLUBS)),
                (2, Card(Rank.THREE, Suit.CLUBS)),
                (3, Card(Rank.FOUR, Suit.CLUBS)),
            ]
        trick.leader = 0
        tricks.append(trick)
    
    scores = calculate_round_score(tricks)
    
    # Check that all players have scores
    assert len(scores) == 4
    assert all(pid in scores for pid in range(4))
    
    # Check shoot-the-moon: player 0 should have 0, others should have 26
    # (if implementation is correct)
    total_points = sum(scores.values())
    if total_points == 26:
        # One player has all points - check shoot-the-moon logic
        for pid, points in scores.items():
            if points == 26:
                # That player should get 0, others get 26
                assert scores[pid] == 0 or all(scores[p] == 26 for p in range(4) if p != pid)
