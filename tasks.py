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
    Process: Read -> Search -> Reply
    """
    def grade(self, state: EnvironmentState) -> float:
        points = 0.0
        ticket = next((t for t in state.tickets if t['id'] == 'TKT-001'), None)
        
        if state.current_ticket_id == 'TKT-001': points += 0.2
        if any('password' in h.lower() or 'auth' in h.lower() for h in state.terminal_history): points += 0.3
        
        if ticket and ticket['status'] == 'resolved':
            points += 0.5
            
        return round(max(0.0, min(1.0, points)), 2)

class MediumGrader(TaskGrader):
    """
    Grader for Ticket-002 (API 500 Error).
    Process: check_db -> restart_db -> verify status UP
    """
    def grade(self, state: EnvironmentState) -> float:
        points = 0.0
        ticket = next((t for t in state.tickets if t['id'] == 'TKT-002'), None)
        history = state.terminal_history
        
        if "check_db" in history: points += 0.2
        if "restart_db" in history: points += 0.3
        
        # State Validation
        if state.system.db_status == "UP":
            points += 0.3
            
        if ticket and ticket['status'] == 'resolved' and state.system.db_status == "UP":
            points += 0.2
            
        return round(max(0.0, min(1.0, points)), 2)

class HardGrader(TaskGrader):
    """
    Grader for Ticket-003 (Migration).
    Process: check_disk -> cleanup_disk (if needed) -> run_migration
    """
    def grade(self, state: EnvironmentState) -> float:
        points = 0.0
        ticket = next((t for t in state.tickets if t['id'] == 'TKT-003'), None)
        history = state.terminal_history
        
        if "check_disk new-server" in history: points += 0.2
        if "cleanup_disk new-server" in history: points += 0.3
        
        # Final State Check
        if "run_migration --src old --dst new" in history and state.system.disk_usage["new-server"] < 90:
            points += 0.3
        
        if ticket and ticket['status'] == 'resolved' and points >= 0.5:
            points += 0.2
            
        return round(max(0.0, min(1.0, points)), 2)

class ExtremeGrader(TaskGrader):
    """
    Grader for Ticket-004 (Cluster Failover).
    Sequence: check_cluster -> flush_cache -> initiate_failover
    """
    def grade(self, state: EnvironmentState) -> float:
        points = 0.0
        ticket = next((t for t in state.tickets if t['id'] == 'TKT-004'), None)
        history = state.terminal_history
        
        if "check_cluster_health" in history: points += 0.1
        
        try:
            flush_idx = history.index("flush_cache --node US-EAST-01")
            points += 0.3
            
            if "initiate_failover --node US-EAST-01" in history:
                fail_idx = history.index("initiate_failover --node US-EAST-01")
                if fail_idx > flush_idx:
                    points += 0.4 # Bonus for correct sequence
                else:
                    points += 0.1 # Out of order
        except ValueError:
            if "initiate_failover --node US-EAST-01" in history:
                points += 0.1 # Danger zone
        
        # State check
        node = next((n for n in state.system.nodes if n['id'] == "US-EAST-01"), None)
        if node and node["status"] == "DOWN" and node["cache"] == "CLEAN":
            points += 0.1
            if ticket and ticket['status'] == 'resolved':
                points += 0.1
            
        return round(max(0.0, min(1.0, points)), 2)

class LegendaryGrader(TaskGrader):
    """
    Grader for Ticket-005 (Network Outage).
    Process: check_network_config -> apply_config --rule LOAD_BALANCE
    """
    def grade(self, state: EnvironmentState) -> float:
        points = 0.0
        ticket = next((t for t in state.tickets if t['id'] == 'TKT-005'), None)
        history = state.terminal_history
        
        if "check_network_config" in history: points += 0.2
        if "apply_config --rule LOAD_BALANCE" in history: points += 0.5
        
        # State validation
        if state.system.network_config["latency"] == "LOW":
            points += 0.2
            if ticket and ticket['status'] == 'resolved':
                points += 0.1
                
        return round(max(0.0, min(1.0, points)), 2)

def get_grader(task_id: str) -> TaskGrader:
    mapping = {
        "task_1": EasyGrader,
        "task_2": MediumGrader,
        "task_3": HardGrader,
        "task_4": ExtremeGrader,
        "task_5": LegendaryGrader
    }
    grader_cls = mapping.get(task_id, TaskGrader)
    return grader_cls(task_id)

