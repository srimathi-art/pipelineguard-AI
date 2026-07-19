import re
from pathlib import Path

import joblib
import pandas as pd
import requests
import streamlit as st

from github_utils import (
    download_workflow_logs,
    get_workflow_runs,
    parse_github_repo_url,
)
from ml_utils import clean_log

MODEL_PATH = Path("models/log_classifier.joblib")

SUGGESTIONS = {
    "ERROR": {
        "testing": "Review failed tests, fixtures, dependencies, and recent code changes.",
        "dependency": "Verify package versions, lock files, registries, and install commands.",
        "build": "Inspect the failed build step, compiler output, environment variables, and artifacts.",
        "deployment": "Check credentials, target environment health, configuration, and rollback status.",
        "database": "Check database connectivity, credentials, pool limits, and query timeouts.",
        "memory": "Inspect memory usage, reduce batch size, and check for memory leaks.",
        "network": "Verify DNS, firewall rules, service availability, and retry configuration.",
        "authentication": "Validate tokens, credentials, permissions, and token expiry.",
        "application": "Review the failing workflow step and the most recent code or configuration changes.",
    },
    "WARNING": {
        "testing": "Inspect skipped, flaky, or slow tests before the next release.",
        "dependency": "Review dependency warnings and update deprecated packages.",
        "performance": "Review slow operations, resource use, and thresholds.",
        "capacity": "Scale resources or reduce workload before the threshold is exceeded.",
        "configuration": "Review configuration values, secrets, and deprecated settings.",
        "application": "Monitor the warning and inspect related workflow steps.",
    },
    "INFO": {"application": "No immediate action is required."},
}

def detect_category(log: str) -> str:
    value = log.lower()
    groups = {
        "testing": ["pytest", "test failed", "tests failed", "assertionerror", "jest", "unit test"],
        "dependency": ["pip install", "npm install", "dependency", "package", "requirements", "module not found"],
        "build": ["build failed", "compilation", "compiler", "docker build", "image build", "makefile"],
        "deployment": ["deploy", "deployment", "release", "rollback", "environment"],
        "database": ["database", "sql", "query", "connection pool", "postgres", "mysql"],
        "memory": ["memory", "outofmemory", "heap", "allocation"],
        "network": ["network", "timeout", "dns", "socket", "connection refused", "unreachable"],
        "authentication": ["auth", "token", "login", "permission", "unauthorized", "forbidden", "secret"],
        "performance": ["slow", "latency", "response time", "degraded"],
        "capacity": ["cpu", "disk", "threshold", "capacity", "utilization"],
        "configuration": ["config", "deprecated", "environment variable"],
    }
    for category, keywords in groups.items():
        if any(keyword in value for keyword in keywords):
            return category
    return "application"

def recommendation(severity: str, category: str) -> str:
    return SUGGESTIONS.get(severity, {}).get(
        category,
        SUGGESTIONS.get(severity, {}).get("application", "Review the log details."),
    )

def ensure_model():
    try:
        model = joblib.load(MODEL_PATH)
        model.predict(["application started successfully"])
        return model
    except Exception:
        from train_model import train_and_save_model
        return train_and_save_model()

@st.cache_resource
def load_model():
    return ensure_model()

def analyze_logs(lines: list[str]) -> pd.DataFrame:
    valid = [
        line.strip() for line in lines
        if line.strip() and len(line.strip()) >= 8 and not re.fullmatch(r"[-=*#\s]+", line)
    ][:5000]
    if not valid:
        return pd.DataFrame()

    model = load_model()
    cleaned = [clean_log(line) for line in valid]
    predictions = model.predict(cleaned)
    probabilities = model.predict_proba(cleaned).max(axis=1)

    rows = []
    for original, severity, confidence in zip(valid, predictions, probabilities):
        category = detect_category(original)
        rows.append({
            "log": original,
            "severity": severity,
            "category": category,
            "confidence": round(float(confidence), 3),
            "suggested_action": recommendation(severity, category),
        })
    return pd.DataFrame(rows)

def run_label(run: dict) -> str:
    name = run.get("name") or "Workflow"
    branch = run.get("head_branch") or "unknown branch"
    state = run.get("conclusion") or run.get("status") or "unknown"
    number = run.get("run_number", "?")
    return f"#{number} · {name} · {branch} · {state}"

