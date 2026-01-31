"""Example usage of the Hearts bot."""

import sys
sys.path.insert(0, '.')

import numpy as np
from hearts_bot.bot import HeartsBot
from hearts_bot.core.cards import Card, Rank, Suit
from hearts_bot.core.game_state import GameState, RoundState, Trick
from hearts_bot.game_runner import deal_hands, pass_cards, random_player
import random


def example_basic_usage():
    """Basic example of using the bot."""
    print("=" * 60)
    print("Example 1: Basic Bot Usage")
    print("=" * 60)
    
    # Create a bot
    bot = HeartsBot(seed=42, n_samples=500)  # Use fewer samples for faster decisions
    
    # Simulate receiving a hand after dealing
    rng = random.Random(42)
    hands = deal_hands(rng)
    bot_hand = hands[0]  # Bot is player 0
    
    # Simulate passing phase
    pass_dir = "left"  # Round 1: pass left
    passed_cards = bot.pass_cards(bot_hand, pass_dir)
    print(f"\nBot's hand before passing: {len(bot_hand)} cards")
    print(f"Cards to pass: {sorted(passed_cards, reverse=True)[:3]}")
    
    # Remove passed cards and add received cards (simplified)
    bot_hand -= passed_cards
    # In real game, you'd receive 3 cards from the player to your right
    
    # Initialize beliefs
    bot.initialize_beliefs(bot_hand, passed_cards={1: passed_cards})
    print(f"Bot's hand after passing: {len(bot_hand)} cards")
    
    # Create a game state
    game_state = GameState()
    game_state.round = RoundState()
    game_state.round.hands = {0: bot_hand}
    game_state.round.hearts_broken = False
    game_state.round.current_trick = Trick()
    
    # Bot decides which card to play
    if len(bot_hand) > 0:
        card = bot.play_card(game_state)
        print(f"\nBot decides to play: {card}")
        print(f"Remaining cards: {len(bot_hand) - 1}")


def example_full_round():
    """Example of playing a full round."""
    print("\n" + "=" * 60)
    print("Example 2: Playing a Full Round (Simplified)")
    print("=" * 60)
    
    # Create bot
    bot = HeartsBot(seed=42, n_samples=200)  # Fewer samples for demo speed
    
    # Deal hands
    rng = random.Random(42)
    hands = deal_hands(rng)
    bot_hand = hands[0]
    
    # Passing
    pass_dir = "left"
    passed = bot.pass_cards(bot_hand, pass_dir)
    bot_hand -= passed
    
    # Initialize bot
    bot.initialize_beliefs(bot_hand, passed_cards={1: passed})
    
    # Find starting player (who has 2♣)
    from hearts_bot.core.cards import TWO_OF_CLUBS
    starting_player = None
    for i, hand in enumerate(hands):
        if TWO_OF_CLUBS in hand:
            starting_player = i
            break
    
    print(f"\nStarting player: {starting_player}")
    print(f"Bot hand size: {len(bot_hand)}")
    
    # Play a few tricks (simplified - just show bot's decisions)
    game_state = GameState()
    game_state.round = RoundState()
    game_state.round.hands = {0: bot_hand.copy()}
    game_state.round.hearts_broken = False
    game_state.round.tricks_taken = []
    
    print("\nPlaying tricks (bot's perspective):")
    for trick_num in range(3):  # Just show first 3 tricks
        if len(bot_hand) == 0:
            break
            
        game_state.round.current_trick = Trick()
        if trick_num == 0:
            game_state.round.current_trick.leader = starting_player
        
        # If bot is to play
        if game_state.round.current_trick.leader == 0 or len(game_state.round.current_trick.cards) > 0:
            card = bot.play_card(game_state)
            print(f"  Trick {trick_num + 1}: Bot plays {card}")
            bot_hand.remove(card)
            game_state.round.hands[0] = bot_hand.copy()
            bot.observe_card_played(0, card)
            
            # Update trick
            game_state.round.current_trick.cards.append((0, card))
            
            if card.suit == Suit.HEARTS:
                game_state.round.hearts_broken = True


def example_with_random_opponents():
    """Example of bot playing against random opponents."""
    print("\n" + "=" * 60)
    print("Example 3: Bot vs Random Players (One Round)")
    print("=" * 60)
    
    from hearts_bot.game_runner import HeartsGame
    
    # Create bot
    bot = HeartsBot(seed=42, n_samples=100)  # Fast mode
    
    # Bot player function
    def bot_player(hand, game_state):
        if not hasattr(bot_player, 'initialized'):
            # Initialize on first call
            bot.initialize_beliefs(hand, {})
            bot_player.initialized = True
            bot_player.hand = hand
        
        # Update hand
        bot_player.hand = hand
        
        # Update game state in bot
        if not hasattr(bot, 'hand') or len(bot.hand) != len(hand):
            bot.hand = hand
        
        # Play card
        return bot.play_card(game_state)
    
    # Create game with bot + 3 random players
    player_functions = [
        bot_player,
        random_player,
        random_player,
        random_player,
    ]
    
    game = HeartsGame(player_functions, rng=random.Random(42))
    
    try:
        # Play one round
        scores = game.play_round()
        print(f"\nRound scores:")
        for player_id, points in scores.items():
            player_type = "Bot" if player_id == 0 else "Random"
            print(f"  Player {player_id} ({player_type}): {points} points")
    except Exception as e:
        print(f"Note: Full game requires more integration. Error: {e}")
        print("This is expected - the bot interface needs more game state updates.")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Hearts Bot Usage Examples")
    print("=" * 60)
    
    # Run examples
    example_basic_usage()
    example_full_round()
    example_with_random_opponents()
    
    print("\n" + "=" * 60)
    print("For more details, see the bot.py and game_runner.py files")
    print("=" * 60)
