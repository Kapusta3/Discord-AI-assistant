from dataclasses import dataclass, asdict

@dataclass
class AgentRequest:
    user_id: int
    user_tag: str
    user_name: str
    message_id: int
    message_text: str
    chat_id: int
    chat_name: str
    chat_type: str
    server_id: int | None
    server_name: str | None
    is_bot: bool
    environment_info: str = ""

    def to_dict(self):
        return asdict(self)

@dataclass
class AgentResponse:
    should_reply: bool
    messages: list[str]