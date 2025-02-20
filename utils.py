from openai import OpenAI
import os
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OpenAI.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()

def generate_sql_query(natural_language_query: str) -> str:
    """
    Generate SQL query from natural language using GPT-4.

    Args:
        natural_query: Natural language query string
        
    Returns:
        Generated SQL query string

    """
    schema_details = (
        "The database 'data.db' has the following schema:\n"
        "1. Products:\n"
        "   - ProductID\n"
        "   - Name (Name of product)\n"
        "   - Category1 (Men, Women, Kids)\n"
        "   - Category2 (Sandals, Casual Shoes, Boots, Sports Shoes)\n\n"
        "2. Transactions:\n"
        "   - StoreID\n"
        "   - ProductID\n"
        "   - Quantity\n"
        "   - PricePerQuantity\n"
        "   - Timestamp (Year, Month, Day hour:minute:second)\n\n"
        "3. Stores:\n"
        "   - StoreID\n"
        "   - State (two-letter code e.g. NY, IL, TX)\n"
        "   - ZipCode\n\n"
    )

    prompt = (
        "You are a highly skilled SQL query generator specialized in SQLite. "
         f"{schema_details} "
        "Based on the above schema, convert the given natural language query into a valid, efficient SQL query. "
        "Return only the SQL code as plain text without any markdown formatting, code fences, or additional text. "
    )
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Natural language query: '{natural_language_query}'" }],
        temperature=0,
    )
    return response.choices[0].message.content.strip()

def execute_sql_query(sql: str) -> list[dict[str, str]]:
    """
    Execute SQL query against SQLite database.
    
    Args:
        sql_query: SQL query to execute
        
    Returns:
        List of dictionaries containing query results
    """
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
