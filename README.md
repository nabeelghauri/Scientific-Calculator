# SmartCalc — Standard + Scientific Calculator

A responsive browser-based calculator with a Python backend, HTML/CSS/JavaScript frontend, a Java launcher, and persistent calculation history.

## Features
- Switch between standard and scientific calculator modes with one click.
- Basic arithmetic: addition, subtraction, multiplication, division, percentages, powers and parentheses.
- Scientific functions: circular and hyperbolic trig (and their inverses), powers and arbitrary roots, logarithms, exponential functions, factorial, combinations, permutations, gcd/lcm, rounding, percent conversion, and angle conversion.
- Radian or degree mode for circular and inverse trigonometric functions.
- Constants: `pi`, `e`, `tau`, `phi`, `sqrt2`, `ln2` and `ln10`.
- Calculation history stored in a local SQLite database, retained after restarting the app.
- Click a history item to restore its expression; clear history when needed.
- Keyboard input, Enter to calculate, Backspace to edit, and Esc to clear.
- Responsive dark UI for desktop and mobile.

## Requirements
- Python 3.9 or newer
- Java 11 or newer (only needed to use the launcher)
- A modern web browser

## Run on Windows
1. Extract the project folder.
2. Open Command Prompt or a terminal in this folder.
3. Install the Python dependency:
   ```bash
   python -m pip install -r requirements.txt
   ```
4. Compile the Java launcher:
   ```bash
   javac CalculatorLauncher.java
   ```
5. Start the app:
   ```bash
   java CalculatorLauncher
   ```
6. Your browser should open `http://127.0.0.1:5000`. Keep the terminal open while using the app.

### Run without Java
```bash
python app.py
```
Then open `http://127.0.0.1:5000` manually.

## How the parts connect
The Java file is a launcher: it starts the Python Flask server and opens the browser. Flask serves `templates/index.html` and `static/style.css` / `static/app.js`. The frontend sends calculations and history requests to Python over local HTTP. Python validates and evaluates expressions and stores history in `calculator_history.db`.

## Notes
- Trigonometric functions use radians by default; select DEG in scientific mode to use degrees. Hyperbolic functions always use their standard dimensionless input.
- Scientific function expressions are validated by the backend rather than evaluated with Python's unrestricted `eval()`. Multi-argument functions use commas, for example `root(27,3)`, `logbase(8,2)`, or `comb(5,2)`.
- The `mod` key performs modulo. For percentage conversion, use `percent(25)` to get `0.25`.
- The server binds to `127.0.0.1`, so it is intended for local use on your own computer.
