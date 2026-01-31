let pyodide;
let botModule;

// Card mapping
const SUIT_MAP = {
    '♣': 0, // CLUBS
    '♦': 1, // DIAMONDS
    '♠': 2, // SPADES
    '♥': 3  // HEARTS
};

const RANK_MAP = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
};

const SUIT_SYMBOLS = ['♣', '♦', '♠', '♥'];
const RANK_SYMBOLS = {
    2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
    10: '10', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'
};

// Initialize Pyodide
async function initPyodide() {
    try {
        pyodide = await loadPyodide();
        console.log('Pyodide loaded');

        // Load numpy (required dependency)
        await pyodide.loadPackage('numpy');
        console.log('NumPy loaded');

        // Load the bot code
        await loadBotCode();
        console.log('Bot code loaded');

        // Hide loading, show app
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('app').classList.remove('hidden');
    } catch (error) {
        console.error('Error initializing Pyodide:', error);
        showFallbackError(error);
    }
}

// Show fallback error with helpful message
function showFallbackError(error) {
    const loadingEl = document.getElementById('loading');
    loadingEl.innerHTML = `
        <div style="padding: 40px; text-align: center;">
            <h2 style="color: #dc3545; margin-bottom: 20px;">⚠️ Bot Engine Failed to Load</h2>
            <div style="background: #f8d7da; color: #721c24; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: left;">
                <p><strong>Error:</strong> ${error.message}</p>
                <p style="margin-top: 10px; font-size: 0.9em;">
                    This usually happens due to network issues or browser compatibility. 
                    Please try:
                </p>
                <ul style="margin-top: 10px; padding-left: 20px;">
                    <li>Refreshing the page</li>
                    <li>Checking your internet connection</li>
                    <li>Using a modern browser (Chrome, Firefox, Safari, Edge)</li>
                    <li>Clearing your browser cache</li>
                </ul>
            </div>
            <button onclick="location.reload()" style="
                padding: 12px 24px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 1em;
                cursor: pointer;
                margin-top: 20px;
            ">Retry</button>
            <p style="margin-top: 30px; color: #6c757d; font-size: 0.9em;">
                If the problem persists, check the browser console (F12) for more details.
            </p>
        </div>
    `;
}

