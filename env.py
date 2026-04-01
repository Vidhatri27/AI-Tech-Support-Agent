import uuid
from typing import Optional, Tuple, Dict, Any, List
from models import Action, Observation, Reward, EnvironmentState
import json

class SupportEnv:
    def __init__(self, task_id: Optional[str] = None):
        self.task_id = task_id
        self.state_data = self._initial_state(task_id)
        self.max_steps = 15

    def _initial_state(self, task_id: str) -> EnvironmentState:
        all_tickets = [
            {"id": "TKT-001", "title": "Password Reset", "description": "I forgot my password and can't log in.", "status": "open", "type": "auth"},
            {"id": "TKT-002", "title": "API 500 Error", "description": "I'm getting 500 Internal Server Error when calling /api/v1/data.", "status": "open", "type": "technical"},
            {"id": "TKT-003", "title": "Migration Request", "description": "Please migrate my data from 'old-server' to 'new-server'.", "status": "open", "type": "migration"},
        ]
        
        if task_id == "task_1":
            tickets = [all_tickets[0]]
        elif task_id == "task_2":
            tickets = [all_tickets[1]]
        elif task_id == "task_3":
            tickets = [all_tickets[2]]
        else:
            tickets = all_tickets
            
        kb = [
            {"id": "KB-101", "topic": "auth", "content": "To reset password, tell the user to use the 'Forgot Password' link on the login page."},
            {"id": "KB-201", "topic": "technical", "content": "For 500 errors, check db connectivity via 'check_db' and service health via 'check_service'."},
            {"id": "KB-202", "topic": "database", "content": "If db connection fails, run 'restart_db' to fix common connection issues."},
            {"id": "KB-301", "topic": "migration", "content": "Before migration, verify disk space on 'new-server' using 'check_disk new-server'."},
            {"id": "KB-302", "topic": "migration", "content": "Execute migration using 'run_migration --src old --dst new'."},
        ]
        
        return EnvironmentState(
            tickets=tickets,
            knowledge_base=kb,
            terminal_history=[],
            current_ticket_id=None,
            step_count=0
        )

    def reset(self) -> Observation:
        self.state_data = self._initial_state(self.task_id)
        return Observation(
            text="Support Environment Initialized. Use 'list_tickets' to see open issues.",
            available_actions=["list_tickets", "read_ticket", "search_kb"]
        )

    def state(self) -> EnvironmentState:
        return self.state_data

    def step(self, action: Action) -> Tuple[Observation, float, bool, Dict[str, Any]]:
        self.state_data.step_count += 1
        
        if self.state_data.step_count > self.max_steps:
             return Observation(text="Max steps exceeded.", available_actions=[]), -1.0, True, {"reason": "timeout"}

        reward = 0.0
        done = False
        obs_text = ""
        obs_data = {}

        action_type = action.action_type
        params = action.parameters

        if action_type == "list_tickets":
            obs_text = "Open Tickets:\n" + "\n".join([f"{t['id']}: {t['title']}" for t in self.state_data.tickets if t['status'] == 'open'])
            obs_data = {"tickets": self.state_data.tickets}
            reward += 0.05
            
        elif action_type == "read_ticket":
            # params is dict or ReadTicket model
            ticket_id = params.get("ticket_id") if isinstance(params, dict) else getattr(params, "ticket_id", None)
            ticket = next((t for t in self.state_data.tickets if t['id'] == ticket_id), None)
            if ticket:
                self.state_data.current_ticket_id = ticket_id
                obs_text = f"Ticket [{ticket_id}]:\nDescription: {ticket['description']}"
                obs_data = {"ticket": ticket}
                reward += 0.1
            else:
                obs_text = f"Ticket {ticket_id} not found."
                reward -= 0.1

        elif action_type == "search_kb":
            query = params.get("query") if isinstance(params, dict) else getattr(params, "query", None)
            results = [k for k in self.state_data.knowledge_base if query.lower() in k['content'].lower() or query.lower() in k['topic'].lower()]
            obs_text = "Knowledge Base Results:\n" + "\n".join([f"- {r['content']}" for r in results]) if results else "No results found."
            obs_data = {"results": results}
            reward += 0.1

        elif action_type == "run_diagnostic":
            command = params.get("command") if isinstance(params, dict) else getattr(params, "command", None)
            self.state_data.terminal_history.append(command)
            
            # Simulated Command Logic
            if command == "check_db":
                obs_text = "Connection Error: Database unreachable at 10.0.0.5"
                reward += 0.2
            elif command == "check_service":
                obs_text = "Service Health: UP (version 1.2.3)"
                reward += 0.1
            elif command == "restart_db":
                obs_text = "Database restarted successfully. All connections cleared."
                reward += 0.3
            elif command == "check_disk new-server":
                obs_text = "Disk usage on new-server: 45% (200GB free)"
                reward += 0.2
            elif command == "run_migration --src old --dst new":
                obs_text = "Migration started... Progress: 100%. Finished."
                reward += 0.4
            else:
                obs_text = f"Command not found: {command}"
                reward -= 0.1
                
            obs_data = {"terminal_history": self.state_data.terminal_history}

        elif action_type == "send_reply":
            msg = params.get("message") if isinstance(params, dict) else getattr(params, "message", None)
            status = params.get("status") if isinstance(params, dict) else getattr(params, "status", None)
            
            current_ticket = next((t for t in self.state_data.tickets if t['id'] == self.state_data.current_ticket_id), None)
            if current_ticket:
                current_ticket['status'] = status
                obs_text = f"Reply sent to customer for {self.state_data.current_ticket_id}. Status updated to {status}."
                # Internal Grader will check final outcome
                done = (status == "resolved")
                reward += 0.2 if done else 0.1
            else:
                obs_text = "No current ticket selected. Usage: read_ticket first."
                reward -= 0.2

        else:
            obs_text = f"Unknown action: {action_type}"
            reward -= 0.1

        observation = Observation(
            text=obs_text,
            data=obs_data,
            available_actions=["list_tickets", "read_ticket", "search_kb", "run_diagnostic", "send_reply"]
        )
        
        return observation, reward, done, {}
