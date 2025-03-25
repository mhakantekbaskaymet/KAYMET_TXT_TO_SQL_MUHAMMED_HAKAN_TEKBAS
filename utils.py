import sqlite3
import re
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()


client = OpenAI()

def generate_sql_query(natural_language_query: str) -> str:
    """
    Generate SQL query from natural language using GPT-4.

    Args:
        natural_language_query: Natural language query string
        
    Returns:
        str: Generated SQL query string

    Raises:
        openai.APIError: If there's an error communicating with the OpenAI API
        openai.RateLimitError: If rate limit is exceeded
        openai.APIConnectionError: If there's a network error
    """
    schema_details = """You are a highly skilled SQL query generator specialized in SQLite. The database 'data.db' has the following schema:
    1. Products:
    - ProductID
    - Name (Name of product)
    - Category1 (Men, Women, Kids)
    - Category2 (Sandals, Casual Shoes, Boots, Sports Shoes)
    2. Transactions:
    - StoreID
    - ProductID
    - Quantity
    - PricePerQuantity
    - Timestamp (Year, Month, Day hour:minute:second)
    3. Stores:
    - StoreID
    - State (two-letter code, e.g., NY, IL, TX)
    - ZipCode"""

    system_prompt = (
    "You are **FashionAI**, an intelligent assistant designed for a fashion company. "
    "Your primary role is to understand user queries and generate **only** read-only SQL queries. "
    "You must always maintain a professional tone and provide accurate responses."
    "\n\n"
    "### **FashionAI Personality & Behavior:**\n"
    "- You are an AI assistant specializing in **fashion-related data**.\n"
    "- You must always answer in the same language the user asked.\n"
    "- If asked 'Who are you?' respond in the user's language: \n"
    "  - Example (English): 'I am FashionAI, the AI assistant for a fashion company. How can I help you?'\n"
    "  - Example (Turkish): 'Ben FashionAI, bir moda şirketi için yapay zeka asistanıyım. Size nasıl yardımcı olabilirim?'\n\n"
    
    "### **SQL Generation Rules:**\n"
    "1. You **must** generate only **read-only SQL queries** (SELECT, WITH, EXPLAIN).\n"
    "2. **DO NOT** generate queries that modify the database (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, etc.).\n"
    "3. If the user's request involves a modification operation, **DO NOT** generate SQL. Instead, politely respond in the user's language: \n"
    "   - Example (English): 'I don't have access to perform write operations. I can only generate read-only queries.'\n"
    "   - Example (Turkish): 'Yazma işlemleri yapma yetkim yok. Sadece salt okunur sorgular üretebilirim.'\n\n"
    "4. When the user requests a specific product name, **use only the exact name provided** and **DO NOT** retrieve similar products. \n"
    "   - **DO NOT** use 'LIKE' operators or any partial matching techniques.\n"
    "   - Ensure that the query strictly filters based on the exact product name given by the user.\n\n"

    "### **Strict Rule: Plain Text SQL Output (No Markup Formatting)**\n"
    "- **Return the SQL query as plain text ONLY**.\n"
    "- **DO NOT** format the output using markdown, SQL tags, triple backticks (` ```sql `) or any other code block formatting.\n"
    "- **DO NOT** include explanations, extra text, or any unnecessary characters in the SQL output.\n"
    "- The output **MUST** be a clean SQL query that can be executed directly without additional processing.\n"
    "- If you return an explanation, keep each output part clearly separated from the SQL output.\n\n"
    
    "### **Response Language Adaptation:**\n"
    "- Automatically detect the user's language and respond in the same language.\n"
    "- Ensure the SQL code remains in **standard SQL syntax**, while the explanation or messages are translated accordingly.\n\n"

    f"{schema_details}\n"
    "Now, based on the schema above, convert the following natural language query into a valid, efficient read-only SQL query. "
    "**Return only the SQL code as plain text, nothing else.**"
)

    user_prompt =(  f"Natural language query: '{natural_language_query}'")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}]
            ,
        temperature=0,
    )
    
    return response.choices[0].message.content.strip() # type: ignore

def execute_sql_query(sql: str) -> list[dict[str, str]]:
    """
    Execute SQL query against SQLite database (read-only queries only).
    
    Args:
        sql: SQL query to execute
        
    Returns:
        list[dict[str, str]]: List of dictionaries where each dictionary represents a row
            with column names as keys and cell values as values
        
    Raises:
        ValueError: If the SQL query is not read-only (must start with SELECT, WITH, or EXPLAIN)
        sqlite3.OperationalError: If there's a syntax error in the SQL query
        sqlite3.Error: If there's any other database-related error
    """
    sql_lower = sql.strip().lower()
    if not (sql_lower.startswith("select") or sql_lower.startswith("with") or sql_lower.startswith("explain")):
        raise ValueError("Only read-only queries are allowed.")
    
    try:
        conn = sqlite3.connect("data.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(sql)
        rows = cursor.fetchall()

        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]

        return results
    finally:
        conn.close()


