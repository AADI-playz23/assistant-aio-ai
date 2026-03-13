import os
import json
from github import Github
import google.generativeai as genai

# 1. Load Environment Variables from GitHub Actions
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")
ISSUE_NUMBER = int(os.environ.get("ISSUE_NUMBER"))

# 2. Initialize APIs
genai.configure(api_key=GEMINI_API_KEY)
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)
issue = repo.get_issue(number=ISSUE_NUMBER)

def run_assistant():
    user_prompt = issue.body
    if not user_prompt:
        issue.create_comment("Error: The issue body is empty. Please provide coding instructions.")
        return

    issue.create_comment("🤖 Assistant activated! Processing your request and writing code...")

    # 3. Configure Gemini to output strict JSON
    model = genai.GenerativeModel('gemini-2.5-pro')
    system_instruction = """
    You are an autonomous AI coding assistant.
    You must output ONLY a valid JSON array of objects representing actions to take on a GitHub repository.
    Do not include markdown blocks, backticks, or any conversational text.
    
    Required JSON Format:
    [
      {"action": "create", "path": "folder/filename.ext", "content": "full file content here"},
      {"action": "update", "path": "existing.ext", "content": "new full file content here"},
      {"action": "delete", "path": "old_file.ext"}
    ]
    """
    
    try:
        # Call Gemini and enforce the application/json MIME type
        response = model.generate_content(
            f"{system_instruction}\n\nUser Request:\n{user_prompt}",
            generation_config={"response_mime_type": "application/json"}
        )
        
        # 4. Parse the JSON plan
        plan = json.loads(response.text)
        
        # 5. Execute actions on GitHub
        for task in plan:
            action = task.get("action")
            path = task.get("path")
            content = task.get("content", "")

            if action == "create":
                repo.create_file(path, f"AI: Created {path}", content)
            elif action == "update":
                # To update, PyGithub requires the current file's SHA hash
                file = repo.get_contents(path)
                repo.update_file(path, f"AI: Updated {path}", content, file.sha)
            elif action == "delete":
                # To delete, PyGithub also requires the current file's SHA hash
                file = repo.get_contents(path)
                repo.delete_file(path, f"AI: Deleted {path}", file.sha)

        issue.create_comment("✅ Task complete! The repository has been updated. Closing this issue.")
        issue.edit(state="closed")

    except Exception as e:
        issue.create_comment(f"⚠️ An error occurred while trying to execute the plan:\n```\n{str(e)}\n```")

if __name__ == "__main__":
    run_assistant()
