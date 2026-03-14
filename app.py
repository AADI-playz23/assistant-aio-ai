import os
import json
import re
from flask import Flask, request, jsonify, render_template_string
from github import Github
import google.generativeai as genai

app = Flask(__name__)

# --- Configuration ---
# Set these in your terminal before running: export GITHUB_TOKEN="your_pat" etc.
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "YOUR_GITHUB_PAT")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_KEY")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY", "your-username/assistant-aio-ai")

# Initialize APIs
genai.configure(api_key=GEMINI_API_KEY)
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# --- Initialize Gemini with Memory ---
# We use system instructions to tell it how to format actions
system_instruction = """
You are an advanced, autonomous AI coding assistant. You chat naturally with the user to plan and discuss code.
When you decide to create, edit, or delete files in the repository, you MUST include a JSON block in your response.
Format the JSON exactly like this, enclosed in ```json and ``` tags:
```json
[
  {"action": "create", "path": "folder/file.py", "content": "print('hello')"},
  {"action": "update", "path": "existing.html", "content": "<h1>Updated</h1>"},
  {"action": "delete", "path": "old.txt"}
]
