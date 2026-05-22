# Database Performance Monitor

This web application monitors the following metrics of a PostgreSQL database:
- number of active connections
- usage of CPU
- memory usage
- number of slow queries

### Endpoints and collection of data

It is implemented using FastAPI, and has the following endpoints: / for basic application status, /active-connections, /cpu-usage, /memory-usage, /slow-queries, /metrics, /ai-insights and /history. Aside from those, there is also a /dashboard endpoint which is a user interface that allows you to test all the other endpoints.

Metrics are collected in the background every 20 seconds while the app is running, and the stored history is limited to the last 500 JSON objects.

### AI Anomaly Detection

For the AI part I am using an IsolationForest model in order to detect anomalies using unsupervised learning, and then the application analyzes which metrics contributed to the anomaly. Based on the metric at fault, a recommendation will be displayed.

Examples of detected anomalies:
- unusually high CPU usage
- unusually high memory usage
- unusual connection patterns
- abnormal slow query activity

### Dashboard

The project includes a simple web dashboard implemented using:

- HTML
- JavaScript
- Chart.js

The dashboard allows:

- manual metric collection
- AI analysis
- slow query inspection
- historical metrics visualization using charts

### Architecture overview

- Frontend Dashboard (HTML + Chart.js)
                
- FastAPI Backend
                
- Metrics Collection Layer
                
- PostgreSQL + System Monitoring
                
- Local JSON Data Storage
                
- AI Anomaly Detection Layer
                
- Recommendation Generator

### Setup instructions

Clone the repository: 
git clone https://github.com/Adela717/Database-Performance-Monitor.git

cd Database-Performance-Monitor

Create virtual environment:

python -m venv .venv

.\.venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Create a .env file:
DB_HOST=localhost

DB_PORT=5432

DB_NAME=postgres

DB_USER=postgres

DB_PASSWORD=your_password

Run the application:
python -m uvicorn app.main:app --reload

Access the Application:
- Dashboard: http://127.0.0.1:8000/dashboard
- Swagger API Documentation: http://127.0.0.1:8000/docs