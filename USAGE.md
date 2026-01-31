# Hearts Bot Usage Guide

## Quick Start

### Running Tests

```bash
# From the project root directory
python3 -m pytest hearts_bot/tests/ -v
```

### Basic Usage

```python
from hearts_bot.bot import HeartsBot
from hearts_bot.core.game_state import GameState, RoundState

# Create a bot
bot = HeartsBot(seed=42, n_samples=1000)

# Initialize with your hand after passing
bot.initialize_beliefs(your_hand, passed_cards={player_id: cards_passed_to_them})

# When it's your turn to play
card = bot.play_card(game_state)

# Update beliefs after observing plays
bot.observe_card_played(player_id, card)
bot.observe_trick_complete(trick)
```

## Detailed Examples

See `example_usage.py` for complete examples:

```bash
python3 example_usage.py
```

## API Reference

### HeartsBot Class

#### Initialization

```python
bot = HeartsBot(seed=42, n_samples=1000)
```

- `seed`: Random seed for reproducibility
- `n_samples`: Number of Monte Carlo samples per decision (more = better but slower)

#### Methods

**`pass_cards(hand, direction)`**
- Returns 3 cards to pass
- `direction`: 'left', 'right', 'across', or 'hold'

**`initialize_beliefs(hand, passed_cards)`**
- Initialize belief state after receiving hand
- `hand`: Your current hand (set of Cards)
- `passed_cards`: Dict mapping player_id -> set of cards you passed to them

**`play_card(game_state)`**
- Main decision function
- Returns the Card to play
- Uses Monte Carlo sampling with belief tracking

**`observe_card_played(player, card)`**
- Update beliefs when a card is played

**`observe_trick_complete(trick)`**
- Update beliefs when a trick completes (infers voids)

## Integration with Game Runner

The bot can be integrated with `game_runner.py`:

```python
from hearts_bot.game_runner import HeartsGame
from hearts_bot.bot import HeartsBot

bot = HeartsBot(seed=42, n_samples=500)

def bot_player(hand, game_state):
    # Initialize on first call
    if not hasattr(bot_player, 'initialized'):
        bot.initialize_beliefs(hand, {})
        bot_player.initialized = True
    
    return bot.play_card(game_state)

# Create game
player_functions = [bot_player, random_player, random_player, random_player]
game = HeartsGame(player_functions, rng=random.Random(42))

# Play a round
scores = game.play_round()
```

## Performance Tuning

- **Fast mode**: `n_samples=100-200` (faster decisions, less optimal)
- **Balanced**: `n_samples=500-1000` (good balance)
- **Optimal**: `n_samples=2000+` (slower but more accurate)

## Testing

Run all tests:
```bash
python3 -m pytest hearts_bot/tests/ -v
```

Run specific test file:
```bash
python3 -m pytest hearts_bot/tests/test_rules.py -v
```

Run custom test suite:
```bash
python3 run_tests.py
```
