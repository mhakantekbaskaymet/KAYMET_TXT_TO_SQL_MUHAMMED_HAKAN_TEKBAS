"""FastAPI application for SQL query generation and execution."""

from typing import Dict, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from utils import generate_sql_query, execute_sql_query

app = FastAPI()


class QueryRequest(BaseModel):
    """Schema for query generation requests."""
    
    query: str


class SQLRequest(BaseModel):
    """Schema for SQL execution requests."""
    
    sql: str


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
    try:
        sql_query = generate_sql_query(request.query)
        return {"sql": sql_query}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Error generating SQL: {str(error)}")


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
    try:
        results = execute_sql_query(request.sql)
        return results
    
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Error executing SQL: {str(error)}")
