# FastAPI SQL Query Generator

## Description
This project is a FastAPI application that processes natural language queries to generate and execute SQL queries.

## Installation
You can run the application locally or using Docker.

### Local Setup

1. **Clone the repository:**
   ```sh 
   git clone https://github.com/mhakantekbaskaymet/KAYMET_TXT_TO_SQL_MUHAMMED_HAKAN_TEKBAS.git
   cd KAYMET_TXT_TO_SQL_MUHAMMED_HAKAN_TEKBAS

2. **Create a `.env` file:**
In the root of your project directory, create a .env file to store your ChatGPT API key:

    OPENAI_API_KEY=your_api_key_here

3. **Install Python dependencies:**

Make sure you have Python installed on your system. Install the required packages listed in `requirements.txt`: 

    pip install -r requirements.txt

4. **Start the FastAPI server:**

Launch the server using Uvicorn:

    python -m uvicorn main:app

   
5. **Access the application:**
Open your browser and go to [http://localhost:8000](http://localhost:8000) to view the FastAPI interface.

## Usage
Leverage the API endpoints provided by the FastAPI application to generate and execute SQL queries.

## API Endpoints:
View the API documentation and test the endpoints interactively by visiting:

[FastAPI Docs](http://localhost:8000/docs)

 **API Endpoints**
- POST /generate-sql: Generates an SQL query from a natural language input.
- OST /execute-sql: Executes a provided SQL query and returns its results.
- GET /new-session: Creates a new session for query history tracking.

## Contributing
We welcome contributions! Please fork the repository and submit a pull request.

## Contact
For any questions or support, please contact muhammed.tekbas@kaymet.com .