// Load bot code from files
async function loadBotCode() {
    // Set up Python path and create package structure
    pyodide.runPython(`
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

# Create package directories in Pyodide's filesystem
os.makedirs('hearts_bot/core', exist_ok=True)
os.makedirs('hearts_bot/inference', exist_ok=True)
os.makedirs('hearts_bot/engine', exist_ok=True)
    `);

    // List of Python files to load in order (with __init__ files first)
    const files = [
        'hearts_bot/__init__.py',
        'hearts_bot/core/__init__.py',
        'hearts_bot/core/cards.py',
        'hearts_bot/core/game_state.py',
        'hearts_bot/core/rules.py',
        'hearts_bot/inference/__init__.py',
        'hearts_bot/inference/beliefs.py',
        'hearts_bot/inference/sampler.py',
        'hearts_bot/inference/updater.py',
        'hearts_bot/engine/__init__.py',
        'hearts_bot/engine/heuristics.py',
        'hearts_bot/engine/simulator.py',
        'hearts_bot/engine/mcts.py',
        'hearts_bot/bot.py',
        'bot_bridge.py'
    ];

    // Load each file and write it to Pyodide's filesystem, then import
    for (const file of files) {
        try {
            const response = await fetch(file);
            if (!response.ok) {
                // __init__.py files might be empty, that's OK
                if (file.includes('__init__.py')) {
                    console.log(`Skipping empty ${file}`);
                    // Create empty __init__.py file
                    pyodide.FS.writeFile(file, '', { encoding: 'utf8' });
                    continue;
                }
                throw new Error(`Failed to load ${file}: ${response.status}`);
            }
            const code = await response.text();
            
            // Skip empty files but create them
            if (code.trim().length === 0) {
                console.log(`Creating empty ${file}`);
                pyodide.FS.writeFile(file, '', { encoding: 'utf8' });
                continue;
            }
            
            // Write file to Pyodide's filesystem
            pyodide.FS.writeFile(file, code, { encoding: 'utf8' });
            console.log(`Wrote ${file}`);
        } catch (error) {
            // __init__.py files are optional
            if (file.includes('__init__.py')) {
                console.log(`Creating empty ${file}: ${error.message}`);
                try {
                    pyodide.FS.writeFile(file, '', { encoding: 'utf8' });
                } catch (e) {
                    // Ignore if we can't create it
                }
                continue;
            }
            console.error(`Error loading ${file}:`, error);
            throw new Error(`Failed to load bot code: ${error.message}`);
        }
    }

    // Now import modules - files are in Pyodide's filesystem
    // We need to import in the right order to handle relative imports
    try {
        // Import packages in order to establish package structure
        pyodide.runPython(`
# Import packages to establish structure
import hearts_bot
import hearts_bot.core
import hearts_bot.inference
import hearts_bot.engine

# Now import modules (this will handle relative imports correctly)
import hearts_bot.core.cards
import hearts_bot.core.game_state
import hearts_bot.core.rules
import hearts_bot.inference.beliefs
import hearts_bot.inference.sampler
import hearts_bot.inference.updater
import hearts_bot.engine.heuristics
import hearts_bot.engine.simulator
import hearts_bot.engine.mcts
import hearts_bot.bot

# Finally import the bridge
import bot_bridge
        `);
        
        botModule = pyodide.pyimport('bot_bridge');
        console.log('Bot module loaded successfully');
    } catch (error) {
        console.error('Error importing modules:', error);
        // Try fallback: check if files exist and provide helpful error
        try {
            const filesExist = pyodide.runPython(`
import os
files_to_check = [
    'hearts_bot/__init__.py',
    'hearts_bot/core/cards.py',
    'hearts_bot/bot.py',
    'bot_bridge.py'
]
missing = [f for f in files_to_check if not os.path.exists(f)]
missing
            `);
            const missing = filesExist.toJs();
            if (missing.length > 0) {
                throw new Error(`Missing required files: ${missing.join(', ')}. Please ensure all bot files are accessible.`);
            }
        } catch (checkError) {
            console.error('File check failed:', checkError);
        }
        throw new Error(`Failed to import bot modules: ${error.message}. Check browser console for details.`);
    }
}
}

// State management
let hand = [];
let trick = [];

// Initialize UI
function initUI() {
    // Hand management
    document.getElementById('add-card-btn').addEventListener('click', addCardToHand);
    document.getElementById('clear-hand-btn').addEventListener('click', clearHand);
    document.getElementById('get-move-btn').addEventListener('click', getBestMove);
    
    // Trick management
    document.getElementById('add-trick-card-btn').addEventListener('click', addCardToTrick);
    document.getElementById('clear-trick-btn').addEventListener('click', clearTrick);
    
    // Allow Enter key in selects
    document.getElementById('rank-select').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addCardToHand();
    });
}

function addCardToHand() {
    const rank = document.getElementById('rank-select').value;
    const suit = document.getElementById('suit-select').value;
    
    const card = { rank, suit };
    
    // Check if card already exists
    if (hand.some(c => c.rank === rank && c.suit === suit)) {
        showError('Card already in hand!');
        return;
    }
    
    if (hand.length >= 13) {
        showError('Hand is full (13 cards max)!');
        return;
    }
    
    hand.push(card);
    updateHandDisplay();
}

// Make removeCardFromHand globally accessible
window.removeCardFromHand = function(index) {
    hand.splice(index, 1);
    updateHandDisplay();
};

function clearHand() {
    hand = [];
    updateHandDisplay();
}

function updateHandDisplay() {
    const display = document.getElementById('hand-display');
    display.innerHTML = '';
    
    hand.forEach((card, index) => {
        const cardEl = document.createElement('div');
        cardEl.className = `card ${getSuitClass(card.suit)}`;
        cardEl.textContent = `${card.rank}${card.suit}`;
        cardEl.textContent = `${card.rank}${card.suit}`;
        const removeBtn = document.createElement('span');
        removeBtn.className = 'remove';
        removeBtn.textContent = '×';
        removeBtn.onclick = () => window.removeCardFromHand(index);
        cardEl.appendChild(removeBtn);
        display.appendChild(cardEl);
    });
    
    if (hand.length === 0) {
        display.innerHTML = '<p style="color: #6c757d; text-align: center; width: 100%;">No cards in hand</p>';
    }
}

