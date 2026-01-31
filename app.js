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
        document.getElementById('loading').innerHTML = 
            `<p style="color: red;">Error loading bot: ${error.message}</p>`;
    }
}

// Load bot code from files
async function loadBotCode() {
    // Set up Python path
    pyodide.runPython(`
import sys
sys.path.insert(0, '.')
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

    // Load each file and execute it
    for (const file of files) {
        try {
            const response = await fetch(file);
            if (!response.ok) {
                // __init__.py files might be empty, that's OK
                if (file.includes('__init__.py')) {
                    console.log(`Skipping empty ${file}`);
                    continue;
                }
                throw new Error(`Failed to load ${file}: ${response.status}`);
            }
            const code = await response.text();
            
            // Skip empty files
            if (code.trim().length === 0) {
                console.log(`Skipping empty ${file}`);
                continue;
            }
            
            // Execute the code
            pyodide.runPython(code);
            console.log(`Loaded ${file}`);
        } catch (error) {
            // __init__.py files are optional
            if (file.includes('__init__.py')) {
                console.log(`Skipping ${file}: ${error.message}`);
                continue;
            }
            console.error(`Error loading ${file}:`, error);
            throw new Error(`Failed to load bot code: ${error.message}`);
        }
    }

    // Import the bridge module
    try {
        botModule = pyodide.pyimport('bot_bridge');
        console.log('Bot module loaded successfully');
    } catch (error) {
        console.error('Error importing bot_bridge:', error);
        throw new Error(`Failed to import bot bridge: ${error.message}`);
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
        showError(`Error: ${error.message}`);
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
