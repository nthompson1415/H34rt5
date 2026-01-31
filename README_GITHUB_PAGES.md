# Hearts Bot - GitHub Pages Frontend

This directory contains a web-based frontend for the Hearts bot that runs entirely in the browser using Pyodide.

## Setup for GitHub Pages

1. **Enable GitHub Pages**:
   - Go to your repository Settings → Pages
   - Select source branch (usually `main` or `gh-pages`)
   - Select folder (usually `/ (root)`)

2. **File Structure**:
   The following files need to be in the root directory for GitHub Pages:
   - `index.html` - Main HTML file
   - `style.css` - Styling
   - `app.js` - JavaScript application
   - `bot_bridge.py` - Python bridge module
   - `hearts_bot/` - All Python bot code (entire directory)

3. **Access**:
   Once enabled, your site will be available at:
   `https://<username>.github.io/<repository-name>/`

## Usage

1. Open `index.html` in a browser (or visit your GitHub Pages URL)
2. Add cards to your hand using the card selector
3. Configure game state:
   - Check "Hearts Broken" if hearts have been played
   - Check "First Trick" if this is the first trick
   - Add cards to the current trick if any have been played
4. Adjust Monte Carlo samples (100-2000, more = better but slower)
5. Click "Get Best Move" to get the bot's recommendation

## How It Works

The frontend uses [Pyodide](https://pyodide.org/) to run Python code directly in the browser:

1. Pyodide loads and executes all Python bot files
2. JavaScript provides a bridge to call Python functions
3. The bot performs Monte Carlo simulations to find the best move
4. Results are displayed in the UI

## Notes

- First load may take 10-20 seconds as Pyodide downloads and initializes
- The bot requires NumPy, which is automatically loaded by Pyodide
- All computation happens client-side (no server needed)
- Works offline after initial load (if cached)

## Troubleshooting

If the bot doesn't load:
- Check browser console for errors
- Ensure all Python files are accessible
- Verify Pyodide CDN is accessible
- Try clearing browser cache