function addCardToTrick() {
    const rank = document.getElementById('trick-rank-select').value;
    const suit = document.getElementById('trick-suit-select').value;
    const player = parseInt(document.getElementById('trick-player-select').value);
    
    trick.push({ player, rank, suit });
    updateTrickDisplay();
}

function clearTrick() {
    trick = [];
    updateTrickDisplay();
}

function updateTrickDisplay() {
    const display = document.getElementById('trick-display');
    display.innerHTML = '';
    
    if (trick.length === 0) {
        display.innerHTML = '<p style="color: #6c757d; text-align: center; width: 100%;">No cards in trick</p>';
        return;
    }
    
    trick.forEach((card) => {
        const cardEl = document.createElement('div');
        cardEl.className = `trick-card ${getSuitClass(card.suit)}`;
        cardEl.innerHTML = `
            ${card.rank}${card.suit}
            <span class="player-label">P${card.player}</span>
        `;
        display.appendChild(cardEl);
    });
}

function getSuitClass(suit) {
    if (suit === '♣' || suit === '♠') return 'clubs';
    if (suit === '♦' || suit === '♥') return 'diamonds';
    return '';
}

async function getBestMove() {
    // Validate bot is loaded
    if (!botModule) {
        showError('Bot engine not loaded. Please refresh the page and try again.');
        return;
    }
    
    // Validate
    if (hand.length === 0) {
        showError('Please add cards to your hand!');
        return;
    }
    
    // Hide previous results
    document.getElementById('result').classList.add('hidden');
    document.getElementById('error').classList.add('hidden');
    
    // Show loading
    const btn = document.getElementById('get-move-btn');
    const originalText = btn.textContent;
    btn.textContent = 'Calculating...';
    btn.disabled = true;
    
    try {
        const heartsBroken = document.getElementById('hearts-broken').checked;
        const isFirstTrick = document.getElementById('is-first-trick').checked;
        const nSamples = parseInt(document.getElementById('n-samples').value);
        
        // Validate n_samples
        if (isNaN(nSamples) || nSamples < 100 || nSamples > 2000) {
            throw new Error('Number of samples must be between 100 and 2000');
        }
        
        // Convert hand to Python format
        const handCards = hand.map(card => [
            RANK_MAP[card.rank],
            SUIT_MAP[card.suit]
        ]);
        
        // Convert trick to Python format
        const trickCards = trick.map(card => [
            card.player,
            RANK_MAP[card.rank],
            SUIT_MAP[card.suit]
        ]);
        
        // Create bot
        const bot = botModule.create_bot(null, nSamples);
        
        // Get best move
        const result = botModule.get_best_move(
            bot,
            handCards,
            heartsBroken,
            isFirstTrick,
            trickCards,
            nSamples
        );
        
        // Display result - handle both tuple and list returns
        let rank, suit;
        if (result && typeof result.toJs === 'function') {
            [rank, suit] = result.toJs();
        } else if (Array.isArray(result)) {
            [rank, suit] = result;
        } else {
            throw new Error('Unexpected result format from bot');
        }
        const rankStr = RANK_SYMBOLS[rank];
        const suitStr = SUIT_SYMBOLS[suit];
        
        document.getElementById('result-card').textContent = `${rankStr}${suitStr}`;
        document.getElementById('result-details').textContent = 
            `Recommended: ${rankStr}${suitStr} (${nSamples} samples)`;
        document.getElementById('result').classList.remove('hidden');
        
    } catch (error) {
        console.error('Error getting best move:', error);
        const errorMsg = error.message || 'An unknown error occurred';
        showError(`Error calculating best move: ${errorMsg}. Please check your input and try again.`);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

function showError(message) {
    const errorEl = document.getElementById('error');
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
    setTimeout(() => {
        errorEl.classList.add('hidden');
    }, 5000);
}

// Start initialization
initPyodide();
initUI();
