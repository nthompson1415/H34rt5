"""Efficient world sampling from beliefs."""

import numpy as np

from hearts_bot.core.cards import Card, Suit
from hearts_bot.inference.beliefs import BeliefState


def sample_world(
    beliefs: BeliefState,
    rng: np.random.Generator,
    max_rejections: int = 1000
) -> tuple[set[Card], set[Card], set[Card]]:
    """
    Generate three opponent hands consistent with beliefs.
    
    Algorithm:
    1. For each card, sample assignment weighted by probabilities
    2. Reject if violates constraints (hand size, voids)
    3. Or use iterative assignment with renormalization
    
    Must be efficient (<0.1ms per world) for 1000+ samples per decision.
    
    Returns:
        Tuple of (hand1, hand2, hand3) for players 1, 2, 3
    """
    # Calculate expected hand sizes
    # Each player should have 13 cards total
    # Some cards are already known (passed cards), rest come from card_probs
    expected_sizes = [13, 13, 13]
    
    # Count passed cards per player
    passed_counts = [0, 0, 0]
    for player_id, cards in beliefs.passed_cards.items():
        opp_idx = player_id - 1
        if 0 <= opp_idx < 3:
            passed_counts[opp_idx] = len(cards)
    
    # Expected final size is always 13, but we need to assign
    # (13 - passed_counts[i]) cards from card_probs to each player
    # Total cards in card_probs may be less than sum if cards have been played
    
    # Use rejection sampling with early constraint checking
    for attempt in range(max_rejections):
        hands = [set() for _ in range(3)]
        
        # Add known passed cards
        for player_id, cards in beliefs.passed_cards.items():
            opp_idx = player_id - 1
            if 0 <= opp_idx < 3:
                hands[opp_idx].update(cards)
        
        # Sample remaining cards
        cards_to_assign = list(beliefs.card_probs.keys())
        rng.shuffle(cards_to_assign)  # Randomize order
        
        # Track current hand sizes
        current_sizes = [len(hand) for hand in hands]
        
        # Assign cards weighted by probabilities
        for card in cards_to_assign:
            probs = beliefs.card_probs[card].copy()
            
            # Zero out probabilities for players who:
            # 1. Have reached expected hand size
            # 2. Are void in this card's suit
            for opp_idx in range(3):
                player_id = opp_idx + 1
                
                # Check hand size constraint
                if current_sizes[opp_idx] >= expected_sizes[opp_idx]:
                    probs[opp_idx] = 0.0
                
                # Check void constraint
                if (player_id, card.suit) in beliefs.voids:
                    probs[opp_idx] = 0.0
            
            # Renormalize
            total = probs.sum()
            if total == 0:
                # No valid assignment - reject this sample
                break
            
            probs /= total
            
            # Sample assignment
            opp_idx = rng.choice(3, p=probs)
            hands[opp_idx].add(card)
            current_sizes[opp_idx] += 1
        
        # Check if all constraints satisfied
        valid = True
        for opp_idx in range(3):
            # Check hand size
            if len(hands[opp_idx]) != expected_sizes[opp_idx]:
                valid = False
                break
            
            # Check voids
            player_id = opp_idx + 1
            for suit in Suit:
                if (player_id, suit) in beliefs.voids:
                    # Check that hand has no cards of this suit
                    if any(card.suit == suit for card in hands[opp_idx]):
                        valid = False
                        break
            if not valid:
                break
        
        if valid:
            return tuple(hands)
    
    # If we've exhausted rejections, return best-effort assignment
    # This should rarely happen, but handle it gracefully
    hands = [set() for _ in range(3)]
    
    # Add known passed cards
    for player_id, cards in beliefs.passed_cards.items():
        opp_idx = player_id - 1
        if 0 <= opp_idx < 3:
            hands[opp_idx].update(cards)
    
    # Greedy assignment for remaining cards
    cards_to_assign = list(beliefs.card_probs.keys())
    for card in cards_to_assign:
        probs = beliefs.card_probs[card].copy()
        
        # Apply constraints
        for opp_idx in range(3):
            player_id = opp_idx + 1
            if len(hands[opp_idx]) >= expected_sizes[opp_idx]:
                probs[opp_idx] = 0.0
            if (player_id, card.suit) in beliefs.voids:
                probs[opp_idx] = 0.0
        
        total = probs.sum()
        if total > 0:
            probs /= total
            opp_idx = rng.choice(3, p=probs)
            hands[opp_idx].add(card)
        else:
            # No valid assignment - assign to first available player
            for opp_idx in range(3):
                if len(hands[opp_idx]) < expected_sizes[opp_idx]:
                    hands[opp_idx].add(card)
                    break
    
    return tuple(hands)
