from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field

class ReadTicket(BaseModel):
    ticket_id: str = Field(..., description="ID of the ticket to read")

class SearchKB(BaseModel):
    query: str = Field(..., description="Search query for the knowledge base")

class RunDiagnostic(BaseModel):
    command: str = Field(..., description="Diagnostic command to run (e.g. 'check_service', 'check_db', 'list_files')")

class SendReply(BaseModel):
    message: str = Field(..., description="Message to send to the customer")
    status: Literal["resolved", "more_info_needed", "pending"] = Field(..., description="New status of the ticket")

class Action(BaseModel):
    action_type: Literal["read_ticket", "search_kb", "run_diagnostic", "send_reply", "list_tickets"]
    parameters: Union[ReadTicket, SearchKB, RunDiagnostic, SendReply, dict]

class Observation(BaseModel):
    text: str = Field(..., description="Primary text output from the action")
    data: dict = Field(default_factory=dict, description="Structured data returned by the action")
    available_actions: List[str] = Field(default_factory=list)

class Reward(BaseModel):
    value: float = Field(..., description="Reward value (usually 0.0 to 1.0 logic, but can be incremental)")
    done: bool = Field(..., description="Whether the episode is finished")
    info: dict = Field(default_factory=dict, description="Extra metadata about the step")

class EnvironmentState(BaseModel):
    tickets: List[dict]
    knowledge_base: List[dict]
    terminal_history: List[str]
    current_ticket_id: Optional[str] = None
    step_count: int = 0
