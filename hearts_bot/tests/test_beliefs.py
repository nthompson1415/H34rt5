"""Tests for belief state updates."""

import numpy as np
import pytest

from hearts_bot.core.cards import Card, Rank, Suit
from hearts_bot.inference.beliefs import BeliefState
from hearts_bot.inference.updater import (
    CardPlayedObservation,
    TrickCompleteObservation,
    VoidShownObservation,
    update_beliefs,
)


def test_belief_initialization():
    """Test belief initialization with uniform distribution."""
    bot_hand = {
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.KING, Suit.CLUBS),
        Card(Rank.QUEEN, Suit.CLUBS),
    }
    
    beliefs = BeliefState.initialize(bot_hand)
    
    # Check that all unknown cards have probabilities
    unknown_count = 52 - len(bot_hand)
    assert len(beliefs.card_probs) == unknown_count
    
    # Check that probabilities sum to 1.0 for each card
    for card, probs in beliefs.card_probs.items():
        assert abs(probs.sum() - 1.0) < 1e-6
        assert len(probs) == 3  # 3 opponents
        # Should be approximately uniform
        assert all(abs(p - 1.0/3.0) < 1e-6 for p in probs)


def test_belief_initialization_with_passed_cards():
    """Test belief initialization accounting for passed cards."""
    bot_hand = {Card(Rank.ACE, Suit.CLUBS)}
    passed_cards = {
        1: {Card(Rank.KING, Suit.CLUBS)},
        2: {Card(Rank.QUEEN, Suit.CLUBS)},
    }
    
    beliefs = BeliefState.initialize(bot_hand, passed_cards)
    
    # Check that passed cards have correct probabilities
    king_card = Card(Rank.KING, Suit.CLUBS)
    queen_card = Card(Rank.QUEEN, Suit.CLUBS)
    
    if king_card in beliefs.card_probs:
        probs = beliefs.card_probs[king_card]
        # Player 1 should have probability 1.0
        assert abs(probs[0] - 1.0) < 1e-6
        assert abs(probs[1]) < 1e-6
        assert abs(probs[2]) < 1e-6
    
    if queen_card in beliefs.card_probs:
        probs = beliefs.card_probs[queen_card]
        # Player 2 should have probability 1.0
        assert abs(probs[1] - 1.0) < 1e-6
        assert abs(probs[0]) < 1e-6
        assert abs(probs[2]) < 1e-6


def test_update_card_played():
    """Test updating beliefs when a card is played."""
    bot_hand = {Card(Rank.ACE, Suit.CLUBS)}
    beliefs = BeliefState.initialize(bot_hand)
    
    played_card = list(beliefs.card_probs.keys())[0]
    
    # Update belief
    beliefs.update_card_played(1, played_card)
    
    # Card should be removed from probabilities
    assert played_card not in beliefs.card_probs


def test_update_void_shown():
    """Test updating beliefs when a void is shown."""
    bot_hand = {Card(Rank.ACE, Suit.CLUBS)}
    beliefs = BeliefState.initialize(bot_hand)
    
    # Show that player 1 is void in hearts
    beliefs.update_void_shown(1, Suit.HEARTS)
    
    # Check that all heart cards have P=0 for player 1
    for card, probs in beliefs.card_probs.items():
        if card.suit == Suit.HEARTS:
            # Player 1 is index 0 (player_id - 1)
            assert abs(probs[0]) < 1e-6
    
    # Check that probabilities are renormalized
    for card, probs in beliefs.card_probs.items():
        if card.suit == Suit.HEARTS:
            # Should sum to 1.0 (across players 2 and 3)
            assert abs(probs.sum() - 1.0) < 1e-6


def test_update_passed_cards():
    """Test updating beliefs with passed cards."""
    bot_hand = {Card(Rank.ACE, Suit.CLUBS)}
    beliefs = BeliefState.initialize(bot_hand)
    
    passed = {Card(Rank.KING, Suit.CLUBS), Card(Rank.QUEEN, Suit.CLUBS)}
    beliefs.update_passed_cards('left', passed)
    
    # Check that passed cards are recorded
    assert 1 in beliefs.passed_cards
    assert passed.issubset(beliefs.passed_cards[1])


def test_update_beliefs_card_played():
    """Test update_beliefs with CardPlayedObservation."""
    bot_hand = {Card(Rank.ACE, Suit.CLUBS)}
    beliefs = BeliefState.initialize(bot_hand)
    
    played_card = list(beliefs.card_probs.keys())[0]
    obs = CardPlayedObservation(1, played_card)
    
    updated = update_beliefs(beliefs, obs)
    
    # Card should be removed
    assert played_card not in updated.card_probs


def test_update_beliefs_void_shown():
    """Test update_beliefs with VoidShownObservation."""
    bot_hand = {Card(Rank.ACE, Suit.CLUBS)}
    beliefs = BeliefState.initialize(bot_hand)
    
    obs = VoidShownObservation(1, Suit.HEARTS)
    updated = update_beliefs(beliefs, obs)
    
    # Check void is recorded
    assert (1, Suit.HEARTS) in updated.voids


def test_probability_constraints():
    """Test that probability constraints are maintained."""
    bot_hand = {Card(Rank.ACE, Suit.CLUBS)}
    beliefs = BeliefState.initialize(bot_hand)
    
    # After several updates, check constraints
    for i, card in enumerate(list(beliefs.card_probs.keys())[:5]):
        beliefs.update_card_played(i % 3 + 1, card)
    
    # Check that remaining probabilities sum to 1.0
    for card, probs in beliefs.card_probs.items():
        total = probs.sum()
        assert abs(total - 1.0) < 1e-6 or total == 0.0
