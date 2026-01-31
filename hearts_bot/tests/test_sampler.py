"""Tests for world sampling from beliefs."""

import time

import numpy as np
import pytest

from hearts_bot.core.cards import Card, Rank, Suit
from hearts_bot.inference.beliefs import BeliefState
from hearts_bot.inference.sampler import sample_world


def test_sample_world_basic():
    """Test basic world sampling."""
    bot_hand = {
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.KING, Suit.CLUBS),
        Card(Rank.QUEEN, Suit.CLUBS),
    }
    
    beliefs = BeliefState.initialize(bot_hand)
    rng = np.random.default_rng(42)
    
    hands = sample_world(beliefs, rng)
    
    # Should return 3 hands
    assert len(hands) == 3
    
    # Each hand should have 13 cards
    for hand in hands:
        assert len(hand) == 13
    
    # All hands should be disjoint
    all_cards = set()
    for hand in hands:
        assert len(hand & all_cards) == 0
        all_cards |= hand
    
    # Total cards should be 39 (52 - 13 in bot's hand)
    assert len(all_cards) == 39


def test_sample_world_with_passed_cards():
    """Test world sampling with known passed cards."""
    bot_hand = {Card(Rank.ACE, Suit.CLUBS)}
    passed_cards = {
        1: {Card(Rank.KING, Suit.CLUBS), Card(Rank.QUEEN, Suit.CLUBS)},
    }
    
    beliefs = BeliefState.initialize(bot_hand, passed_cards)
    rng = np.random.default_rng(42)
    
    hands = sample_world(beliefs, rng)
    
    # Player 1's hand should contain passed cards
    assert Card(Rank.KING, Suit.CLUBS) in hands[0]  # Player 1 is index 0
    assert Card(Rank.QUEEN, Suit.CLUBS) in hands[0]


def test_sample_world_with_voids():
    """Test world sampling respects void constraints."""
    bot_hand = {Card(Rank.ACE, Suit.CLUBS)}
    beliefs = BeliefState.initialize(bot_hand)
    
    # Mark player 1 as void in hearts
    beliefs.update_void_shown(1, Suit.HEARTS)
    
    rng = np.random.default_rng(42)
    hands = sample_world(beliefs, rng)
    
    # Player 1's hand should have no hearts
    player1_hand = hands[0]  # Player 1 is index 0
    for card in player1_hand:
        assert card.suit != Suit.HEARTS


def test_sample_world_statistical():
    """Statistical test: sample marginals should match beliefs."""
    bot_hand = {Card(Rank.ACE, Suit.CLUBS)}
    beliefs = BeliefState.initialize(bot_hand)
    
    # Track card assignments over many samples
    card_counts = {}  # card -> [count for p1, count for p2, count for p3]
    
    rng = np.random.default_rng(42)
    n_samples = 10000
    
    for _ in range(n_samples):
        hands = sample_world(beliefs, rng)
        
        for opp_idx, hand in enumerate(hands):
            for card in hand:
                if card not in card_counts:
                    card_counts[card] = [0, 0, 0]
                card_counts[card][opp_idx] += 1
    
    # Check that marginals match beliefs (approximately)
    for card, counts in card_counts.items():
        if card in beliefs.card_probs:
            expected_probs = beliefs.card_probs[card]
            observed_probs = np.array(counts) / n_samples
            
            # Should be close (within reasonable tolerance)
            for i in range(3):
                if expected_probs[i] > 0:
                    # Allow 5% error
                    assert abs(observed_probs[i] - expected_probs[i]) < 0.05


def test_sample_world_performance():
    """Performance test: ensure sampling is fast."""
    bot_hand = {Card(Rank.ACE, Suit.CLUBS)}
    beliefs = BeliefState.initialize(bot_hand)
    rng = np.random.default_rng(42)
    
    # Time 1000 samples
    start = time.perf_counter()
    for _ in range(1000):
        sample_world(beliefs, rng)
    elapsed = time.perf_counter() - start
    
    # Should be < 0.1ms per sample on average
    avg_time_ms = (elapsed / 1000) * 1000
    assert avg_time_ms < 0.1, f"Average sample time {avg_time_ms:.3f}ms exceeds 0.1ms"


def test_sample_world_hand_sizes():
    """Test that sampled hands have correct sizes."""
    bot_hand = {Card(Rank.ACE, Suit.CLUBS) for _ in range(13)}
    beliefs = BeliefState.initialize(bot_hand)
    
    rng = np.random.default_rng(42)
    
    for _ in range(100):
        hands = sample_world(beliefs, rng)
        
        # Each hand should have exactly 13 cards
        for hand in hands:
            assert len(hand) == 13
