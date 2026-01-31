# Hearts Bot - Monte Carlo with Belief Tracking

An optimal-play Hearts bot using Monte Carlo sampling over inferred opponent hand distributions. The bot tracks all cards played, maintains probability distributions over opponent holdings, samples consistent "worlds," and simulates games to completion to select moves that minimize expected points.

## Features

- **Belief Tracking**: Maintains probability distributions over opponent hands
- **Monte Carlo Sampling**: Samples consistent worlds and simulates to completion
- **Heuristic Overrides**: Fast path for obvious moves
- **Full Rules Implementation**: Complete Hearts rules including shoot-the-moon

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from hearts_bot.bot import HeartsBot
from hearts_bot.game_runner import HeartsGame

# Create bot
bot = HeartsBot(seed=42, n_samples=1000)

# Initialize with hand and passed cards
bot.initialize_beliefs(hand, passed_cards)

# Play card
card = bot.play_card(game_state)

# Update beliefs after observations
bot.observe_card_played(player, card)
bot.observe_trick_complete(trick)
```

## Project Structure

```
hearts_bot/
├── core/           # Core game components (cards, rules, game state)
├── inference/      # Belief tracking and sampling
├── engine/         # Simulation and MCTS
├── bot.py          # Top-level bot interface
├── game_runner.py  # Game execution framework
└── tests/          # Test suite
```

## Testing

```bash
pytest hearts_bot/tests/
```

## Performance Targets

- Decision time: <500ms with 1000 samples
- Sample generation: <0.1ms per world
- Full game simulation: <5ms per game
