"""Game state data structures for Hearts."""

from dataclasses import dataclass, field
from typing import Optional

from .cards import Card, Suit, TWO_OF_CLUBS, QUEEN_OF_SPADES


@dataclass
class Trick:
    """Represents a single trick in Hearts."""
    cards: list[tuple[int, Card]] = field(default_factory=list)  # (player_id, card) in play order
    leader: int = 0
    
    @property
    def led_suit(self) -> Optional[Suit]:
        """Return the suit that was led, or None if no cards played yet."""
        if not self.cards:
            return None
        return self.cards[0][1].suit
    
    def winner(self) -> int:
        """Return the player_id of the trick winner."""
        if not self.cards:
            raise ValueError("Cannot determine winner of empty trick")
        
        led_suit = self.led_suit
        if led_suit is None:
            raise ValueError("No suit led")
        
        # Find highest card of led suit
        winning_card = None
        winning_player = None
        
        for player_id, card in self.cards:
            if card.suit == led_suit:
                if winning_card is None or card.rank > winning_card.rank:
                    winning_card = card
                    winning_player = player_id
        
        return winning_player
    
    def points(self) -> int:
        """Return total points in this trick."""
        total = 0
        for _, card in self.cards:
            if card.suit == Suit.HEARTS:
                total += 1
            elif card == QUEEN_OF_SPADES:
                total += 13
        return total


@dataclass
class RoundState:
    """State of a single round of Hearts."""
    hands: dict[int, set[Card]] = field(default_factory=dict)  # player_id -> current hand
    tricks_taken: list[Trick] = field(default_factory=list)
    current_trick: Trick = field(default_factory=Trick)
    hearts_broken: bool = False


@dataclass
class GameState:
    """Full game state including scores and round information."""
    scores: list[int] = field(default_factory=lambda: [0, 0, 0, 0])  # cumulative scores per player
    round: RoundState = field(default_factory=RoundState)
    round_number: int = 1
    pass_direction: str = "left"  # 'left', 'right', 'across', 'hold'
    
    def get_pass_direction(self) -> str:
        """Calculate pass direction based on round number (cycles every 4 rounds)."""
        round_in_cycle = (self.round_number - 1) % 4
        if round_in_cycle == 0:
            return "left"
        elif round_in_cycle == 1:
            return "right"
        elif round_in_cycle == 2:
            return "across"
        else:
            return "hold"
