"""Game simulation for playing rounds to completion."""

import numpy as np

from hearts_bot.core.cards import TWO_OF_CLUBS
from hearts_bot.core.game_state import RoundState, Trick
from hearts_bot.core.rules import calculate_round_score, get_legal_moves, resolve_trick
from hearts_bot.engine.heuristics import simulation_policy


def simulate_round(
    hands: dict[int, set],
    starting_player: int,
    rng: np.random.Generator
) -> dict[int, int]:
    """
    Play round to completion given 4 hands.
    
    Args:
        hands: Dict mapping player_id -> set of cards
        starting_player: Player who leads first trick (has 2♣)
        rng: Random number generator
    
    Returns:
        Dict mapping player_id -> points taken in round
    """
    # Create round state
    round_state = RoundState()
    round_state.hands = {pid: hand.copy() for pid, hand in hands.items()}
    round_state.hearts_broken = False
    
    current_player = starting_player
    
    # Play 13 tricks
    for trick_num in range(13):
        trick = Trick(leader=current_player)
        round_state.current_trick = trick
        
        # Play 4 cards
        for _ in range(4):
            hand = round_state.hands[current_player]
            is_first_trick = (trick_num == 0)
            
            legal = get_legal_moves(
                hand,
                trick,
                round_state.hearts_broken,
                is_first_trick=is_first_trick
            )
            
            if not legal:
                # Fallback: play any card (shouldn't happen, but handle it)
                legal = list(hand)
            
            # Use simulation policy to choose card
            card = simulation_policy(hand, round_state, current_player)
            
            # If policy returned invalid card, pick randomly from legal
            if card not in legal:
                card = rng.choice(legal)
            
            # Play card
            trick.cards.append((current_player, card))
            round_state.hands[current_player].remove(card)
            
            # Check if hearts broken
            if card.suit == 3:  # Suit.HEARTS
                round_state.hearts_broken = True
            
            # Move to next player
            current_player = (current_player + 1) % 4
        
        # Resolve trick
        winner, _ = resolve_trick(trick)
        round_state.tricks_taken.append(trick)
        current_player = winner
    
    # Calculate and return scores
    scores = calculate_round_score(round_state.tricks_taken)
    return scores


def continue_simulation(
    round_state: RoundState,
    hands: dict[int, set],
    current_player: int,
    rng: np.random.Generator
) -> dict[int, int]:
    """
    Continue simulation from a partial round state.
    
    Args:
        round_state: Partial round state (may have tricks_taken and current_trick)
        hands: Current hands for all players
        current_player: Next player to move
        rng: Random number generator
    
    Returns:
        Dict mapping player_id -> points taken in round (cumulative with existing tricks)
    """
    # Update hands in round state
    round_state.hands = {pid: hand.copy() for pid, hand in hands.items()}
    
    # Count remaining tricks to play
    tricks_played = len(round_state.tricks_taken)
    remaining_tricks = 13 - tricks_played
    
    # If current trick is in progress, complete it first
    if round_state.current_trick.cards:
        # Continue current trick
        while len(round_state.current_trick.cards) < 4:
            hand = round_state.hands[current_player]
            is_first_trick = (tricks_played == 0)
            
            legal = get_legal_moves(
                hand,
                round_state.current_trick,
                round_state.hearts_broken,
                is_first_trick=is_first_trick
            )
            
            if not legal:
                legal = list(hand)
            
            card = simulation_policy(hand, round_state, current_player)
            if card not in legal:
                card = rng.choice(legal)
            
            round_state.current_trick.cards.append((current_player, card))
            round_state.hands[current_player].remove(card)
            
            if card.suit == 3:  # Suit.HEARTS
                round_state.hearts_broken = True
            
            current_player = (current_player + 1) % 4
        
        # Resolve trick
        winner, _ = resolve_trick(round_state.current_trick)
        round_state.tricks_taken.append(round_state.current_trick)
        round_state.current_trick = Trick()
        round_state.current_trick.leader = winner
        current_player = winner
        remaining_tricks -= 1
    
    # Play remaining tricks
    for _ in range(remaining_tricks):
        trick = Trick(leader=current_player)
        round_state.current_trick = trick
        
        for _ in range(4):
            hand = round_state.hands[current_player]
            is_first_trick = (len(round_state.tricks_taken) == 0)
            
            legal = get_legal_moves(
                hand,
                trick,
                round_state.hearts_broken,
                is_first_trick=is_first_trick
            )
            
            if not legal:
                legal = list(hand)
            
            card = simulation_policy(hand, round_state, current_player)
            if card not in legal:
                card = rng.choice(legal)
            
            trick.cards.append((current_player, card))
            round_state.hands[current_player].remove(card)
            
            if card.suit == 3:  # Suit.HEARTS
                round_state.hearts_broken = True
            
            current_player = (current_player + 1) % 4
        
        winner, _ = resolve_trick(trick)
        round_state.tricks_taken.append(trick)
        round_state.current_trick = Trick()
        round_state.current_trick.leader = winner
        current_player = winner
    
    # Calculate scores
    scores = calculate_round_score(round_state.tricks_taken)
    return scores
