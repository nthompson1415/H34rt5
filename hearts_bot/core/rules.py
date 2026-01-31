"""Game rules and validation for Hearts."""

from typing import Optional

from .cards import Card, Suit, TWO_OF_CLUBS, QUEEN_OF_SPADES
from .game_state import Trick


def get_legal_moves(
    hand: set[Card],
    trick: Trick,
    hearts_broken: bool,
    is_first_trick: bool = False
) -> list[Card]:
    """
    Return all legal cards to play.
    
    Rules:
    - Must follow suit if able
    - Cannot lead hearts unless broken or hand contains only hearts
    - First trick: 2♣ must lead, no points allowed (hearts and Q♠ cannot be played)
    """
    legal = []
    
    # If trick is empty, we're leading
    if not trick.cards:
        # First trick: must lead 2♣ if we have it
        if is_first_trick:
            if TWO_OF_CLUBS in hand:
                return [TWO_OF_CLUBS]
            else:
                # Can't lead first trick if we don't have 2♣
                return []
        
        # Check if we can lead hearts
        can_lead_hearts = hearts_broken or all(card.suit == Suit.HEARTS for card in hand)
        
        for card in hand:
            if card.suit == Suit.HEARTS and not can_lead_hearts:
                continue
            legal.append(card)
        
        return legal
    
    # Not leading - must follow suit if able
    led_suit = trick.led_suit
    if led_suit is None:
        raise ValueError("Trick has cards but no led suit")
    
    # Check if we have cards of the led suit
    cards_of_suit = [card for card in hand if card.suit == led_suit]
    
    if cards_of_suit:
        # Must follow suit
        legal = cards_of_suit
    else:
        # Void in led suit - can play any card
        legal = list(hand)
    
    # First trick: no points allowed
    if is_first_trick:
        legal = [
            card for card in legal
            if card.suit != Suit.HEARTS and card != QUEEN_OF_SPADES
        ]
    
    return legal


def resolve_trick(trick: Trick) -> tuple[int, int]:
    """
    Return (winner_player_id, points_taken).
    
    Winner is highest card of led suit.
    Points are sum of hearts (1 each) and Q♠ (13).
    """
    if not trick.cards:
        raise ValueError("Cannot resolve empty trick")
    
    winner = trick.winner()
    points = trick.points()
    
    return winner, points


def calculate_round_score(tricks: list[Trick]) -> dict[int, int]:
    """
    Calculate scores for each player in the round.
    
    Handles shoot-the-moon: if one player takes all 26 points,
    they get 0 and all opponents get 26.
    """
    # Sum points per player
    player_points: dict[int, int] = {}
    
    for trick in tricks:
        winner, points = resolve_trick(trick)
        player_points[winner] = player_points.get(winner, 0) + points
    
    # Check for shoot-the-moon (all 26 points taken by one player)
    total_points = sum(player_points.values())
    if total_points == 26:
        # Check if one player has all 26
        for player_id, points in player_points.items():
            if points == 26:
                # Shoot the moon: that player gets 0, others get 26
                result = {}
                for pid in range(4):
                    if pid == player_id:
                        result[pid] = 0
                    else:
                        result[pid] = 26
                return result
    
    # Normal scoring
    # Ensure all players are in the result (with 0 if needed)
    result = {}
    for player_id in range(4):
        result[player_id] = player_points.get(player_id, 0)
    
    return result
