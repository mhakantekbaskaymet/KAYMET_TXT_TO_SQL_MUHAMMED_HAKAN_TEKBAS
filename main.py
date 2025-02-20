"""FastAPI application for SQL query generation and execution."""

from typing import Dict, List,Any
from fastapi import FastAPI
from pydantic import BaseModel
from utils import generate_sql_query, execute_sql_query
print(12)

app = FastAPI()


class QueryRequest(BaseModel):
    """Schema for query generation requests."""
    
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
    
    Args:
        request (QueryRequest): The natural language query request.
        
    Returns:
        QueryResponse: Contains the generated SQL query and the execution results.
        
    Raises:
        HTTPException: If an error occurs during SQL generation or execution.
    """
   
    sql_query = generate_sql_query(request.query)
 
    results = execute_sql_query(sql_query)    
    
    return QueryResponse(sql=sql_query, results=results)