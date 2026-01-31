"""Monte Carlo card selection algorithm."""

import copy
import numpy as np

from hearts_bot.core.cards import Card, TWO_OF_CLUBS
from hearts_bot.core.game_state import RoundState, Trick
from hearts_bot.core.rules import get_legal_moves
from hearts_bot.engine.heuristics import check_overrides
from hearts_bot.engine.simulator import continue_simulation
from hearts_bot.inference.beliefs import BeliefState
from hearts_bot.inference.sampler import sample_world


def select_card(
    game_state: RoundState,
    beliefs: BeliefState,
    hand: set[Card],
    n_samples: int = 1000,
    rng: np.random.Generator = None
) -> Card:
    """
    Monte Carlo card selection.
    
    Algorithm:
    1. Check for heuristic override
    2. Get legal moves
    3. For each sample:
       a. Sample consistent world from beliefs
       b. For each legal move:
          - Clone state, apply move
          - Simulate to round end using simulation_policy
          - Record points taken by bot
    4. Return card with lowest average points
    
    Args:
        game_state: Current round state
        beliefs: Current belief state
        hand: Bot's current hand
        n_samples: Number of Monte Carlo samples
        rng: Random number generator
    
    Returns:
        Best card to play
    """
    if rng is None:
        rng = np.random.default_rng()
    
    # Check for heuristic override
    is_first_trick = (len(game_state.tricks_taken) == 0 and not game_state.current_trick.cards)
    legal = get_legal_moves(
        hand,
        game_state.current_trick,
        game_state.hearts_broken,
        is_first_trick=is_first_trick
    )
    
    if not legal:
        # Fallback: play any card
        legal = list(hand)
    
    override = check_overrides(hand, game_state, legal)
    if override is not None:
        return override
    
    # Track points for each legal move
    move_points: dict[Card, list[float]] = {card: [] for card in legal}
    
    # Monte Carlo sampling
    for _ in range(n_samples):
        # Sample consistent world
        opp_hands = sample_world(beliefs, rng)
        
        # For each legal move, simulate and record points
        for move in legal:
            # Clone game state
            sim_state = copy.deepcopy(game_state)
            sim_hand = hand.copy()
            
            # Apply move
            sim_hand.remove(move)
            sim_state.hands[0] = sim_hand.copy()
            
            # Update current trick
            if not sim_state.current_trick.cards:
                # Starting new trick - we're leading
                sim_state.current_trick.leader = 0
            sim_state.current_trick.cards.append((0, move))
            
            # Check if hearts broken
            if move.suit == 3:  # Suit.HEARTS
                sim_state.hearts_broken = True
            
            # Determine next player
            if len(sim_state.current_trick.cards) == 4:
                # Trick complete - resolve it
                from hearts_bot.core.rules import resolve_trick
                winner, _ = resolve_trick(sim_state.current_trick)
                sim_state.tricks_taken.append(sim_state.current_trick)
                sim_state.current_trick = Trick()
                sim_state.current_trick.leader = winner
                next_player = winner
            else:
                # Continue current trick
                next_player = (sim_state.current_trick.cards[-1][0] + 1) % 4
            
            # Build full hands for simulation
            sim_hands = {
                0: sim_hand,
                1: opp_hands[0],
                2: opp_hands[1],
                3: opp_hands[2],
            }
            
            # Continue simulation from current state
            try:
                scores = continue_simulation(sim_state, sim_hands, next_player, rng)
                bot_points = scores.get(0, 0)
                move_points[move].append(float(bot_points))
            except Exception:
                # Simulation failed - assign high penalty
                move_points[move].append(26.0)
    
    # Calculate average points for each move
    move_averages = {
        card: np.mean(points) if points else 26.0
        for card, points in move_points.items()
    }
    
    # Return card with lowest average points
    best_card = min(move_averages, key=move_averages.get)
    return best_card
