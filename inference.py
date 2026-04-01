import os
import json
import textwrap
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI
from env import SupportEnv
from tasks import get_grader
from models import Action, Observation

# MANDATORY CONFIGURATION
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

# HYPERPARAMETERS
MAX_STEPS = 8
TEMPERATURE = 0.2
MAX_TOKENS = 500
FALLBACK_ACTION = {"action_type": "list_tickets", "parameters": {}}

def build_history_lines(history: List[str]) -> str:
    """Provides a rolling window of the last 4 major actions."""
    if not history:
        return "None"
    return "\n".join(history[-4:])

def parse_action_response(response_text: str) -> Dict[str, Any]:
    """Robust parser with regex fallbacks for mixed-format model outputs."""
    if not response_text:
        return FALLBACK_ACTION
    try:
        # Preferred: Direct JSON parsing
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback: Extract JSON block using regex
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
             try:
                 return json.loads(match.group(0))
             except:
                 pass
    return FALLBACK_ACTION

def build_user_prompt(step: int, obs: Observation, history: List[str]) -> str:
    """Constructs a high-fidelity prompt following the sample script's mapping."""
    ticket_id = obs.data.get("ticket", {}).get("id") or "None"
    kb_results = obs.data.get("results") or []
    terminal_out = obs.data.get("terminal_history") or []
    
    # Format environment-specific metadata
    kb_hint = "\n".join([f"    - {r['content'][:100]}..." for r in kb_results]) if kb_results else "    (none)"
    term_hint = "\n".join([f"    $ {cmd}" for cmd in terminal_out[-3:]]) if terminal_out else "    (empty)"

    return textwrap.dedent(f"""
        Step: {step}
        Current Ticket: {ticket_id}
        Target Goal: Analyze, diagnose, and resolve all open support tickets.
        
        Previous History:
        {build_history_lines(history)}
        
        Knowledge Base Context:
        {kb_hint}
        
        Recent Terminal History:
        {term_hint}
        
        Current Observation:
        {obs.text}
        
        Reply with exactly one JSON action object.
    """).strip()

SYSTEM_PROMPT = textwrap.dedent("""
    You are an AI Support Engineer orchestration agent.
    Your goal is to resolve customer tickets using the available tools.
    
    Tool Definitions:
    - list_tickets: List all open tickets. Use {} parameters.
    - read_ticket: Read ticket details. Use {"ticket_id": "TKT-###"}.
    - search_kb: Search knowledge base. Use {"query": "string"}.
    - run_diagnostic: Run commands. Use {"command": "cmd"}.
    - send_reply: Respond to customer. Use {"message": "msg", "status": "resolved/pending"}.
    
    Reply ONLY with a JSON object. No explanations.
    Example: {"action_type": "read_ticket", "parameters": {"ticket_id": "TKT-001"}}
""").strip()

def solve_task(task_id: str, client: OpenAI) -> float:
    print(f"\n[OpenEnv] Initializing Environment: {task_id}")
    env = SupportEnv(task_id=task_id)
    history: List[str] = []

    try:
        obs = env.reset()
        print(f"Episode Goal: Resolve {task_id} issues successfully.")

        for step in range(1, MAX_STEPS + 1):
            user_prompt = build_user_prompt(step, obs, history)
            
            # Using the exact multimodal-compatible message format from the sample
            messages = [
                {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT}]},
                {"role": "user", "content": [{"type": "text", "text": user_prompt}]}
            ]

            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                    response_format={ "type": "json_object" },
                    stream=False,
                )
                response_text = completion.choices[0].message.content or ""
            except Exception as exc:
                print(f"Model request failed ({exc}). Using fallback action.")
                response_text = json.dumps(FALLBACK_ACTION)

            res_json = parse_action_response(response_text)
            action_type = res_json.get("action_type")
            params = res_json.get("parameters", {})
            action_str = f"{action_type}({params})"
            
            print(f"Step {step}: model suggested -> {action_str}")

            # Execution
            action = Action(action_type=action_type, parameters=params)
            obs, reward, done, info = env.step(action)
            
            # Professional Logging matching sample pattern
            history_line = f"Step {step}: {action_str} -> reward {reward:+.2f}"
            history.append(history_line)
            
            print(f"  Reward: {reward:+.2f} | Done: {done}")

            if done:
                print("Episode complete.")
                break
        else:
             print(f"Reached max steps ({MAX_STEPS}).")

    finally:
        # env.close() # Local env cleanup if necessary
        pass

    score = get_grader(task_id).grade(env.state())
    print(f"[Result] Final Score for {task_id}: {score:.2f}")
    return score

def main():
    if not API_KEY:
        print("Error: HF_TOKEN (or OPENAI_API_KEY) not set.")
        exit(1)

    client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
    scores = {}
    
    print("="*60)
    print("OPENENV HACKATHON EVALUATION START")
    print("="*60)

    for tid in ["task_1", "task_2", "task_3"]:
        scores[tid] = solve_task(tid, client)
        
    print("\n" + "="*60)
    print("FINAL OPENENV RESULTS")
    print("="*60)
    for tid, s in scores.items():
        print(f" {tid:<10} | Baseline Score: {s:.2f}")
    print("="*60)

if __name__ == "__main__":
    main()