def initialize_session_db():
    """Initialize the SQLite database and create table if not exists."""
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_request TEXT NOT NULL,
            ai_response TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def save_to_session(session_id: str, user_request: str, ai_response: str) -> None:
    """
    Save user request and AI response to the session database.
    
    Args:
        session_id: Unique identifier for the chat session
        user_request: The message sent by the user
        ai_response: The response generated by the AI
        
    Returns:
        None
        
    Raises:
        sqlite3.IntegrityError: If there's a constraint violation
        sqlite3.Error: If there's any other database-related error
    """
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO sessions (session_id, user_request, ai_response)
        VALUES (?, ?, ?)
    """, (session_id, user_request, ai_response))
    
    conn.commit()
    conn.close()


def get_session_history(session_id: str) -> list[dict[str, str]]:
    """
    Retrieve session history by session_id.
    
    Args:
        session_id: Unique identifier for the chat session
        
    Returns:
        list[dict[str, str]]: List of conversation entries where each dictionary contains:
            - 'user': The user's message
            - 'ai': The AI's response
        
    Raises:
        sqlite3.Error: If there's any database-related error
    """
    conn = sqlite3.connect("sessions.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_request, ai_response FROM sessions
        WHERE session_id = ?
        ORDER BY id ASC
    """, (session_id,))
    
    conversation = cursor.fetchall()
    conn.close()
    
    return [{"user": row["user_request"], "ai": row["ai_response"]} for row in conversation]

def quick_check_sql(sql_query: str, db_path: str = "data.db") -> bool:
    """
    Checks whether a given SQL SELECT query contains any data.

    - Extracts everything after FROM and wraps it inside a SELECT EXISTS query.
    - Removes ORDER BY since it's unnecessary for EXISTS.
    - Automatically supports WHERE, JOIN, GROUP BY, HAVING, and other SQL structures.

    Args:
        sql_query (str): The SQL SELECT query to check.
        db_path (str): Path to the database file. Default is "data.db".

    Returns:
        bool: Returns True if data exists, otherwise False.
    """
        
    # Remove ORDER BY (not needed for EXISTS)
    sql_query = re.sub(r"ORDER BY .*", "", sql_query, flags=re.IGNORECASE)

    # Extract everything after FROM
    match = re.search(r"\bFROM\b\s+(.*)", sql_query, re.IGNORECASE)
    if not match:
        return False

    after_from = match.group(1)  # Capture everything after FROM

    # Construct EXISTS query
    exists_query = f"SELECT EXISTS (SELECT 1 FROM {after_from})"

    # Connect to the database and execute the query
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(exists_query)
            exists = cursor.fetchone()[0]
        except ValueError:
            return False

    return bool(exists)
    



# Define OpenAI Function Calling tools
tools = [{
    "type": "function",
    "function": {
        "name": "quick_check_sql",
        "description": "Checks whether a given SQL query returns any data before execution.",
        "parameters": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "The SQL SELECT query to check."
                }
            },
            "required": ["sql_query"],
            "additionalProperties": False
        },
        "strict": True
    }
}]

def check_data_existence(sql_query: str) :
    """
    Uses OpenAI Function Calling to verify whether a generated SQL query returns any data.

    This function:
    - Sends a request to OpenAI to check if there is relevant data for the given SQL query.
    - If OpenAI invokes the `quick_check_sql` function, it extracts the SQL query parameters and executes it.
    - The response from OpenAI is then appended to the conversation history.
    - Finally, a second OpenAI API call is made, and the response content is returned as is.

    Args:
        sql_query (str): The SQL SELECT query that needs to be checked.

    Returns:
        str: The content of OpenAI's response, which may indicate whether data exists.
    """
    messages = [{"role": "user", "content": f"Check if data exists for query: {sql_query}"}]
    
    # Initial API request
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages, # type: ignore
        tools=tools, # type: ignore
        tool_choice="auto"  
    )

    # If OpenAI decides to invoke `quick_check_sql`
    if completion.choices[0].message.tool_calls:
        tool_call = completion.choices[0].message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)

        # Execute the function and get the result
        result = quick_check_sql(arguments["sql_query"])

        messages.append(completion.choices[0].message) # type: ignore
        messages.append({                               # append result message
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result)
        })

        completion_2 = client.chat.completions.create(
            model="gpt-4o",
            messages=messages, # type: ignore
            tools=tools, # type: ignore
        )
        
        # Return the result extracted from the AI response
        return completion_2.choices[0].message.content# type: ignore