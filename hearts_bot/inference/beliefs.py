"""Belief state representation for tracking opponent hand distributions."""

import numpy as np
from dataclasses import dataclass, field

from hearts_bot.core.cards import Card, DECK, Suit


@dataclass
class BeliefState:
    """
    Track probability distribution over opponent hands.
    
    For each unknown card (not in bot's hand, not yet played),
    maintain P(card belongs to player_i) for i in {1, 2, 3}.
    
    Constraints:
    - Sum across players = 1.0 for each card
    - Sum of probabilities per player = expected hand size
    """
    
    # Map from Card -> [P(p1), P(p2), P(p3)]
    card_probs: dict[Card, np.ndarray] = field(default_factory=dict)
    
    # Known voids: if player showed void in suit, P = 0 for all cards in suit
    voids: set[tuple[int, Suit]] = field(default_factory=set)
    
    # Cards we passed to specific player (known holdings)
    passed_cards: dict[int, set[Card]] = field(default_factory=dict)
    
    def update_card_played(self, player: int, card: Card) -> None:
        """
        Collapse probability for played card.
        
        When a card is played, we know it belonged to that player.
        Remove it from card_probs and renormalize remaining probabilities.
        """
        if card in self.card_probs:
            del self.card_probs[card]
    
    def update_void_shown(self, player: int, suit: Suit) -> None:
        """
        Zero out suit probabilities for player.
        
        When a player shows void in a suit (by playing a different suit
        when they could have followed), set P=0 for all cards in that suit
        for that player, then renormalize.
        """
        self.voids.add((player, suit))
        
        # Zero out probabilities for this player-suit combination
        for card in self.card_probs:
            if card.suit == suit:
                # Get player index (0-based for opponents: 1, 2, 3)
                opp_idx = player - 1
                if 0 <= opp_idx < 3:
                    self.card_probs[card][opp_idx] = 0.0
        
        # Renormalize
        self._renormalize()
    
    def update_passed_cards(self, direction: str, cards: set[Card]) -> None:
        """
        Record passed cards.
        
        Args:
            direction: 'left', 'right', 'across', or 'hold'
            cards: Set of cards we passed
        """
        if direction == 'hold':
            return
        
        # Determine target player based on direction
        # Bot is player 0
        if direction == 'left':
            target = 1  # Pass to left (player 1)
        elif direction == 'right':
            target = 3  # Pass to right (player 3)
        elif direction == 'across':
            target = 2  # Pass to across (player 2)
        else:
            raise ValueError(f"Unknown direction: {direction}")
        
        if target not in self.passed_cards:
            self.passed_cards[target] = set()
        self.passed_cards[target].update(cards)
        
        # Update probabilities: these cards definitely belong to target
        for card in cards:
            if card in self.card_probs:
                # Set P=1 for target, P=0 for others
                opp_idx = target - 1
                if 0 <= opp_idx < 3:
                    self.card_probs[card][:] = 0.0
                    self.card_probs[card][opp_idx] = 1.0
    
    def _renormalize(self) -> None:
        """Renormalize probabilities to maintain constraints."""
        for card in self.card_probs:
            probs = self.card_probs[card]
            total = probs.sum()
            if total > 0:
                probs /= total
            else:
                # All zeros - reset to uniform (shouldn't happen, but handle it)
                probs[:] = 1.0 / 3.0
    
    @classmethod
    def initialize(
        cls,
        bot_hand: set[Card],
        passed_cards: dict[int, set[Card]] = None
    ) -> 'BeliefState':
        """
        Initialize belief state with uniform distribution over unknown cards.
        
        Args:
            bot_hand: Set of cards in bot's hand
            passed_cards: Dict mapping player_id -> set of cards we passed to them
        """
        beliefs = cls()
        
        if passed_cards is None:
            passed_cards = {}
        
        # Find all unknown cards (not in bot's hand)
        unknown_cards = DECK - bot_hand
        
        # Initialize probabilities
        for card in unknown_cards:
            # Check if we passed this card to someone
            known_owner = None
            for player_id, cards in passed_cards.items():
                if card in cards:
                    known_owner = player_id
                    break
            
            if known_owner is not None:
                # We know who has this card
                opp_idx = known_owner - 1
                if 0 <= opp_idx < 3:
                    probs = np.zeros(3)
                    probs[opp_idx] = 1.0
                    beliefs.card_probs[card] = probs
            else:
                # Uniform distribution over 3 opponents
                beliefs.card_probs[card] = np.array([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0])
        
        beliefs.passed_cards = passed_cards.copy()
        
        return beliefs
