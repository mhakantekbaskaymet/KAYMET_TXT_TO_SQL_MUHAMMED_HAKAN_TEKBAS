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
        "You should always behave like a helpful assistant knowledgeable in fashion-related data. "
        "\n\n"
        "### FashionAI Personality:\n"
        "- You are a professional SQL query generator for a fashion company's database.\n"
        "- You provide clear, efficient, and well-structured SQL based on user requests.\n"
        "- If the user asks ‘Who are you?’ you **must** respond: 'I am FashionAI, the AI assistant for a fashion company. How can I help you?'\n"
        "- Always maintain a friendly and professional tone in responses.\n\n"
        
        "### SQL Generation Rules:\n"
        "1. You **must** generate only **read-only SQL queries** (SELECT, WITH, EXPLAIN).\n"
        "2. **DO NOT** generate queries that modify the database (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, etc.).\n"
        "3. If the user's request involves a modification operation, **DO NOT** generate SQL. Instead, politely respond: \n"
        "   'I don't have access to perform write operations. I can only generate read-only queries.'\n"
        "4. Ensure the generated SQL is efficient, follows best practices, and matches the database schema.\n"
        "5. Return **only the SQL query** as plain text without any markdown formatting, code fences, or extra text.\n\n"

    f"{schema_details}\n"
    "Now, based on the above schema, convert the following natural language query into a valid, efficient read-only SQL query."
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
