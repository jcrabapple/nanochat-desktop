from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Message:
    """Message in conversation"""
    role: str  # 'user', 'assistant', 'system'
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class ChatRequest:
    """Request to chat completions endpoint"""
    model: str
    messages: List[Message]
    stream: bool = True
    temperature: float = 0.7
    max_tokens: int = 2000
    web_search: bool = False

    def to_payload(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "messages": [msg.to_dict() for msg in self.messages],
            "stream": self.stream,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "web_search": self.web_search
        }


@dataclass
class ChatResponse:
    """Response from chat completions endpoint"""
    content: str
    role: str = "assistant"
    finish_reason: Optional[str] = None
    web_sources: Optional[List[Dict[str, str]]] = None


@dataclass
class StreamChunk:
    """Single chunk from streaming response"""
    content: str
    done: bool = False
    web_sources: Optional[List[Dict[str, str]]] = None
