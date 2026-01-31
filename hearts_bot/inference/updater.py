"""Bayesian belief updates on observations."""

from typing import Union

from hearts_bot.core.cards import Card, Suit
from hearts_bot.core.game_state import Trick
from hearts_bot.inference.beliefs import BeliefState


class Observation:
    """Base class for observations."""
    pass


class CardPlayedObservation(Observation):
    """Observation that a card was played by a player."""
    def __init__(self, player: int, card: Card):
        self.player = player
        self.card = card


class VoidShownObservation(Observation):
    """Observation that a player showed void in a suit."""
    def __init__(self, player: int, suit: Suit):
        self.player = player
        self.suit = suit


class TrickCompleteObservation(Observation):
    """Observation that a trick is complete - can infer from plays."""
    def __init__(self, trick: Trick):
        self.trick = trick


def update_beliefs(beliefs: BeliefState, observation: Observation) -> BeliefState:
    """
    Process observations and update beliefs.
    
    Args:
        beliefs: Current belief state
        observation: Observation to process
    
    Returns:
        Updated belief state (may be same object, modified in place)
    """
    if isinstance(observation, CardPlayedObservation):
        # Card was played - remove from probabilities
        beliefs.update_card_played(observation.player, observation.card)
        beliefs._renormalize()
    
    elif isinstance(observation, VoidShownObservation):
        # Player showed void in suit
        beliefs.update_void_shown(observation.player, observation.suit)
    
    elif isinstance(observation, TrickCompleteObservation):
        # Trick complete - infer voids from plays
        trick = observation.trick
        if trick.led_suit is not None:
            led_suit = trick.led_suit
            
            # For each player in the trick
            for player_id, card in trick.cards:
                # If player played a different suit, they're void in led suit
                if card.suit != led_suit:
                    beliefs.update_void_shown(player_id, led_suit)
    
    return beliefs


def infer_voids_from_trick(trick: Trick) -> list[VoidShownObservation]:
    """
    Infer void observations from a completed trick.
    
    If a player didn't follow suit, they're void in that suit.
    """
    observations = []
    
    if trick.led_suit is None:
        return observations
    
    led_suit = trick.led_suit
    
    for player_id, card in trick.cards:
        if card.suit != led_suit:
            observations.append(VoidShownObservation(player_id, led_suit))
    
    return observations
