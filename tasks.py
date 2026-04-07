from typing import List, Dict, Any, Optional
from models import EnvironmentState

class TaskGrader:
    def __init__(self, task_id: str):
        self.task_id = task_id

    def grade(self, state: EnvironmentState) -> float:
        raise NotImplementedError

class EasyGrader(TaskGrader):
    """
    Grader for Ticket-001 (Password Reset).
    Criteria:
    - Read ticket (0.2)
    - Search KB for auth/password (0.3)
    - Resolve ticket (0.5)
    """
    def grade(self, state: EnvironmentState) -> float:
        points = 0.0
        ticket = next((t for t in state.tickets if t['id'] == 'TKT-001'), None)
        
        # 1. Did they read the ticket?
        if state.current_ticket_id == 'TKT-001' or any('TKT-001' in h for h in state.terminal_history):
            points += 0.2
            
        # 2. Did they search the KB?
        kb_keywords = ['password', 'auth', 'reset', 'forgot']
        if any(any(kw in h.lower() for kw in kb_keywords) for h in state.terminal_history):
             points += 0.3
             
        # 3. Final outcome
        if ticket and ticket['status'] == 'resolved':
            points += 0.5
            
        # Penalty for excessive steps (efficiency)
        if state.step_count > 6:
            points = max(0.1, points - 0.1)

        return round(min(1.0, points), 2)

class MediumGrader(TaskGrader):
    """
    Grader for Ticket-002 (API 500 Error).
    Criteria:
    - Check DB (0.2)
    - Restart DB (0.4)
    - Resolve (0.4)
    """
    def grade(self, state: EnvironmentState) -> float:
        points = 0.0
        ticket = next((t for t in state.tickets if t['id'] == 'TKT-002'), None)
        
        if "check_db" in state.terminal_history: points += 0.2
        if "restart_db" in state.terminal_history: points += 0.4
        
        if ticket and ticket['status'] == 'resolved' and "restart_db" in state.terminal_history:
            points += 0.4
        elif ticket and ticket['status'] == 'resolved':
            points += 0.1 # Resolve without fixing? Minimal credit.
            
        return round(min(1.0, points), 2)

class HardGrader(TaskGrader):
    """
    Grader for Ticket-003 (Migration).
    Criteria:
    - Check disk on new-server (0.3)
    - Run migration command (0.4)
    - Resolve (0.3)
    """
    def grade(self, state: EnvironmentState) -> float:
        points = 0.0
        ticket = next((t for t in state.tickets if t['id'] == 'TKT-003'), None)
        
        if "check_disk new-server" in state.terminal_history: points += 0.3
        if "run_migration --src old --dst new" in state.terminal_history: points += 0.4
        
        if ticket and ticket['status'] == 'resolved' and "run_migration" in str(state.terminal_history):
            points += 0.3
            
        return round(min(1.0, points), 2)

class ExtremeGrader(TaskGrader):
    """
    Grader for Ticket-004 (Cluster Failover).
    Requires exact sequence:
    1. Check cluster health (0.2)
    2. Flush cache for US-EAST-01 (0.3)
    3. Initiate failover for US-EAST-01 (0.3)
    4. Resolve (0.2)
    """
    def grade(self, state: EnvironmentState) -> float:
        points = 0.0
        ticket = next((t for t in state.tickets if t['id'] == 'TKT-004'), None)
        history = state.terminal_history
        
        if "check_cluster_health" in history: points += 0.2
        
        # Check for flush cache BEFORE failover (Premium logic)
        try:
            flush_idx = history.index("flush_cache --node US-EAST-01")
            points += 0.3
            
            if "initiate_failover --node US-EAST-01" in history:
                fail_idx = history.index("initiate_failover --node US-EAST-01")
                if fail_idx > flush_idx:
                    points += 0.3
                else:
                    points += 0.1 # Out of order
        except ValueError:
            if "initiate_failover --node US-EAST-01" in history:
                points += 0.1 # Failover without flush
        
        if ticket and ticket['status'] == 'resolved' and points > 0.5:
            points += 0.2
            
        return round(min(1.0, points), 2)

def get_grader(task_id: str) -> TaskGrader:
    mapping = {
        "task_1": EasyGrader,
        "task_2": MediumGrader,
        "task_3": HardGrader,
        "task_4": ExtremeGrader
    }
    grader_cls = mapping.get(task_id, TaskGrader)
    return grader_cls(task_id)

