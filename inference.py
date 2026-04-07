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
MAX_STEPS = 12
TEMPERATURE = 0.1
MAX_TOKENS = 600
FALLBACK_ACTION = {"action_type": "list_tickets", "parameters": {}}

def build_history_lines(history: List[str]) -> str:
    """Provides a rolling window of the last 5 major actions."""
    if not history:
        return "None"
    return "\n".join(history[-5:])

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
    kb_hint = "\n".join([f"    - {r['content'][:150]}..." for r in kb_results]) if kb_results else "    (none)"
    term_hint = "\n".join([f"    $ {cmd}" for cmd in terminal_out[-4:]]) if terminal_out else "    (empty)"

    return textwrap.dedent(f"""
        [STEP] {step}
        [CONTEXT] Current Ticket: {ticket_id}
        [OBJECTIVE] Use available tools to diagnose and resolve the issue.
        
        [HISTORY]
        {build_history_lines(history)}
        
        [KB_CONTEXT]
        {kb_hint}
        
        [TERMINAL_OUTPUT]
        {term_hint}
        
        [OBSERVATION]
        {obs.text}
        
        Reply with exactly one JSON action object.
    """).strip()

SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert AI Support Orchestration Agent. Your goal is to resolve technical tickets by methodically using diagnostics and knowledge bases.
    
    Available Tool Palette:
    1. list_tickets: {} - List all pending high-priority items.
    2. read_ticket: {"ticket_id": "TKT-###"} - Ingest ticket requirements.
    3. search_kb: {"query": "string"} - Query the internal technical repository.
    4. run_diagnostic: {"command": "cmd"} - Execute system-level probes or fixes.
    5. send_reply: {"message": "msg", "status": "resolved/pending"} - Deliver resolution to client.
    
    CRITICAL PROTOCOL:
    - Always search the KB if you are unsure of a command sequence.
    - Resolve the ticket ONLY after the diagnostic output confirms the fix was successful.
    - Reply ONLY with a valid JSON object. No pre-amble.
""").strip()

def solve_task(task_id: str, client: OpenAI) -> float:
    print(f"\n[OpenEnv] Initializing Environment: {task_id}")
    print(f"[START] task={task_id}", flush=True)
    env = SupportEnv(task_id=task_id)
    history: List[str] = []
    actual_steps = 0

    try:
        obs = env.reset()
        print(f"Episode Goal: Solve {task_id} efficiently.")

        for step in range(1, MAX_STEPS + 1):
            actual_steps = step
            user_prompt = build_user_prompt(step, obs, history)
            
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
                print(f"Model error ({exc}). Fallback to safety action.")
                response_text = json.dumps(FALLBACK_ACTION)

            res_json = parse_action_response(response_text)
            action_type = res_json.get("action_type", "list_tickets")
            params = res_json.get("parameters", {})
            action_str = f"{action_type}({params})"
            
            print(f"Step {step}: Agent Action -> {action_str}")

            # Execution
            action = Action(action_type=action_type, parameters=params)
            obs, reward, done, info = env.step(action)
            
            # Structured Logging
            history_line = f"S{step}: {action_str} -> {reward:+.2f}"
            history.append(history_line)
            
            print(f"  Step Reward: {reward:+.2f} | End Of Episode: {done}")
            print(f"[STEP] step={step} reward={reward}", flush=True)

            if done:
                print(f"Task {task_id} completed successfully in {step} steps.")
                break
        else:
             print(f"Exhausted total step allowance ({MAX_STEPS}).")

    finally:
        pass

    score = get_grader(task_id).grade(env.state())
    print(f"[FINAL] Score for {task_id}: {score:.2f}")
    print(f"[END] task={task_id} score={score} steps={actual_steps}", flush=True)
    return score

def main():
    if not API_KEY:
        print("CRITICAL ERROR: API key (HF_TOKEN or OPENAI_API_KEY) is not defined in environment.", flush=True)
        exit(1)

    client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
    scores = {}
    
    print("="*60, flush=True)
    print("OPENENV AI TECH SUPPORT EVALUATION ENGINE", flush=True)
    print("="*60, flush=True)

    for tid in ["task_1", "task_2", "task_3", "task_4"]:
        scores[tid] = solve_task(tid, client)
        
    print("\n" + "="*60, flush=True)
    print("CONSOLIDATED SCOREBOARD", flush=True)
    print("="*60, flush=True)
    for tid, s in scores.items():
        print(f" {tid:<10} | Score: {s:.2f}")
    print("="*60, flush=True)

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
