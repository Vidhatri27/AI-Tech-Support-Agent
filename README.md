# 🛠️ AI Tech Support Orchestrator (OpenEnv)



## 🌟 Overview

The **AI Tech Support Orchestrator** is more than a simple chatbot simulation. It models the actual workflow of a Senior Support Engineer, requiring agents to:
1.  **Analyze** incoming high-pressure technical tickets.
2.  **Retrieve** pertinent documentation from a structured Knowledge Base (KB).
3.  **Execute** diagnostic and restorative commands in a simulated terminal environment.
4.  **Communicate** through a formal customer response API.

---

## 🕹️ The Environment Stack

### 🛠️ Actions (The Tool Palette)
All actions are **Pydantic-validated** to ensure type-safe agent interactions:
*   `list_tickets`: Retrieve the active work queue.
*   `read_ticket(ticket_id)`: Deep-dive into a specific customer issue.
*   `search_kb(query)`: Query the technical repository for standard operating procedures (SOPs).
*   `run_diagnostic(command)`: Access a simulated bash terminal (e.g., `check_cluster_health`, `flush_cache`).
*   `send_reply(message, status)`: Formalize the ticket resolution and state update.

---

## 📊 Task & Difficulty Matrix

| Task ID | Name | Difficulty | Core Reasoning Challenge |
| :--- | :--- | :--- | :--- |
| `task_1` | **Auth Reset** | 🟢 Easy | Basic KB retrieval and status update. |
| `task_2` | **DB Recovery** | 🟡 Medium | Diagnostic-to-Fix loop (Verify failure before restart). |
| `task_3` | **Cloud Migration** | 🟠 Hard | Dependency-aware multi-step orchestration (Disk check + Move). |
| `task_4` | **Cluster Failover** | 🔴 Extreme | **Sequential logic**: Diagnose PARTIAL node -> Flush Cache -> Failover. |

---

## 📈 Performance Benchmarks (Baseline Scores)

The environment has been validated against **GPT-4o** and **Claude 3.5 Sonnet**.

| Model | Task 1 | Task 2 | Task 3 | Task 4 |
| :--- | :--- | :--- | :--- | :--- |
| **GPT-4o** | 1.00 | 1.00 | 1.00 | 1.00 |
| **Random Agent**| 0.05 | 0.01 | 0.01 | 0.00 |

---

## 🚀 Quick Start

### 📦 Containerized Execution (Recommended)
```bash
docker build -t openenv-support .
docker run -p 7860:7860 openenv-support
```

### 🐍 Local Development
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Run Evaluation Engine**:
   ```bash
   export HF_TOKEN="your_token"
   python inference.py
   ```

---

## 📑 OpenEnv Spec Compliance
This repository follows the **OpenEnv v1.0** specification. See `openenv.yaml` for full configuration details including observation and action space schemas.

> [!TIP]
> To pass Task 4 (Extreme), ensure your agent follows the KB articles in exact order. Failover without cache flushing will result in partial credit (0.4) instead of full marks.

