"""Game execution framework for running Hearts games."""

import random
from typing import Callable, Optional

from hearts_bot.core.cards import Card, DECK, TWO_OF_CLUBS
from hearts_bot.core.game_state import GameState, RoundState, Trick
from hearts_bot.core.rules import calculate_round_score, get_legal_moves, resolve_trick


def deal_hands(rng: random.Random) -> list[set]:
    """Deal 52 cards into 4 hands of 13 cards each."""
    deck = list(DECK)
    rng.shuffle(deck)
    
    hands = []
    for i in range(4):
        start = i * 13
        end = start + 13
        hands.append(set(deck[start:end]))
    
    return hands


def pass_cards(hands: list[set], direction: str, rng: random.Random) -> list[set]:
    """
    Handle passing phase.
    
    Args:
        hands: List of 4 hands (player 0, 1, 2, 3)
        direction: 'left', 'right', 'across', or 'hold'
        rng: Random number generator
    
    Returns:
        Updated hands after passing
    """
    if direction == 'hold':
        return hands
    
    # Determine pass targets
    if direction == 'left':
        # Player i passes to player (i+1) % 4
        targets = [(i, (i + 1) % 4) for i in range(4)]
    elif direction == 'right':
        # Player i passes to player (i-1) % 4
        targets = [(i, (i - 1) % 4) for i in range(4)]
    elif direction == 'across':
        # Player i passes to player (i+2) % 4
        targets = [(i, (i + 2) % 4) for i in range(4)]
    else:
        raise ValueError(f"Unknown pass direction: {direction}")
    
    # Collect cards to pass
    cards_to_pass = {}
    for source, target in targets:
        # Simple strategy: pass 3 highest cards
        hand_list = sorted(hands[source], reverse=True)
        cards_to_pass[(source, target)] = set(hand_list[:3])
    
    # Remove passed cards from source hands
    new_hands = [hand.copy() for hand in hands]
    for (source, target), cards in cards_to_pass.items():
        new_hands[source] -= cards
    
    # Add passed cards to target hands
    for (source, target), cards in cards_to_pass.items():
        new_hands[target] |= cards
    
    return new_hands


class HeartsGame:
    """Manages a full game of Hearts."""
    
    def __init__(
        self,
        player_functions: list[Callable[[set, GameState], Card]],
        rng: Optional[random.Random] = None
    ):
        """
        Initialize game.
        
        Args:
            player_functions: List of 4 functions, each takes (hand, game_state) and returns Card
            rng: Random number generator (defaults to new Random())
        """
        self.player_functions = player_functions
        self.rng = rng or random.Random()
        self.game_state = GameState()
        self.hands = None
    
    def play_round(self) -> dict[int, int]:
        """Play one round and return scores."""
        # Deal hands
        self.hands = deal_hands(self.rng)
        
        # Handle passing
        pass_dir = self.game_state.get_pass_direction()
        self.hands = pass_cards(self.hands, pass_dir, self.rng)
        
        # Initialize round state
        round_state = RoundState()
        round_state.hands = {i: self.hands[i].copy() for i in range(4)}
        round_state.hearts_broken = False
        
        # Find player with 2♣ to lead first trick
        starting_player = None
        for i in range(4):
            if TWO_OF_CLUBS in round_state.hands[i]:
                starting_player = i
                break
        
        if starting_player is None:
            raise ValueError("No player has 2♣")
        
        # Play 13 tricks
        current_player = starting_player
        for trick_num in range(13):
            trick = Trick(leader=current_player)
            round_state.current_trick = trick
            
            # Play 4 cards
            for _ in range(4):
                hand = round_state.hands[current_player]
                is_first_trick = (trick_num == 0)
                
                legal = get_legal_moves(
                    hand,
                    trick,
                    round_state.hearts_broken,
                    is_first_trick=is_first_trick
                )
                
                if not legal:
                    raise ValueError(f"Player {current_player} has no legal moves")
                
                # Get card from player function
                # For bot (player 0), use the function; for others, use their function
                if current_player == 0:
                    # Bot - will be handled by bot interface
                    card = self.player_functions[0](hand, self.game_state)
                else:
                    card = self.player_functions[current_player](hand, self.game_state)
                
                if card not in legal:
                    raise ValueError(f"Player {current_player} played illegal card {card}")
                
                # Play card
                trick.cards.append((current_player, card))
                round_state.hands[current_player].remove(card)
                
                # Check if hearts broken
                if card.suit == 3:  # Suit.HEARTS
                    round_state.hearts_broken = True
                
                # Move to next player
                current_player = (current_player + 1) % 4
            
            # Resolve trick
            winner, _ = resolve_trick(trick)
            round_state.tricks_taken.append(trick)
            current_player = winner
        
        # Calculate scores
        scores = calculate_round_score(round_state.tricks_taken)
        return scores
    
    def play_game(self) -> dict[int, int]:
        """Play full game until someone reaches 100+ points."""
        while all(score < 100 for score in self.game_state.scores):
            round_scores = self.play_round()
            
            # Update cumulative scores
            for player_id, points in round_scores.items():
                self.game_state.scores[player_id] += points
            
            self.game_state.round_number += 1
            self.game_state.pass_direction = self.game_state.get_pass_direction()
        
        return self.game_state.scores


def random_player(hand: set, game_state: GameState) -> Card:
    """Simple random player for testing."""
    from hearts_bot.core.rules import get_legal_moves
    from hearts_bot.core.game_state import Trick
    
    legal = get_legal_moves(
        hand,
        Trick(),
        game_state.round.hearts_broken,
        is_first_trick=(len(game_state.round.tricks_taken) == 0 and not game_state.round.current_trick.cards)
    )
    
    if not legal:
        # Fallback: play any card
        legal = list(hand)
    
    return random.choice(legal)
