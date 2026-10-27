name: UPSC Current Affairs Daily Pipeline

on:
  schedule:
    - cron: '0 2 * * *' # Runs every day at 02:00 UTC
  workflow_dispatch:

jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install feedparser google-genai

      - name: Run Fetch and AI Classification
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python fetch_and_classify.py

      - name: Commit and push generated JSON payload
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add -A
          git diff-index --quiet HEAD || (git commit -m "Auto-update UPSC current affairs [skip ci]" && git push)
