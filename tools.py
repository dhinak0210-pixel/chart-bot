import ast
import operator
import datetime
import requests
import urllib.parse
import random

# Safe AST Math Calculator
def calculate(expression: str) -> str:
    """Safely evaluates a mathematical expression containing numbers and basic operators.
    Supported operators: +, -, *, /, **, %, ( )
    """
    # Define allowed operators
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def eval_node(node):
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
        elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
            return node.n
        elif isinstance(node, ast.Constant):  # Python >= 3.8
            if isinstance(node.value, (int, float)):
                return node.value
            raise TypeError(f"Unsupported constant type: {type(node.value)}")
        elif isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            op_type = type(node.op)
            if op_type in operators:
                # Prevent division by zero
                if op_type in (ast.Div, ast.Mod) and right == 0:
                    raise ZeroDivisionError("Division or modulo by zero is not allowed.")
                # Prevent extremely large exponents to avoid CPU hang
                if op_type == ast.Pow and (abs(left) > 1000 or abs(right) > 1000):
                    raise ValueError("Exponents or bases too large to prevent overflow.")
                return operators[op_type](left, right)
            raise TypeError(f"Unsupported binary operator: {op_type}")
        elif isinstance(node, ast.UnaryOp):
            operand = eval_node(node.operand)
            op_type = type(node.op)
            if op_type in operators:
                return operators[op_type](operand)
            raise TypeError(f"Unsupported unary operator: {op_type}")
        else:
            raise TypeError(f"Unsupported syntax node: {type(node)}")

    # Clean expression and evaluate
    expression = expression.strip()
    try:
        tree = ast.parse(expression, mode='eval')
        result = eval_node(tree)
        return f"Result of '{expression}': {result}"
    except ZeroDivisionError as e:
        return f"Error: {str(e)}"
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error evaluating expression '{expression}': {str(e)}. Make sure you only use numbers and math operators (+, -, *, /, **, %)."

# Time retrieval tool
def get_time() -> str:
    """Returns the current date and time."""
    now = datetime.datetime.now()
    return f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')} (timezone-agnostic local time)"

# Wikipedia API retrieval tool
def search_wikipedia(query: str) -> str:
    """Searches Wikipedia and returns a summary for the given query using the free REST API."""
    if not query or not query.strip():
        return "Error: Wikipedia search query cannot be empty."
    
    # Format query for Wikipedia API (replace spaces with underscores and URL encode)
    formatted_query = urllib.parse.quote(query.strip().replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_query}"
    
    headers = {
        "User-Agent": "AgenticAIChatbot/1.0 (contact: support@chatbot.local; personal educational bot)"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            title = data.get("title", query)
            extract = data.get("extract", "")
            description = data.get("description", "")
            
            res_str = f"Wikipedia Title: {title}\n"
            if description:
                res_str += f"Description: {description}\n"
            res_str += f"Summary: {extract}"
            return res_str
        elif response.status_code == 404:
            return f"Wikipedia page not found for '{query}'. Try searching for a broader or alternate term."
        else:
            return f"Error connecting to Wikipedia (Status code: {response.status_code})."
    except requests.exceptions.RequestException as e:
        return f"Network error when trying to search Wikipedia: {str(e)}"

# Mock Weather Tool
def get_weather(city: str) -> str:
    """Simulates real-time weather information for a given city."""
    if not city or not city.strip():
        return "Error: City name cannot be empty."
    
    city = city.strip().title()
    
    # Mock data store for major cities
    mock_weather_db = {
        "New York": {"temp": 22, "condition": "Partly Cloudy", "humidity": 60, "wind": 15},
        "London": {"temp": 15, "condition": "Light Rain", "humidity": 85, "wind": 22},
        "Tokyo": {"temp": 26, "condition": "Sunny", "humidity": 50, "wind": 10},
        "Paris": {"temp": 18, "condition": "Overcast", "humidity": 70, "wind": 12},
        "Sydney": {"temp": 16, "condition": "Windy", "humidity": 55, "wind": 30},
        "Mumbai": {"temp": 31, "condition": "Humid and Sunny", "humidity": 80, "wind": 8},
        "Cairo": {"temp": 35, "condition": "Hot and Sunny", "humidity": 25, "wind": 14},
        "Moscow": {"temp": 8, "condition": "Chilly and Cloudy", "humidity": 75, "wind": 18},
        "Toronto": {"temp": 20, "condition": "Clear Sky", "humidity": 50, "wind": 9},
        "Berlin": {"temp": 17, "condition": "Mild Breeze", "humidity": 65, "wind": 14},
        "Singapore": {"temp": 32, "condition": "Thundershowers", "humidity": 85, "wind": 11},
        "Cape Town": {"temp": 19, "condition": "Pleasant", "humidity": 60, "wind": 16},
    }
    
    if city in mock_weather_db:
        w = mock_weather_db[city]
        return f"Weather in {city}: {w['temp']}°C, Condition: {w['condition']}, Humidity: {w['humidity']}%, Wind Speed: {w['wind']} km/h."
    
    # Generate random weather for other cities deterministically using city name seed
    random.seed(city)
    temp = random.randint(5, 38)
    condition = random.choice(["Sunny", "Partly Cloudy", "Cloudy", "Overcast", "Rainy", "Windy", "Foggy"])
    humidity = random.randint(30, 95)
    wind = random.randint(5, 35)
    
    return f"Weather in {city} (Simulated): {temp}°C, Condition: {condition}, Humidity: {humidity}%, Wind Speed: {wind} km/h."

def plot_chart(chart_type: str, data: dict, x_label: str, y_label: str) -> str:
    """Plots a chart (line, bar, or area) using Streamlit.
    - chart_type: 'line', 'bar', or 'area'
    - data: A dictionary containing the columns and values (e.g. {"Category": ["A", "B"], "Value": [10, 20]})
    - x_label: The column name to use for the X-axis
    - y_label: The column name to use for the Y-axis
    """
    import streamlit as st
    st.session_state.active_chart = {
        "chart_type": chart_type.lower(),
        "data": data,
        "x_label": x_label,
        "y_label": y_label
    }
    return f"Success: Rendered {chart_type} chart with X-axis '{x_label}' and Y-axis '{y_label}'."

# Exported tools registry
TOOLS = {
    "calculate": calculate,
    "get_time": get_time,
    "search_wikipedia": search_wikipedia,
    "get_weather": get_weather,
    "plot_chart": plot_chart
}
