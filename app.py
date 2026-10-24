from flask import Flask, render_template, request, jsonify
import ast
import math
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "calculator_history.db"

# Only these names and operations are permitted in expressions.
def _root(value, degree):
    if degree == 0:
        raise ValueError("Root degree cannot be zero.")
    if value < 0:
        is_integer_degree = isinstance(degree, int) or degree.is_integer()
        if not is_integer_degree or int(degree) % 2 == 0:
            raise ValueError("Even roots of negative numbers are not real.")
        return -((-value) ** (1 / degree))
    return value ** (1 / degree)


FUNCTIONS = {
    "sqrt": (math.sqrt, 1), "cbrt": (lambda value: math.copysign(abs(value) ** (1 / 3), value), 1),
    "root": (_root, 2), "sin": (math.sin, 1), "cos": (math.cos, 1),
    "tan": (math.tan, 1), "asin": (math.asin, 1), "acos": (math.acos, 1),
    "atan": (math.atan, 1), "sinh": (math.sinh, 1), "cosh": (math.cosh, 1),
    "tanh": (math.tanh, 1), "asinh": (math.asinh, 1), "acosh": (math.acosh, 1),
    "atanh": (math.atanh, 1), "log": (math.log10, 1), "log2": (math.log2, 1),
    "logbase": (math.log, 2), "ln": (math.log, 1), "log1p": (math.log1p, 1),
    "abs": (abs, 1), "floor": (math.floor, 1), "ceil": (math.ceil, 1),
    "round": (round, 1), "exp": (math.exp, 1), "expm1": (math.expm1, 1),
    "factorial": (math.factorial, 1), "comb": (math.comb, 2),
    "perm": (math.perm, 2), "gcd": (math.gcd, 2), "lcm": (math.lcm, 2),
    "hypot": (math.hypot, 2), "degrees": (math.degrees, 1),
    "radians": (math.radians, 1), "percent": (lambda value: value / 100, 1),
}
CONSTANTS = {
    "pi": math.pi, "e": math.e, "tau": math.tau, "phi": (1 + math.sqrt(5)) / 2,
    "sqrt2": math.sqrt(2), "ln2": math.log(2), "ln10": math.log(10),
}
BINARY_OPERATORS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a ** b,
    ast.Mod: lambda a, b: a % b,
}
UNARY_OPERATORS = {ast.UAdd: lambda a: +a, ast.USub: lambda a: -a}


def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expression TEXT NOT NULL,
                    result TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)


def safe_eval(expression, angle_unit="radians"):
    """Evaluate a restricted mathematical expression without eval()."""
    if angle_unit not in {"radians", "degrees"}:
        raise ValueError("Unsupported angle unit.")
    # Permit calculator-style symbols while still parsing only a Python AST.
    expression = expression.replace("^", "**").replace("×", "*").replace("÷", "/")
    tree = ast.parse(expression, mode="eval")

    def trig(function):
        def apply(value):
            if angle_unit == "degrees":
                value = math.radians(value)
            return function(value)
        return apply

    def inverse_trig(function):
        def apply(value):
            result = function(value)
            return math.degrees(result) if angle_unit == "degrees" else result
        return apply

    functions = FUNCTIONS.copy()
    for name in ("sin", "cos", "tan"):
        function, arity = functions[name]
        functions[name] = (trig(function), arity)
    for name in ("asin", "acos", "atan"):
        function, arity = functions[name]
        functions[name] = (inverse_trig(function), arity)

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in CONSTANTS:
                return CONSTANTS[node.id]
            raise ValueError(f"Unknown name: {node.id}")
        if isinstance(node, ast.BinOp) and type(node.op) in BINARY_OPERATORS:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 1000:
                raise ValueError("Exponent is too large")
            value = BINARY_OPERATORS[type(node.op)](left, right)
            if isinstance(value, complex):
                raise ValueError("Complex results are not supported")
            if not math.isfinite(value):
                raise ValueError("Result is outside the supported range")
            return value
        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPERATORS:
            return UNARY_OPERATORS[type(node.op)](visit(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name not in functions or node.keywords:
                raise ValueError("Unsupported function or arguments")
            function, arity = functions[name]
            if len(node.args) != arity:
                raise ValueError(f"{name} expects {arity} argument(s)")
            args = [visit(arg) for arg in node.args]
            value = function(*args)
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("Result is outside the supported range")
            return value
        raise ValueError("Invalid or unsupported expression")

    result = visit(tree)
    if isinstance(result, float) and not math.isfinite(result):
        raise ValueError("Result is outside the supported range")
    return result


def format_result(value):
    if isinstance(value, float):
        if value.is_integer() and abs(value) < 1e16:
            return str(int(value))
        return f"{value:.12g}"
    return str(value)


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/calculate")
def calculate():
    data = request.get_json(silent=True) or {}
    expression = str(data.get("expression", "")).strip()
    mode = "scientific" if data.get("mode") == "scientific" else "standard"
    angle_unit = data.get("angle_unit", "radians")

    if not expression:
        return jsonify({"error": "Enter an expression first."}), 400
    if len(expression) > 300:
        return jsonify({"error": "Expression is too long."}), 400
    if angle_unit not in {"radians", "degrees"}:
        return jsonify({"error": "Unsupported angle unit."}), 400

    try:
        result = format_result(safe_eval(expression, angle_unit))
        history_mode = f"{mode} ({angle_unit})" if mode == "scientific" else mode
        with closing(sqlite3.connect(DB_PATH)) as conn:
            with conn:
                conn.execute(
                    "INSERT INTO history (expression, result, mode, created_at) VALUES (?, ?, ?, ?)",
                    (expression, result, history_mode, datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"))
                )
        return jsonify({"expression": expression, "result": result})
    except ZeroDivisionError:
        message = "Cannot divide by zero."
    except (ValueError, TypeError, SyntaxError, OverflowError) as exc:
        message = str(exc) or "Invalid expression."
    except Exception:
        message = "Could not calculate this expression."
    return jsonify({"error": message}), 400


@app.get("/api/history")
def history():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, expression, result, mode, created_at FROM history ORDER BY id DESC LIMIT 100"
            ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.delete("/api/history")
def clear_history():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.execute("DELETE FROM history")
    return jsonify({"ok": True})


init_db()

if __name__ == "__main__":
    # Local-only server; no external network access is needed.
    app.run(host="127.0.0.1", port=5000, debug=False)
