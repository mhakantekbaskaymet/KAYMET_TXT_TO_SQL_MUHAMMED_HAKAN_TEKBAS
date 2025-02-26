import sqlite3
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()


client = OpenAI()

def generate_sql_query(natural_language_query: str) -> str:
    """
    Generate SQL query from natural language using GPT-4.

    Args:
        natural_query: Natural language query string
        
    Returns:
        Generated SQL query string

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
    "- If asked ‘Who are you?’, respond in the user's language: \n"
    "  - Example (English): 'I am FashionAI, the AI assistant for a fashion company. How can I help you?'\n"
    "  - Example (Turkish): 'Ben FashionAI, bir moda şirketi için yapay zeka asistanıyım. Size nasıl yardımcı olabilirim?'\n\n"
    
    "### **SQL Generation Rules:**\n"
    "1. You **must** generate only **read-only SQL queries** (SELECT, WITH, EXPLAIN).\n"
    "2. **DO NOT** generate queries that modify the database (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, etc.).\n"
    "3. If the user's request involves a modification operation, **DO NOT** generate SQL. Instead, politely respond in the user's language: \n"
    "   - Example (English): 'I don't have access to perform write operations. I can only generate read-only queries.'\n"
    "   - Example (Turkish): 'Yazma işlemleri yapma yetkim yok. Sadece salt okunur sorgular üretebilirim.'\n\n"

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
    return response.choices[0].message.content.strip()

def execute_sql_query(sql: str) -> list[dict[str, str]]:
    """
    Execute SQL query against SQLite database (read-only queries only).
    
    Args:
        sql: SQL query to execute
        
    Returns:
        List of dictionaries containing query results
        
    Raises:
        ValueError: If the SQL query is not read-only.
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

def save_to_session(session_id: str, user_request: str, ai_response: str):
    """Save user request and AI response to the session database."""
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO sessions (session_id, user_request, ai_response)
        VALUES (?, ?, ?)
    """, (session_id, user_request, ai_response))
    
    conn.commit()
    conn.close()


def get_session_history(session_id: str):
    """Retrieve session history by session_id."""
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
