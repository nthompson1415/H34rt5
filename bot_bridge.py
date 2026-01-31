"""
Bridge module for web interface.
Provides a simple API for JavaScript to interact with the Hearts bot.
"""

import sys
from hearts_bot.bot import HeartsBot
from hearts_bot.core.cards import Card, Rank, Suit
from hearts_bot.core.game_state import GameState, RoundState, Trick

def create_card(rank, suit):
    """Create a Card from rank and suit integers."""
    return Card(rank=Rank(rank), suit=Suit(suit))

def create_bot(seed=None, n_samples=500):
    """Create a HeartsBot instance."""
    return HeartsBot(seed=seed, n_samples=n_samples)

def get_best_move(bot, hand_cards, hearts_broken, is_first_trick, trick_cards, n_samples):
    """
    Get the best move for the bot.
    
    Args:
        bot: HeartsBot instance
        hand_cards: List of (rank, suit) tuples for bot's hand
        hearts_broken: Boolean
        is_first_trick: Boolean
        trick_cards: List of (player, rank, suit) tuples for current trick
        n_samples: Number of Monte Carlo samples
    
    Returns:
        (rank, suit) tuple of best card
    """
    # Create bot's hand
    hand = set(create_card(rank, suit) for rank, suit in hand_cards)
    
    # Initialize bot if needed
    if bot.beliefs is None:
        bot.initialize_beliefs(hand, {})
    else:
        bot.hand = hand
    
    # Create game state
    game_state = GameState()
    game_state.round = RoundState()
    game_state.round.hands = {0: hand.copy()}
    game_state.round.hearts_broken = hearts_broken
    game_state.round.current_trick = Trick()
    
    # Add trick cards
    for player, rank, suit in trick_cards:
        card = create_card(rank, suit)
        game_state.round.current_trick.cards.append((player, card))
    
    # Set leader if trick is empty
    if trick_cards:
        game_state.round.current_trick.leader = trick_cards[0][0]
    
    # Update bot's n_samples
    bot.n_samples = n_samples
    
    # Get best move
    best_card = bot.play_card(game_state)
    
    return (best_card.rank.value, best_card.suit.value)
