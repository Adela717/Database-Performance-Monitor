import json
from pathlib import Path
from statistics import mean
from sklearn.ensemble import IsolationForest


FEATURES = [
    "cpu_usage_percent",
    "memory_usage_mb",
    "active_connections",
    "slow_queries_count"
]


def load_metrics_history():
    data_file = Path("data/metrics.json")

    if not data_file.exists():
        return []

    with open(data_file, "r") as file:
        return json.load(file)


def extract_features(metrics_list):
    return [
        [
            item["cpu_usage_percent"],
            item["memory_usage_mb"],
            item["active_connections"],
            item["slow_queries_count"]
        ]
        for item in metrics_list
    ]


def detect_anomaly(current_metrics):
    history = load_metrics_history()

    if len(history) < 20:
        return {
            "status": "not_enough_data",
            "message": "At least 20 metric samples are needed for anomaly detection.",
            "is_anomaly": False
        }

    training_data = extract_features(history)

    model = IsolationForest(
        contamination=0.1,
        random_state=42
    )

    model.fit(training_data)

    current_data = [[
        current_metrics["cpu_usage_percent"],
        current_metrics["memory_usage_mb"],
        current_metrics["active_connections"],
        current_metrics["slow_queries_count"]
    ]]

    prediction = model.predict(current_data)[0]
    anomaly_score = model.decision_function(current_data)[0]

    is_anomaly = bool(prediction == -1)

    return {
        "status": "analyzed",
        "is_anomaly": is_anomaly,
        "prediction": int(prediction),
		"anomaly_score": float(anomaly_score),
        "interpretation": interpret_anomaly(current_metrics, history, is_anomaly)
    }


def interpret_anomaly(current_metrics, history, is_anomaly):
    if not is_anomaly:
        return [
            "The current metrics look normal compared to the collected history."
        ]

    recent_history = history[-20:]

    avg_cpu = mean(item["cpu_usage_percent"] for item in recent_history)
    avg_memory = mean(item["memory_usage_mb"] for item in recent_history)
    avg_connections = mean(item["active_connections"] for item in recent_history)
    avg_slow_queries = mean(item["slow_queries_count"] for item in recent_history)

    recommendations = []

    if current_metrics["cpu_usage_percent"] > avg_cpu * 1.5:
        recommendations.append("CPU usage is significantly higher than the recent average.")

    if current_metrics["memory_usage_mb"] > avg_memory * 1.3:
        recommendations.append("Memory usage is significantly higher than the recent average.")

    if current_metrics["active_connections"] > avg_connections * 1.5:
        recommendations.append("The number of active database connections is unusually high.")

    if current_metrics["slow_queries_count"] > avg_slow_queries + 2:
        recommendations.append("The number of slow queries is higher than usual.")

    if not recommendations:
        recommendations.append(
            "The combination of metrics is unusual, even if no single metric is extremely high."
        )

    return recommendations