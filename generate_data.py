from pathlib import Path
import random
import pandas as pd

random.seed(42)

TEMPLATES = {
    "INFO": [
        "Application started successfully on port {n}",
        "User login completed successfully",
        "Scheduled backup completed",
        "Health check passed for service api",
        "Deployment version {n} completed successfully",
        "Configuration loaded successfully",
        "Request processed with status 200",
        "Worker process started",
        "Cache initialized successfully",
        "Database migration completed",
        "Docker image build completed",
        "All tests passed",
        "GitHub Actions workflow completed successfully",
    ],
    "WARNING": [
        "CPU utilization reached {n} percent",
        "Memory usage is above warning threshold",
        "API response time is slow at {n} milliseconds",
        "Disk capacity is approaching limit",
        "Deprecated configuration option detected",
        "Connection pool usage is high",
        "Retry attempt {n} for external service",
        "Authentication token will expire soon",
        "Queue size exceeded recommended threshold",
        "Network latency is elevated",
        "Dependency package is deprecated",
        "Test was skipped",
        "Docker build cache was not found",
    ],
    "ERROR": [
        "Database connection timed out",
        "OutOfMemoryError in worker process",
        "Authentication failed due to invalid token",
        "Connection refused by upstream service",
        "Disk write failed because device is full",
        "Unhandled exception in application module",
        "DNS resolution failed for service endpoint",
        "SQL query execution failed",
        "Permission denied while accessing configuration",
        "Critical service health check failed",
        "pytest test failed with AssertionError",
        "pip install failed because dependency was not found",
        "Docker image build failed",
        "Deployment failed due to missing secret",
        "GitHub Actions workflow failed",
    ],
}

def generate_dataset():
    rows = []
    for severity, patterns in TEMPLATES.items():
        for pattern in patterns:
            for _ in range(12):
                rows.append({"log": pattern.format(n=random.randint(2, 99)), "severity": severity})
    random.shuffle(rows)
    output = Path("data/training_logs.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output, index=False)
    print(f"Generated {len(rows)} logs")
    return output

if __name__ == "__main__":
    generate_dataset()
