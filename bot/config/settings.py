import os
from dotenv import load_dotenv

load_dotenv()

# Slack設定
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

# esa設定
ESA_ACCESS_TOKEN = os.getenv("ESA_ACCESS_TOKEN")
ESA_TEAM_NAME = os.getenv("ESA_TEAM_NAME")
ESA_API_BASE = "https://api.esa.io/v1"

# Gemini設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash-lite-preview-09-2025"

# 要約設定
SUMMARY_LENGTHS = {
    "short": "3-5文で簡潔に",
    "medium": "10文程度で詳しく",
    "long": "20文以上で詳細に"
}

SUMMARY_STYLES = {
    "bullet": "箇条書き",
    "paragraph": "段落形式"
}