import psutil
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db import get_connection
from datetime import datetime
from pathlib import Path
from app.anomaly_detector import detect_anomaly
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

templates = Jinja2Templates(directory="app/templates")

def collect_and_store_metrics():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT count(*) FROM pg_stat_activity;")
    active_connections_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT pid, now() - query_start AS duration, query
        FROM pg_stat_activity
        WHERE state = 'active'
        AND now() - query_start > interval '1 second';
    """)
    slow_query_rows = cursor.fetchall()

    cursor.close()
    conn.close()

    cpu = cpu_usage()["cpu_usage_percent"]
    memory = memory_usage()["memory_usage_mb"]

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "cpu_usage_percent": cpu,
        "memory_usage_mb": memory,
        "active_connections": active_connections_count,
        "slow_queries_count": len(slow_query_rows),
        "slow_queries": [
            {
                "pid": row[0],
                "duration": str(row[1]),
                "query": row[2]
            }
            for row in slow_query_rows
        ]
    }

    data_file = Path("data/metrics.json")
    data_file.parent.mkdir(exist_ok=True)

    if data_file.exists():
        with open(data_file, "r") as file:
            history = json.load(file)
    else:
        history = []

    history.append(metrics)
    history = history[-500:]

    with open(data_file, "w") as file:
        json.dump(history, file, indent=4)

    return metrics

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(periodic_metrics_collection())
    yield
    task.cancel()

app = FastAPI(title="Database Performance Monitor", lifespan=lifespan)

@app.get("/")
def home():
    return {"message": "Database Performance Monitor is running"}

@app.get("/active-connections")
def active_connections():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT count(*) FROM pg_stat_activity;")
    con = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return {
        "database_connection": "successful",
        "active_connections": con
    }

@app.get("/cpu-usage")
def cpu_usage():
    cpu_usage = 0

    for process in psutil.process_iter(["name", "cpu_percent"]):
        try:
            process_name = process.info["name"]

            if process_name and "postgres" in process_name.lower():
                cpu_usage += process.cpu_percent(interval=0.1)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    cpu_usage = cpu_usage / psutil.cpu_count()
    return {
        "cpu_usage_percent": cpu_usage
    }

@app.get("/memory-usage")
def memory_usage():
    memory_usage_bytes = 0

    for process in psutil.process_iter(["name", "memory_info"]):
        try:
            process_name = process.info["name"]

            if process_name and "postgres" in process_name.lower():
                memory_usage_bytes += process.info["memory_info"].rss

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    memory_usage_mb = round(memory_usage_bytes / (1024 ** 2), 2)

    return {
        "memory_usage_mb": memory_usage_mb
    }

@app.get("/slow-queries")
def slow_queries():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pid, now() - query_start AS duration, query
        FROM pg_stat_activity
        WHERE state = 'active'
        AND now() - query_start > interval '1 second';
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "slow_queries_count": len(rows),
        "slow_queries": [
            {
                "pid": row[0],
                "duration": str(row[1]),
                "query": row[2]
            }
            for row in rows
        ]
    }

@app.get("/metrics")
def collect_metrics():
    return collect_and_store_metrics()

async def periodic_metrics_collection():
    while True:
        collect_and_store_metrics()
        await asyncio.sleep(20)

@app.get("/ai-insights")
def ai_insights():
    current_metrics = collect_and_store_metrics()
    anomaly_result = detect_anomaly(current_metrics)

    return {
        "current_metrics": current_metrics,
        "ai_analysis": anomaly_result
    }

@app.get("/history")
def get_history():
    data_file = Path("data/metrics.json")

    if not data_file.exists():
        return {
            "count": 0,
            "history": []
        }

    with open(data_file, "r") as file:
        history = json.load(file)

    chart_data = [
        {
            "timestamp": item["timestamp"],
            "cpu_usage_percent": item["cpu_usage_percent"],
            "memory_usage_mb": item["memory_usage_mb"],
            "active_connections": item["active_connections"],
            "slow_queries_count": item["slow_queries_count"]
        }
        for item in history
    ]

    return {
        "count": len(chart_data),
        "history": chart_data
    }

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html"
    )