"""Card representation and deck generation for Hearts."""

from enum import IntEnum
from dataclasses import dataclass


class Suit(IntEnum):
    """Card suits."""
    CLUBS = 0
    DIAMONDS = 1
    SPADES = 2
    HEARTS = 3


class Rank(IntEnum):
    """Card ranks."""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


@dataclass(frozen=True, order=True)
class Card:
    """Represents a playing card."""
    rank: Rank
    suit: Suit
    
    def __hash__(self) -> int:
        """Hash based on rank and suit."""
        return hash((self.rank, self.suit))
    
    def __repr__(self) -> str:
        """String representation of card (e.g., 'Q♠', '2♣')."""
        rank_str = {
            Rank.TWO: "2",
            Rank.THREE: "3",
            Rank.FOUR: "4",
            Rank.FIVE: "5",
            Rank.SIX: "6",
            Rank.SEVEN: "7",
            Rank.EIGHT: "8",
            Rank.NINE: "9",
            Rank.TEN: "10",
            Rank.JACK: "J",
            Rank.QUEEN: "Q",
            Rank.KING: "K",
            Rank.ACE: "A",
        }[self.rank]
        
        suit_str = {
            Suit.CLUBS: "♣",
            Suit.DIAMONDS: "♦",
            Suit.SPADES: "♠",
            Suit.HEARTS: "♥",
        }[self.suit]
        
        return f"{rank_str}{suit_str}"


# Generate full deck
DECK: frozenset[Card] = frozenset(
    Card(rank=rank, suit=suit)
    for suit in Suit
    for rank in Rank
)

# Special cards
TWO_OF_CLUBS: Card = Card(rank=Rank.TWO, suit=Suit.CLUBS)
QUEEN_OF_SPADES: Card = Card(rank=Rank.QUEEN, suit=Suit.SPADES)
