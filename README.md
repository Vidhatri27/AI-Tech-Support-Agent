# AI Tech Support Orchestrator (OpenEnv)

### Overview
The **AI Tech Support Orchestrator** is a high-fidelity OpenEnv environment designed to train and evaluate AI agents on real-world technical support workflows. Unlike simple games, this environment simulates a modern support stack, including a ticket management system, a searchable knowledge base, and a diagnostic terminal.

### Motivation
In the real world, support engineers don't just "chat." They:
1.  **Analyze** ticket data.
2.  **Search** internal documentation (KBs).
3.  **Run** diagnostics (API checks, database restarts).
4.  **Action** resolutions (sending replies, closing tickets).

This environment provides a structured way to measure an agent's ability to reason across these disparate tools.

---

### Action & Observation Space

#### Action Space
Agents can perform the following Pydantic-validated actions:
- **`list_tickets`**: Returns a list of all currently open tickets.
- **`read_ticket(ticket_id)`**: Retrieves detailed information about a specific ticket.
- **`search_kb(query)`**: Performs a semantic-like search across the knowledge base.
- **`run_diagnostic(command)`**: Executes a simulated system command (e.g., `check_db`, `restart_service`).
- **`send_reply(message, status)`**: Communicates with the customer and updates the ticket status.

#### Observation Space
The environment returns:
- **`text`**: Human-readable output (e.g., command results, KB snippets).
- **`data`**: Structured metadata for programmatic processing.
- **`available_actions`**: A list of valid next steps.

---

### Tasks & Evaluation logic

| Task ID | Name | Difficulty | Description | Grader Logic |
|---|---|---|---|---|
| `task_1` | Password Reset | **Easy** | Resolve a simple auth issue using the KB. | Checks for correct KB usage and 'resolved' status. |
| `task_2` | API 500 Error | **Medium** | Diagnose a database connection failure and fix it. | Requires `check_db` and `restart_db` in history. |
| `task_3` | Data Migration | **Hard** | Execute a multi-step server-to-server migration. | Verifies `check_disk` before `run_migration`. |

---

### Setup & Usage

#### Local Setup (Python)
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn pydantic openai
   ```
3. Run the inference script:
   ```bash
   export OPENAI_API_KEY="your-key"
   python inference.py
   ```

#### Containerized Execution (Docker)
1. Build the image:
   ```bash
   docker build -t openenv-support .
   ```
2. Run the environment:
   ```bash
   docker run -p 7860:7860 openenv-support
   ```

#### Deployment (Hugging Face Spaces)
This environment is designed for HF Spaces. Simply push the files and set the Space type to **Docker**.

---

### Baseline Scores (Reproduce using GPT-4o)
- **Task 1**: 1.00
- **Task 2**: 1.00
- **Task 3**: 1.00
*Note: Scores may vary slightly due to model stochasticity, but the environment provides clear signals for partial progress.*

---

### Environment Metadata (openenv.yaml)
```yaml
version: "1.0"
name: "AI Tech Support Orchestrator"
description: "Realistic Support Workflow Simulation"
...
```
