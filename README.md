# live Application
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pipelineguard-ai.streamlit.app)
# PipelineGuard AI

Professional CI/CD log intelligence dashboard with GitHub Actions integration.

## Run on Windows

```bash
python -m pip install -r requirements.txt
python generate_data.py
python train_model.py
python -m streamlit run app.py
```

## GitHub Actions integration

1. Enter a repository URL.
2. Click **Connect Repository**.
3. Select a completed workflow run.
4. Click **Fetch and Analyze Workflow Logs**.

Public repositories may work without a token. Private repositories require a fine-grained GitHub personal access token with:

```text
Repository permissions → Actions → Read-only
```

Do not commit tokens to GitHub.

## Other input modes

- Upload `.txt` or `.log`
- Paste logs manually

## Docker

```bash
docker build -t pipelineguard-ai .
docker run -p 8501:8501 pipelineguard-ai
```

Open `http://localhost:8501`.
