"""Fast heuristic policy for simulation and override checks."""

from typing import Optional

from hearts_bot.core.cards import Card, Suit, QUEEN_OF_SPADES, TWO_OF_CLUBS
from hearts_bot.core.game_state import RoundState, Trick
from hearts_bot.core.rules import get_legal_moves


def check_overrides(
    hand: set[Card],
    game_state: RoundState,
    legal: list[Card]
) -> Optional[Card]:
    """
    Hard rules that skip MC.
    
    Returns:
        Card to play if override applies, None otherwise
    """
    # Only one legal move
    if len(legal) == 1:
        return legal[0]
    
    # Must play 2♣ (first trick, we have it, we're leading)
    if TWO_OF_CLUBS in legal:
        # Check if we're leading first trick
        if not game_state.current_trick.cards and len(game_state.tricks_taken) == 0:
            return TWO_OF_CLUBS
    
    # Guaranteed safe dump: last to play, can't win, no points in trick
    if len(game_state.current_trick.cards) == 3:
        trick = game_state.current_trick
        if trick.led_suit is not None:
            # Check if we can win
            led_suit = trick.led_suit
            highest_in_trick = max(
                (card.rank for player, card in trick.cards if card.suit == led_suit),
                default=None
            )
            
            # Check if we have a card that can win
            can_win = False
            if highest_in_trick is not None:
                for card in legal:
                    if card.suit == led_suit and card.rank > highest_in_trick:
                        can_win = True
                        break
            
            # If we can't win, check if trick has no points
            if not can_win:
                points_in_trick = trick.points()
                if points_in_trick == 0:
                    # Safe dump - play highest card we can
                    if legal:
                        return max(legal, key=lambda c: c.rank)
    
    return None


def simulation_policy(
    hand: set[Card],
    game_state: RoundState,
    player: int
) -> Card:
    """
    Fast, reasonable policy for playout simulation.
    
    Priority order:
    1. Follow suit if required
    2. If can't win trick, play highest legal card (dump points if possible)
    3. If winning trick, play lowest winning card
    4. Avoid taking Q♠ if possible
    5. Don't lead Q♠ early
    6. Lead low cards to probe voids
    """
    trick = game_state.current_trick
    is_first_trick = (len(game_state.tricks_taken) == 0 and not trick.cards)
    
    legal = get_legal_moves(hand, trick, game_state.hearts_broken, is_first_trick)
    
    if not legal:
        # Fallback: play any card
        legal = list(hand)
    
    if len(legal) == 1:
        return legal[0]
    
    # If leading (empty trick)
    if not trick.cards:
        # Priority 5: Don't lead Q♠ early
        if QUEEN_OF_SPADES in legal and len(game_state.tricks_taken) < 3:
            legal = [c for c in legal if c != QUEEN_OF_SPADES]
            if not legal:
                legal = list(hand)
        
        # Priority 6: Lead low cards to probe voids
        return min(legal, key=lambda c: c.rank)
    
    # Not leading - check if we must follow suit
    led_suit = trick.led_suit
    if led_suit is None:
        raise ValueError("Trick has cards but no led suit")
    
    cards_of_suit = [c for c in legal if c.suit == led_suit]
    
    if cards_of_suit:
        # We have cards of led suit
        # Find highest card in trick of led suit
        highest_in_trick = max(
            (card.rank for player, card in trick.cards if card.suit == led_suit),
            default=None
        )
        
        if highest_in_trick is not None:
            # Check if we can win
            winning_cards = [
                c for c in cards_of_suit
                if c.rank > highest_in_trick
            ]
            
            if winning_cards:
                # Priority 3: If winning, play lowest winning card
                return min(winning_cards, key=lambda c: c.rank)
            else:
                # Priority 2: Can't win, play highest to dump points
                return max(cards_of_suit, key=lambda c: c.rank)
        else:
            # No cards of led suit in trick (shouldn't happen, but handle it)
            return max(cards_of_suit, key=lambda c: c.rank)
    else:
        # Void in led suit - can play any card
        # Priority 4: Avoid taking Q♠ if possible
        if QUEEN_OF_SPADES in legal:
            # Check if Q♠ would win the trick
            trick_points = trick.points()
            # If trick already has points, try to avoid adding Q♠
            if trick_points > 0:
                # Try to find a non-point card
                non_point_cards = [
                    c for c in legal
                    if c.suit != Suit.HEARTS and c != QUEEN_OF_SPADES
                ]
                if non_point_cards:
                    return max(non_point_cards, key=lambda c: c.rank)
            
            # If we must take points anyway, or trick is safe, play highest non-Q♠ if possible
            safe_cards = [c for c in legal if c != QUEEN_OF_SPADES]
            if safe_cards:
                return max(safe_cards, key=lambda c: c.rank)
        
        # Priority 2: Play highest card to dump points if possible
        return max(legal, key=lambda c: c.rank)
