from fastapi import FastAPI

app = FastAPI(title="Database Performance Monitor")

@app.get("/")
def home():
    return {"message": "Database Performance Monitor is running"}
