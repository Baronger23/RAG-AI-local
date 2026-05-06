"""
Tool Functions for L3: Tool-Augmented RAG
Handles database queries and API calls to monitoring service
"""

import sqlite3
import time
from typing import Any, Dict, List, Optional

import requests

from config import SQLITE_PATH, MONITORING_API_BASE, MONITORING_API_TIMEOUT, DB_TYPE
from logger import logger


class DatabaseTool:
    """Tool for querying the GeekBrain database"""

    def __init__(self, db_path: str = SQLITE_PATH):
        self.db_path = db_path
        self._verify_database()

    def _verify_database(self):
        """Check if database file exists and has tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            )
            tables = cursor.fetchall()
            conn.close()

            if not tables:
                logger.warning(
                    f"Database exists but has no tables. Run seed_data.py first: "
                    f"cd data_package/scripts && python seed_data.py --db-type sqlite"
                )
            else:
                logger.info(f"Database verified. Tables: {[t[0] for t in tables]}")
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            logger.info(
                "To seed the database, run: cd data_package/scripts && python seed_data.py"
            )

    def query(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute a SQL query against the database.
        
        Use for:
        - Historical costs (monthly_costs table)
        - SLA targets (sla_targets table)
        - Incident history (incidents table)
        - Daily metrics trends (daily_metrics table)
        
        Example:
        SELECT SUM(total_cost) FROM monthly_costs 
        WHERE service = 'PaymentGW' AND month BETWEEN '2026-01' AND '2026-03'
        """
        logger.info(f"Executing database query: {sql_query[:100]}...")
        start_time = time.time()

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Execute query
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            conn.close()

            # Convert rows to list of dicts
            data = [dict(row) for row in rows]

            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Query executed successfully. Rows: {len(data)}, Duration: {duration_ms:.2f}ms"
            )

            return {
                "success": True,
                "row_count": len(data),
                "data": data,
                "query": sql_query,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": sql_query,
            }

    # Convenience methods for common queries
    def get_service_cost(self, service_name: str, month: str = None, start_month: str = None, end_month: str = None) -> Dict:
        """Get total cost for a service in a date range or specific month"""
        if month and not start_month:
            start_month = month
        if not end_month:
            end_month = start_month
            
        query = f"""
        SELECT service, SUM(total_cost) as total_cost, SUM(compute_cost) as compute_cost, 
               SUM(storage_cost) as storage_cost, SUM(network_cost) as network_cost,
               COUNT(*) as month_count
        FROM monthly_costs
        WHERE service = '{service_name}' AND month BETWEEN '{start_month}' AND '{end_month}'
        GROUP BY service
        """
        return self.query(query)

    def get_incidents(self, service_name: str = None, severity: str = None) -> Dict:
        """Get incidents, optionally filtered by service or severity"""
        where_clauses = []
        if service_name:
            where_clauses.append(f"service = '{service_name}'")
        if severity:
            where_clauses.append(f"severity = '{severity}'")

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
        SELECT * FROM incidents
        WHERE {where_clause}
        ORDER BY date DESC
        LIMIT 20
        """
        return self.query(query)

    def get_sla_targets(self, service_name: str) -> Dict:
        """Get SLA targets for a service"""
        query = f"SELECT * FROM sla_targets WHERE service = '{service_name}'"
        return self.query(query)

    def get_daily_metrics(self, service: str, start_date: str, end_date: str) -> Dict:
        """Get daily metrics for a service in a date range"""
        query = f"SELECT * FROM daily_metrics WHERE service = '{service}' AND date BETWEEN '{start_date}' AND '{end_date}' ORDER BY date ASC"
        return self.query(query)

    def get_daily_metrics_average(self, service: str, start_date: str, end_date: str) -> Dict:
        """Get average daily metrics for a service in a date range"""
        query = f"""
        SELECT service, 
               AVG(latency_p99_ms) as avg_latency_p99_ms,
               AVG(error_rate_percent) as avg_error_rate,
               AVG(requests_per_minute) as avg_rpm,
               AVG(availability_percent) as avg_availability
        FROM daily_metrics
        WHERE service = '{service}' AND date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY service
        """
        return self.query(query)


class MonitoringAPITool:
    """Tool for querying the live monitoring API"""

    def __init__(self, base_url: str = MONITORING_API_BASE):
        self.base_url = base_url
        self._verify_api()

    def _verify_api(self):
        """Check if monitoring API is reachable"""
        try:
            response = requests.get(
                f"{self.base_url}/services",
                timeout=MONITORING_API_TIMEOUT,
            )
            if response.status_code == 200:
                services = response.json()
                logger.info(f"Monitoring API verified. Services: {services}")
            else:
                logger.warning(f"Monitoring API returned status {response.status_code}")
        except Exception as e:
            logger.warning(
                f"Monitoring API not reachable at {self.base_url}: {e}. "
                f"Start it with: cd data_package/scripts && uvicorn monitoring_api:app --port 8000"
            )

    def get_services(self) -> Dict[str, Any]:
        """Get list of all available services"""
        try:
            response = requests.get(
                f"{self.base_url}/services",
                timeout=MONITORING_API_TIMEOUT,
            )
            response.raise_for_status()
            services = response.json()
            logger.info(f"Retrieved {len(services)} services from API")
            return {"success": True, "services": services}
        except Exception as e:
            logger.error(f"Failed to get services: {e}")
            return {"success": False, "error": str(e)}

    def get_metrics(self, service_name: str) -> Dict[str, Any]:
        """
        Get current live metrics for a service.
        Returns: latency (p50/p95/p99), error_rate, requests_per_minute, CPU/memory utilization
        """
        try:
            logger.info(f"Fetching current metrics for {service_name}")
            response = requests.get(
                f"{self.base_url}/metrics/{service_name}",
                timeout=MONITORING_API_TIMEOUT,
            )
            response.raise_for_status()
            metrics = response.json()

            logger.info(f"Retrieved metrics for {service_name}: {list(metrics.keys())}")
            return {"success": True, "metrics": metrics}
        except Exception as e:
            logger.error(f"Failed to get metrics for {service_name}: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get health status of a service.
        Returns: status (healthy/degraded/down), uptime percentages, active alerts
        """
        try:
            logger.info(f"Fetching status for {service_name}")
            response = requests.get(
                f"{self.base_url}/status/{service_name}",
                timeout=MONITORING_API_TIMEOUT,
            )
            response.raise_for_status()
            status = response.json()

            logger.info(f"Status for {service_name}: {status.get('status', 'unknown')}")
            return {"success": True, "status": status}
        except Exception as e:
            logger.error(f"Failed to get status for {service_name}: {e}")
            return {"success": False, "error": str(e)}

    def compare_services(self, service_names: List[str], metric_name: str) -> Dict[str, Any]:
        """Compare a specific metric across multiple services."""
        results = {}
        for svc in service_names:
            metrics_resp = self.get_metrics(svc)
            if metrics_resp.get("success"):
                results[svc] = metrics_resp["metrics"].get(metric_name, "N/A")
            else:
                results[svc] = f"Error: {metrics_resp.get('error')}"
        
        return {
            "success": True,
            "metric": metric_name,
            "comparison": results
        }

    def get_incidents(self, service_name: str = None) -> Dict[str, Any]:
        """Get incident history from monitoring API"""
        try:
            if service_name:
                url = f"{self.base_url}/incidents/{service_name}"
                logger.info(f"Fetching incidents for {service_name}")
            else:
                url = f"{self.base_url}/incidents"
                logger.info("Fetching all incidents")

            response = requests.get(url, timeout=MONITORING_API_TIMEOUT)
            response.raise_for_status()
            incidents = response.json()

            logger.info(f"Retrieved {len(incidents)} incidents")
            return {"success": True, "incidents": incidents}
        except Exception as e:
            logger.error(f"Failed to get incidents: {e}")
            return {"success": False, "error": str(e)}


# Global tool instances
db_tool = DatabaseTool()
api_tool = MonitoringAPITool()
