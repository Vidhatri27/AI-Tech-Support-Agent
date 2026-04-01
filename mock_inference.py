import json
from env import SupportEnv
from tasks import get_grader
from models import Action

def run_mock_task(task_id: str, actions: list):
    print(f"\n--- Running Mock Task: {task_id} ---")
    env = SupportEnv(task_id=task_id)
    obs = env.reset()
    
    for action_data in actions:
        action = Action(action_type=action_data["type"], parameters=action_data["params"])
        obs, reward, done, info = env.step(action)
        print(f"Action: {action_data['type']} -> Obs: {obs.text[:60]}... (Reward: {reward:+.2f})")
        if done:
            break
            
    score = get_grader(task_id).grade(env.state())
    print(f"Final Score for {task_id}: {score:.2f}")
    return score

if __name__ == "__main__":
    # Task 1: Password Reset
    task_1_actions = [
        {"type": "read_ticket", "params": {"ticket_id": "TKT-001"}},
        {"type": "search_kb", "params": {"query": "password"}},
        {"type": "send_reply", "params": {"message": "Use the Forgot Password link.", "status": "resolved"}}
    ]
    
    # Task 2: API 500 Error
    task_2_actions = [
        {"type": "read_ticket", "params": {"ticket_id": "TKT-002"}},
        {"type": "run_diagnostic", "params": {"command": "check_db"}},
        {"type": "run_diagnostic", "params": {"command": "restart_db"}},
        {"type": "send_reply", "params": {"message": "DB restarted, issue fixed.", "status": "resolved"}}
    ]
    
    # Task 3: Migration
    task_3_actions = [
        {"type": "read_ticket", "params": {"ticket_id": "TKT-003"}},
        {"type": "run_diagnostic", "params": {"command": "check_disk new-server"}},
        {"type": "run_diagnostic", "params": {"command": "run_migration --src old --dst new"}},
        {"type": "send_reply", "params": {"message": "Migration complete.", "status": "resolved"}}
    ]
    
    run_mock_task("task_1", task_1_actions)
    run_mock_task("task_2", task_2_actions)
    run_mock_task("task_3", task_3_actions)
