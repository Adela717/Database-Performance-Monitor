import psutil
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db import get_connection
from datetime import datetime
from pathlib import Path
from app.anomaly_detector import detect_anomaly

app = FastAPI(title="Database Performance Monitor")

RECOMMENDATIONS = {
    "healthy": [
        "No major performance issues detected.",
        "Continue periodic monitoring."
    ],
    "high_cpu": [
        "High CPU usage detected.",
        "Check expensive queries or background processes."
    ],
    "high_memory": [
        "High memory usage detected.",
        "Check large result sets or memory-heavy operations."
    ],
    "high_connections": [
        "High number of database connections detected.",
        "Check if idle connections are being closed correctly."
    ],
    "slow_queries": [
        "Slow queries detected.",
        "Consider adding indexes on frequently filtered columns."
    ],
    "critical": [
        "Critical database performance situation detected.",
        "Investigate slow queries and system resource usage immediately.",
        "Reduce database load and check active connections."
    ]
}

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

    mem = psutil.virtual_memory()

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "cpu_usage_percent": psutil.cpu_percent(interval=1),
        "memory_usage_percent": mem.percent,
        "total_memory_gb": round(mem.total / (1024 ** 3), 2),
        "used_memory_gb": round(mem.used / (1024 ** 3), 2),
        "available_memory_gb": round(mem.available / (1024 ** 3), 2),
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

    with open(data_file, "w") as file:
        json.dump(history, file, indent=4)

    return metrics

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
	cpu_usage = psutil.cpu_percent(interval=1)
	return {
        "database_connection": "successful",
        "percantage_of_cpu_usage": cpu_usage
    }

@app.get("/memory-usage")
def memory():
    mem = psutil.virtual_memory()

    return {
        "memory_usage_percent": mem.percent,
        "total_memory_gb": round(mem.total / (1024 ** 3), 2),
        "used_memory_gb": round(mem.used / (1024 ** 3), 2),
        "available_memory_gb": round(mem.available / (1024 ** 3), 2)
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(periodic_metrics_collection())
    yield
    task.cancel()

@app.get("/ai-insights")
def ai_insights():
    current_metrics = collect_and_store_metrics()
    anomaly_result = detect_anomaly(current_metrics)

    return {
        "current_metrics": current_metrics,
        "ai_analysis": anomaly_result
    }