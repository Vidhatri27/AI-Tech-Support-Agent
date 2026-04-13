from typing import Optional, Tuple, Dict, Any, List
from models import Action, Observation, EnvironmentState, SystemState
import json
import random

class SupportEnv:
    def __init__(self, task_id: Optional[str] = None):
        self.task_id = task_id
        self.state_data = self._initial_state(task_id)
        self.max_steps = 20

    def _initial_state(self, task_id: str) -> EnvironmentState:
        all_tickets = [
            {"id": "TKT-001", "title": "Password Reset", "description": "I forgot my password and can't log in.", "status": "open", "type": "auth"},
            {"id": "TKT-002", "title": "API 500 Error", "description": "I'm getting 500 Internal Server Error when calling /api/v1/data.", "status": "open", "type": "technical"},
            {"id": "TKT-003", "title": "Migration Request", "description": "Please migrate my data from 'old-server' to 'new-server'.", "status": "open", "type": "migration"},
            {"id": "TKT-004", "title": "Cluster Failover", "description": "Response times are crashing in US-EAST zone. Immediate audit and fix required.", "status": "open", "type": "cluster"},
            {"id": "TKT-005", "title": "Network Outage", "description": "Complete service blackout in EU-WEST zone. Latency reported as 5000ms+.", "status": "open", "type": "network"},
        ]
        
        system = SystemState()
        
        if task_id == "task_1":
            tickets = [all_tickets[0]]
        elif task_id == "task_2":
            tickets = [all_tickets[1]]
            system.db_status = "DOWN"
        elif task_id == "task_3":
            tickets = [all_tickets[2]]
            system.disk_usage["new-server"] = 98.0 # Almost full
        elif task_id == "task_4":
            tickets = [all_tickets[3]]
            system.nodes[0]["status"] = "PARTIAL"
            system.nodes[0]["cache"] = "DIRTY"
        elif task_id == "task_5":
            tickets = [all_tickets[4]]
            system.network_config = {"rules": "STRICT_ISO", "latency": "CRITICAL"}
        else:
            tickets = all_tickets
            
        kb = [
            {"id": "KB-101", "topic": "auth", "content": "To reset password, tell the user to use the 'Forgot Password' link on the login page."},
            {"id": "KB-201", "topic": "technical", "content": "For 500 errors, check db connectivity via 'check_db' and service health via 'check_service'."},
            {"id": "KB-202", "topic": "database", "content": "If db connection fails, run 'restart_db' to fix common connection issues."},
            {"id": "KB-301", "topic": "migration", "content": "Before migration, verify disk space on 'new-server' using 'check_disk new-server'. If usage > 90%, run 'cleanup_disk <server>'."},
            {"id": "KB-302", "topic": "migration", "content": "Execute migration using 'run_migration --src old --dst new'."},
            {"id": "KB-401", "topic": "cluster", "content": "Cluster status: 'check_cluster_health'. If node is 'PARTIAL', check logs and 'flush_cache --node <name>' before failover."},
            {"id": "KB-402", "topic": "cluster", "content": "Failover logic: 'initiate_failover --node <name>'. Only proceed if cache is flushed or node is fully 'DOWN'."},
            {"id": "KB-501", "topic": "network", "content": "Latency issues in EU-WEST: Check network rules using 'check_network_config'. High latency often caused by 'STRICT_ISO' rules."},
            {"id": "KB-502", "topic": "network", "content": "Fixing network rules: Use 'apply_config --rule <NAME>'. For production traffic, use 'LOAD_BALANCE'."},
        ]
        
        return EnvironmentState(
            tickets=tickets,
            knowledge_base=kb,
            terminal_history=[],
            current_ticket_id=None,
            step_count=0,
            system=system
        )

    def reset(self) -> Observation:
        self.state_data = self._initial_state(self.task_id)
        return Observation(
            text="[SYSTEM] Support Environment Initialized. Use 'list_tickets' to see open issues.",
            available_actions=["list_tickets", "read_ticket", "search_kb"]
        )

    def state(self) -> EnvironmentState:
        return self.state_data

    def step(self, action: Action) -> Tuple[Observation, float, bool, Dict[str, Any]]:
        self.state_data.step_count += 1
        
        if self.state_data.step_count > self.max_steps:
             return Observation(text="Max steps exceeded (STMT_TIMEOUT).", available_actions=[]), -1.0, True, {"reason": "timeout"}

        reward = 0.0
        done = False
        obs_text = ""
        obs_data = {}

        action_type = action.action_type
        params = action.parameters

        if action_type == "list_tickets":
            open_tickets = [t for t in self.state_data.tickets if t['status'] == 'open']
            obs_text = "Open Tickets:\n" + "\n".join([f"{t['id']}: {t['title']}" for t in open_tickets])
            obs_data = {"tickets": open_tickets}
            reward += 0.05
            
        elif action_type == "read_ticket":
            ticket_id = params.get("ticket_id")
            ticket = next((t for t in self.state_data.tickets if t['id'] == ticket_id), None)
            if ticket:
                self.state_data.current_ticket_id = ticket_id
                obs_text = f"TICKET_DATA: {json.dumps(ticket, indent=2)}"
                obs_data = {"ticket": ticket}
                reward += 0.1
            else:
                obs_text = f"ERROR: Ticket {ticket_id} not found."
                reward -= 0.1

        elif action_type == "search_kb":
            query = params.get("query", "").lower()
            results = [k for k in self.state_data.knowledge_base if query in k['content'].lower() or query in k['topic'].lower()]
            obs_text = f"KB_SEARCH_RESULTS ({len(results)} matches):\n" + "\n".join([f"- {r['content']}" for r in results]) if results else "NO_RESULTS_FOUND."
            obs_data = {"results": results}
            reward += 0.1

        elif action_type == "run_diagnostic":
            command = params.get("command")
            self.state_data.terminal_history.append(command)
            system = self.state_data.system
            
            if command == "check_db":
                status = "CRITICAL" if system.db_status == "DOWN" else "HEALTHY"
                obs_text = f"[SYSTEM_CHECK] DB_STATUS: {status} | Latency: {'5s' if status == 'CRITICAL' else '2ms'}"
                reward += 0.1
            elif command == "check_service":
                obs_text = f"SERVICES: {json.dumps(system.services, indent=2)}"
                reward += 0.1
            elif command == "restart_db":
                system.db_status = "UP"
                obs_text = "[RESTART] Database services rebooting... DONE. STATUS=UP."
                reward += 0.3
            elif command == "check_disk new-server":
                usage = system.disk_usage["new-server"]
                obs_text = f"DISK_REPORT: node='new-server' | usage={usage}% | status={'WARNING' if usage > 90 else 'OK'}"
                reward += 0.2
            elif command == "cleanup_disk new-server":
                system.disk_usage["new-server"] = 45.0
                obs_text = "[CLEANUP] Deleted 152GB of temporary logs on 'new-server'. Usage is now 45%."
                reward += 0.3
            elif command == "run_migration --src old --dst new":
                if system.disk_usage["new-server"] > 90:
                    obs_text = "FAILED: Insufficient disk space on destination node 'new-server'."
                    reward -= 0.2
                else:
                    obs_text = "MIGRATION_JOB: ID=9928 | SRC=OLD | DST=NEW | PROGRESS=100% | STATUS=FINISHED"
                    reward += 0.4
            elif command == "check_cluster_health":
                obs_text = f"CLUSTER_NODES: {json.dumps(system.nodes, indent=2)}"
                reward += 0.1
            elif command == "flush_cache --node US-EAST-01":
                node = next((n for n in system.nodes if n['id'] == "US-EAST-01"), None)
                if node:
                    node["cache"] = "CLEAN"
                    obs_text = "[CACHE] Flushed node US-EAST-01. Status: CLEAN."
                    reward += 0.2
            elif command == "initiate_failover --node US-EAST-01":
                node = next((n for n in system.nodes if n['id'] == "US-EAST-01"), None)
                if node and node["cache"] == "DIRTY":
                    obs_text = "CRITICAL_ERROR: Cannot failover node with DIRTY cache. Data loss would occur."
                    reward -= 0.5
                elif node:
                    node["status"] = "DOWN"
                    obs_text = "[FAILOVER] US-EAST-01 deactivated. Traffic routing to standby nodes."
                    reward += 0.4
            elif command == "check_network_config":
                obs_text = f"NETWORK_CONFIG: {json.dumps(system.network_config, indent=2)}"
                reward += 0.2
            elif command.startswith("apply_config --rule"):
                rule = command.replace("apply_config --rule ", "")
                system.network_config["rules"] = rule
                if rule == "LOAD_BALANCE":
                    system.network_config["latency"] = "LOW"
                    obs_text = f"[CONFIG_APPLIED] Rule set to {rule}. Latency stabilized."
                else:
                    obs_text = f"[CONFIG_APPLIED] Rule set to {rule}. No change in latency."
                reward += 0.3
            else:
                obs_text = f"BASH: command not found: {command}"
                reward -= 0.1
                
            obs_data = {
                "system_state": system.dict(),
                "terminal_history": self.state_data.terminal_history
            }

        elif action_type == "send_reply":
            msg = params.get("message")
            status = params.get("status")
            
            current_ticket = next((t for t in self.state_data.tickets if t['id'] == self.state_data.current_ticket_id), None)
            if current_ticket:
                current_ticket['status'] = status
                obs_text = f"REPLY_SENT: Ticket {self.state_data.current_ticket_id} updated to {status}."
                done = (status == "resolved")
                reward += 0.2 if done else 0.1
                obs_data = {"ticket_status": status, "terminal_history": self.state_data.terminal_history}
            else:
                obs_text = "ERROR: No ticket context. Use 'read_ticket' first."
                reward -= 0.2

        else:
            obs_text = f"ERROR: Unknown action {action_type}"
            reward -= 0.1

        observation = Observation(
            text=obs_text,
            data=obs_data,
            available_actions=["list_tickets", "read_ticket", "search_kb", "run_diagnostic", "send_reply"]
        )
        
        return observation, reward, done, {}
