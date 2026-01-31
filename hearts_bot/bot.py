"""Top-level interface for the Hearts bot."""

import numpy as np

from hearts_bot.core.cards import Card
from hearts_bot.core.game_state import GameState, RoundState
from hearts_bot.engine.mcts import select_card
from hearts_bot.inference.beliefs import BeliefState
from hearts_bot.inference.updater import (
    CardPlayedObservation,
    TrickCompleteObservation,
    VoidShownObservation,
    infer_voids_from_trick,
    update_beliefs,
)


class HeartsBot:
    """Monte Carlo Hearts bot with belief tracking."""
    
    def __init__(self, seed: int = None, n_samples: int = 1000):
        """
        Initialize bot.
        
        Args:
            seed: Random seed for reproducibility
            n_samples: Number of Monte Carlo samples per decision
        """
        self.rng = np.random.default_rng(seed)
        self.n_samples = n_samples
        self.beliefs: BeliefState = None
        self.hand: set[Card] = None
    
    def initialize_beliefs(self, hand: set[Card], passed_cards: dict[int, set[Card]] = None) -> None:
        """
        Initialize belief state after receiving hand and passing.
        
        Args:
            hand: Bot's hand after passing
            passed_cards: Dict mapping player_id -> cards we passed to them
        """
        self.hand = hand
        self.beliefs = BeliefState.initialize(hand, passed_cards)
    
    def pass_cards(self, hand: set[Card], direction: str) -> set[Card]:
        """
        Strategy for passing cards.
        
        Simple strategy: pass 3 highest cards.
        
        Args:
            hand: Bot's hand before passing
            direction: 'left', 'right', 'across', or 'hold'
        
        Returns:
            Set of 3 cards to pass (empty if direction is 'hold')
        """
        if direction == 'hold':
            return set()
        
        # Simple strategy: pass 3 highest cards
        hand_list = sorted(hand, reverse=True)
        return set(hand_list[:3])
    
    def play_card(self, game_state: GameState) -> Card:
        """
        Main interface for playing a card.
        
        Args:
            game_state: Current game state
        
        Returns:
            Card to play
        """
        if self.hand is None:
            raise ValueError("Bot not initialized - call initialize_beliefs first")
        
        if self.beliefs is None:
            raise ValueError("Beliefs not initialized")
        
        # Use MCTS to select card
        card = select_card(
            game_state.round,
            self.beliefs,
            self.hand,
            n_samples=self.n_samples,
            rng=self.rng
        )
        
        return card
    
    def update_beliefs_from_observation(self, observation) -> None:
        """
        Update beliefs based on an observation.
        
        Args:
            observation: Observation object (CardPlayedObservation, etc.)
        """
        if self.beliefs is None:
            return
        
        update_beliefs(self.beliefs, observation)
    
    def observe_card_played(self, player: int, card: Card) -> None:
        """Observe that a card was played."""
        if self.beliefs is None:
            return
        
        obs = CardPlayedObservation(player, card)
        update_beliefs(self.beliefs, obs)
        
        # If it's our card, remove from hand
        if player == 0 and card in self.hand:
            self.hand.remove(card)
    
    def observe_trick_complete(self, trick) -> None:
        """Observe that a trick is complete."""
        if self.beliefs is None:
            return
        
        # Infer voids from trick
        void_observations = infer_voids_from_trick(trick)
        for obs in void_observations:
            update_beliefs(self.beliefs, obs)
        
        # Record card plays
        for player, card in trick.cards:
            self.observe_card_played(player, card)
