from fastapi import FastAPI, HTTPException
from models import Action, Observation, Reward, EnvironmentState
from env import SupportEnv
from typing import Optional, Dict

app = FastAPI(title="OpenEnv - AI Tech Support Orchestrator")

# Global session storage (simplified for single-user/demo)
sessions: Dict[str, SupportEnv] = {}

@app.get("/")
def health():
    return {"status": "ok", "message": "OpenEnv Tech Support environment is online."}

@app.post("/reset", response_model=Observation)
def reset(task_id: Optional[str] = None):
    session_id = "default" # Simplified
    env = SupportEnv(task_id=task_id)
    sessions[session_id] = env
    return env.reset()

@app.post("/step")
def step(action: Action):
    session_id = "default"
    if session_id not in sessions:
        raise HTTPException(status_code=400, detail="Call /reset first.")
    
    obs, reward, done, info = sessions[session_id].step(action)
    return {
        "observation": obs,
        "reward": reward,
        "done": done,
        "info": info
    }

@app.get("/state", response_model=EnvironmentState)
def get_state():
    session_id = "default"
    if session_id not in sessions:
        raise HTTPException(status_code=400, detail="Call /reset first.")
    return sessions[session_id].state()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
