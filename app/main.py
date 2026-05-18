from fastapi import FastAPI
from app.db import get_connection

app = FastAPI(title="Database Performance Monitor")

@app.get("/")
def home():
    return {"message": "Database Performance Monitor is running"}

@app.get("/db-test")
def db_test():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return {
        "database_connection": "successful",
        "postgres_version": version
    }