def show_results(result: pd.DataFrame, source: str):
    if result.empty:
        st.warning("No meaningful log entries were found.")
        return

    st.caption(f"Source: {source}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Logs Processed", len(result))
    c2.metric("Critical Events", int((result["severity"] == "ERROR").sum()))
    c3.metric("Warnings", int((result["severity"] == "WARNING").sum()))
    c4.metric("Informational", int((result["severity"] == "INFO").sum()))

    st.subheader("Incident Overview")
    st.bar_chart(result["severity"].value_counts().reindex(["ERROR", "WARNING", "INFO"], fill_value=0))

    st.subheader("Analysis Report")
    severity_filter = st.multiselect(
        "Filter severity",
        ["ERROR", "WARNING", "INFO"],
        default=["ERROR", "WARNING", "INFO"],
    )
    filtered = result[result["severity"].isin(severity_filter)]
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    st.download_button(
        "Export Report",
        result.to_csv(index=False).encode("utf-8"),
        "pipelineguard_analysis.csv",
        "text/csv",
        use_container_width=True,
    )

    st.subheader("Priority Findings")
    priority = result[result["severity"].isin(["ERROR", "WARNING"])].head(30)
    if priority.empty:
        st.success("No critical events or warnings were detected.")
    else:
        for _, row in priority.iterrows():
            with st.expander(f"{row['severity']} · {row['category'].title()} · {row['confidence']:.2f}"):
                st.code(row["log"])
                st.write(f"**Recommended action:** {row['suggested_action']}")

st.set_page_config(page_title="PipelineGuard AI", page_icon="🛡️", layout="wide")
st.title("PipelineGuard AI")
st.caption("CI/CD workflow monitoring and intelligent failure analysis")

github_tab, upload_tab, paste_tab = st.tabs(["GitHub Actions", "Upload Logs", "Paste Logs"])

with github_tab:
    st.subheader("Connect a GitHub Repository")
    repo_url = st.text_input(
        "Repository URL",
        placeholder="https://github.com/owner/repository",
    )
    token = st.text_input(
        "GitHub token",
        type="password",
        help="Optional for public repositories. Private repositories require Actions read access.",
    )

    if st.button("Connect Repository", type="primary", use_container_width=True):
        try:
            owner, repo = parse_github_repo_url(repo_url)
            with st.spinner("Loading workflow runs..."):
                runs = get_workflow_runs(owner, repo, token or None)
            st.session_state["owner"] = owner
            st.session_state["repo"] = repo
            st.session_state["runs"] = runs
            st.success(f"Connected to {owner}/{repo}" if runs else "Connected, but no workflow runs were found.")
        except (ValueError, RuntimeError, requests.RequestException) as exc:
            st.error(str(exc))

    runs = st.session_state.get("runs", [])
    if runs:
        completed = [run for run in runs if run.get("status") == "completed"]
        options = {run_label(run): run for run in (completed or runs)}
        selected_label = st.selectbox("Workflow run", list(options.keys()))
        selected = options[selected_label]

        if selected.get("html_url"):
            st.markdown(f"[Open selected run on GitHub]({selected['html_url']})")

        if st.button("Fetch and Analyze Workflow Logs", use_container_width=True):
            try:
                with st.spinner("Downloading and analyzing logs..."):
                    logs = download_workflow_logs(
                        st.session_state["owner"],
                        st.session_state["repo"],
                        int(selected["id"]),
                        token or None,
                    )
                    result = analyze_logs(logs)
                st.session_state["result"] = result
                st.session_state["source"] = (
                    f"GitHub Actions · {st.session_state['owner']}/"
                    f"{st.session_state['repo']} · Run #{selected.get('run_number')}"
                )
            except (RuntimeError, requests.RequestException) as exc:
                st.error(str(exc))
    st.info("""
⚠️ **GitHub Connection Notice**

GitHub workflow logs could not be retrieved. This may be due to repository
permissions or missing authorization.

You can still analyze logs using:
- 📄 Upload Log File (.txt)
- 📋 Paste Log Text
""")

with upload_tab:
    uploaded = st.file_uploader("Upload a .txt or .log file", type=["txt", "log"])
    if uploaded is not None and st.button("Analyze Uploaded Logs", use_container_width=True):
        content = uploaded.read().decode("utf-8", errors="ignore")
        st.session_state["result"] = analyze_logs(content.splitlines())
        st.session_state["source"] = uploaded.name

with paste_tab:
    manual = st.text_area("Paste logs, one entry per line", height=220)
    if st.button("Analyze Pasted Logs", use_container_width=True):
        st.session_state["result"] = analyze_logs(manual.splitlines())
        st.session_state["source"] = "Pasted logs"

if "result" in st.session_state:
    st.divider()
    show_results(st.session_state["result"], st.session_state.get("source", "Logs"))
