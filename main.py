"""FastAPI application for SQL query generation and execution."""

from typing import Dict, List,Any
from fastapi import FastAPI
import uuid
from pydantic import BaseModel
from utils import generate_sql_query, execute_sql_query,initialize_session_db,get_session_history,save_to_session,check_data_existence

app = FastAPI()

initialize_session_db()

class QueryRequest(BaseModel):
    """Schema for query requests including session ID."""
    session_id: str
    query: str


class SQLRequest(BaseModel):
    """Schema for SQL execution requests."""
    
    sql: str

class QueryResponse(BaseModel):
    """Schema for responses including the generated SQL query and its results."""
    sql: str
    results: List[Dict[str, Any]]


@app.post("/generate-sql", response_model=Dict[str, str])
def generate_sql(request: QueryRequest) -> Dict[str, str]:
    """Generates an SQL query based on a natural language query.

    Args:
        request (QueryRequest): The input query request.

    Returns:
        Dict[str, str]: The generated SQL query.

    Raises:
        HTTPException: If an error occurs during SQL generation.
    """
 
    sql_query = generate_sql_query(request.query)
    return {"sql": sql_query}


@app.post("/execute-sql", response_model=List[Dict[str, str]])
def execute_sql(request: SQLRequest) -> List[Dict[str, str]]:
    """Executes an SQL query and returns the results.

    Args:
        request (SQLRequest): The SQL query request.

    Returns:
        List[Dict[str, str]]: The query execution results.

    Raises:
        HTTPException: If an error occurs during SQL execution.
    """
   
    results = execute_sql_query(request.sql)
    return results

  
@app.post("/query", response_model=QueryResponse)
def process_query(request: QueryRequest) -> QueryResponse:
    """
    Processes a natural language query by generating an SQL query and executing it.
    
    If the generated SQL is not read-only, it returns a GPT-generated explanation instead of executing the query.
    
    Args:
        request (QueryRequest): The natural language query request.
        
    Returns:
        QueryResponse: Contains the generated SQL query and either the execution results.
    """
    
    history = get_session_history(request.session_id)
    if history:
    # Create a structured conversation history prompt
        history_text = "\n\n".join([f"User: {entry['user']}\nAI: {entry['ai']}" for entry in history])

        full_prompt = (
        "You are FashionAI, assisting users with fashion database queries."
        "You remember prior queries and provide coherent responses."
        f"Conversation history:\n{history_text}\n\n"
        f"Current user query:\nUser: {request.query}\n"
        f"Generate a valid **read-only** SQL query based on the context provided."
        )
    else:
        # New session, providing clear instruction
        full_prompt = (
            f"User query:\nUser: {request.query}\n"
            f"Generate a valid **read-only** SQL query based on this query."
        )

    sql_query = generate_sql_query(full_prompt)
    try:
        results = execute_sql_query(sql_query)
    except ValueError:
        return QueryResponse(sql=sql_query, results=[])

    # Store new conversation entry
    ai_response = f"SQL Query: {sql_query}" if not results else str(results)
    save_to_session(request.session_id, request.query, ai_response)


    return QueryResponse(sql=sql_query, results=results)




@app.get("/new-session")
def create_new_session():
    """
    Generates a new session ID for a fresh conversation.
    Returns:
        Dict[str, str]: A dictionary containing the newly generated session ID.
 
    """

    session_id = str(uuid.uuid4())
    return {"session_id": session_id}

@app.post("/check-and-execute")
def check_and_execute(request: QueryRequest):
    """
    API endpoint to:
    - Convert a natural language query into an SQL query.
    - Check if the generated SQL query returns any data.
    - If data exists, execute the SQL query and return the results.
    - Handles execution errors gracefully.

    Args:
        request (QueryRequest): A request containing session_id and a user query.

    Returns:
        dict: A dictionary containing:
              - "status" (bool): Indicates whether relevant data exists for the query.
              - "sql_query" (str): The generated SQL query.
              - "results" (list): The execution results if data exists, else an empty list.
    """

    # Step 1: Convert natural language query into SQL
    sql_query = generate_sql_query(request.query)

    # Step 2: Verify if query returns data using check_data_existence()
    data_exists = check_data_existence(sql_query)

    # Step 3: Execute SQL query since data exists
    try:
        results = execute_sql_query(sql_query)
    except ValueError:
        response = QueryResponse(sql=sql_query, results=[])
        return response.model_copy(update={"status": data_exists})
    
    

    return {"status": data_exists, "sql_query": sql_query, "results": results}