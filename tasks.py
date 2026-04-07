from typing import List, Dict, Any, Optional
from env import SupportEnv
from models import Action, EnvironmentState

class TaskGrader:
    def __init__(self, task_id: str):
        self.task_id = task_id

    def grade(self, state: EnvironmentState) -> float:
        raise NotImplementedError

class EasyGrader(TaskGrader):
    """
    Grader for Ticket-001 (Password Reset).
    Requirements:
    1. Read TKT-001.
    2. Search KB for 'password'.
    3. Send message with correct instructions.
    4. Close TKT-001 as 'resolved'.
    """
    def grade(self, state: EnvironmentState) -> float:
        score = 0.0
        
        # Check if TKT-001 is resolved
        ticket = next((t for t in state.tickets if t['id'] == 'TKT-001'), None)
        if ticket and ticket['status'] == 'resolved':
            score += 0.5
            
        # Check if they actually read it
        if state.current_ticket_id == 'TKT-001' or any(h for h in state.terminal_history if 'TKT-001' in h):
             score += 0.2
        
        # Check step count (penalize excessive looping)
        if state.step_count > 10:
            score -= 0.1
            
        final_score = score + 0.3 if ticket and ticket['status'] == 'resolved' else score
        return max(0.01, min(0.99, final_score))

class MediumGrader(TaskGrader):
    """
    Grader for Ticket-002 (API 500 Error).
    Requirements:
    1. Read TKT-002.
    2. Run 'check_db'.
    3. Run 'restart_db'.
    4. Close TKT-002 as 'resolved'.
    """
    def grade(self, state: EnvironmentState) -> float:
        score = 0.0
        ticket = next((t for t in state.tickets if t['id'] == 'TKT-002'), None)
        
        # Requirement checks
        has_checked_db = "check_db" in state.terminal_history
        has_restarted_db = "restart_db" in state.terminal_history
        
        if has_checked_db: score += 0.2
        if has_restarted_db: score += 0.4
        if ticket and ticket['status'] == 'resolved':
            if has_restarted_db:
                 score += 0.4
            else:
                 score += 0.1 # Resolved without fixing? Low score.
                 
        return max(0.01, min(0.99, score))

class HardGrader(TaskGrader):
    """
    Grader for Ticket-003 (Migration).
    Requirements:
    1. Verify disk space on new-server.
    2. Run migration.
    3. Resolve ticket.
    """
    def grade(self, state: EnvironmentState) -> float:
        score = 0.0
        ticket = next((t for t in state.tickets if t['id'] == 'TKT-003'), None)
        
        has_checked_disk = "check_disk new-server" in state.terminal_history
        has_run_migration = "run_migration --src old --dst new" in state.terminal_history
        
        if has_checked_disk: score += 0.3
        if has_run_migration: score += 0.4
        if ticket and ticket['status'] == 'resolved' and has_run_migration:
            score += 0.3
            
        return max(0.01, min(0.99, score))

def get_grader(task_id: str) -> TaskGrader:
    if task_id == "task_1":
        return EasyGrader(task_id)
    elif task_id == "task_2":
        return MediumGrader(task_id)
    elif task_id == "task_3":
        return HardGrader(task_id)
    else:
        return TaskGrader(task_id)

        
