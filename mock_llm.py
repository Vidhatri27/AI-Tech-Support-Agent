from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import json

app = FastAPI()

class Message(BaseModel):
    role: str
    content: list | str

class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    response_format: dict | None = None

@app.post("/v1/chat/completions")
def chat_completions(req: ChatRequest):
    prompt_text = ""
    for msg in req.messages:
        if isinstance(msg.content, list):
            for c in msg.content:
                if 'text' in c: prompt_text += c['text']
        else:
            prompt_text += str(msg.content)
            
    action = {"action_type": "list_tickets", "parameters": {}}
    
    # State mapping based on prompt substrings
    
    # Task 1 (Password)
    if "TKT-001" in prompt_text and "Password" in prompt_text:
        if "Current Ticket: None" in prompt_text and "I forgot my password" not in prompt_text:
            action = {"action_type": "read_ticket", "parameters": {"ticket_id": "TKT-001"}}
        elif "I forgot my password" in prompt_text and "To reset password" not in prompt_text:
            action = {"action_type": "search_kb", "parameters": {"query": "password"}}
        elif "To reset password" in prompt_text:
            action = {"action_type": "send_reply", "parameters": {"message": "Use the Forgot Password link.", "status": "resolved"}}
            
    # Task 2 (500 Error)
    elif "TKT-002" in prompt_text and "500 Error" in prompt_text:
        if "Current Ticket: None" in prompt_text and "Internal Server Error" not in prompt_text:
            action = {"action_type": "read_ticket", "parameters": {"ticket_id": "TKT-002"}}
        elif "Internal Server Error" in prompt_text and "Connection Error" not in prompt_text and "Database restarted" not in prompt_text:
            action = {"action_type": "run_diagnostic", "parameters": {"command": "check_db"}}
        elif "Connection Error" in prompt_text and "Database restarted" not in prompt_text:
            action = {"action_type": "run_diagnostic", "parameters": {"command": "restart_db"}}
        elif "Database restarted" in prompt_text:
            action = {"action_type": "send_reply", "parameters": {"message": "Fixed", "status": "resolved"}}
            
    # Task 3 (Migration)
    elif "TKT-003" in prompt_text and "Migration Request" in prompt_text:
        if "Current Ticket: None" in prompt_text and "migrate my data" not in prompt_text:
            action = {"action_type": "read_ticket", "parameters": {"ticket_id": "TKT-003"}}
        elif "migrate my data" in prompt_text and "Disk usage" not in prompt_text and "Migration started" not in prompt_text:
            action = {"action_type": "run_diagnostic", "parameters": {"command": "check_disk new-server"}}
        elif "Disk usage" in prompt_text and "Migration started" not in prompt_text:
            action = {"action_type": "run_diagnostic", "parameters": {"command": "run_migration --src old --dst new"}}
        elif "Migration started" in prompt_text:
            action = {"action_type": "send_reply", "parameters": {"message": "Done", "status": "resolved"}}

    return {"choices": [{"message": {"content": json.dumps(action)}}]}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
