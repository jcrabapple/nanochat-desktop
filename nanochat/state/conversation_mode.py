"""
Conversation modes for different AI interaction styles.

Each mode has optimized prompts, temperature settings, and web search preferences
tailored to specific use cases.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class ConversationMode(Enum):
    """Different conversation modes for AI interactions"""
    STANDARD = "standard"
    CREATE = "create"
    EXPLORE = "explore"
    CODE = "code"
    LEARN = "learn"


@dataclass
class ModeConfig:
    """Configuration for a conversation mode"""
    name: str
    icon: str
    system_prompt: str
    temperature: float
    enable_web_search: bool
    description: str


# Mode configurations with optimized settings
MODE_CONFIGS = {
    ConversationMode.STANDARD: ModeConfig(
        name="Standard",
        icon="user-info-symbolic",
        system_prompt="",
        temperature=0.7,
        enable_web_search=False,
        description="Normal conversation mode (Ctrl+1)"
    ),

    ConversationMode.CREATE: ModeConfig(
        name="Create",
        icon="document-new-symbolic",
        system_prompt="You are a creative assistant. Help users create content including articles, stories, marketing copy, and more. Be imaginative and engaging.",
        temperature=0.8,
        enable_web_search=False,
        description="Content creation mode with higher creativity (Ctrl+2)"
    ),

    ConversationMode.EXPLORE: ModeConfig(
        name="Explore",
        icon="system-search-symbolic",
        system_prompt="You are a research assistant. Provide accurate, well-sourced information. Be thorough in your explanations and cite sources when possible.",
        temperature=0.5,
        enable_web_search=True,
        description="Research mode with web search enabled (Ctrl+3)"
    ),

    ConversationMode.CODE: ModeConfig(
        name="Code",
        icon="emblem-system-symbolic",
        system_prompt="You are a coding assistant. Provide clean, well-commented code following best practices. Explain your code clearly and suggest improvements when appropriate.",
        temperature=0.3,
        enable_web_search=False,
        description="Code generation with higher precision (Ctrl+4)"
    ),

    ConversationMode.LEARN: ModeConfig(
        name="Learn",
        icon="dialog-information-symbolic",
        system_prompt="You are an educational assistant. Explain concepts step by step, using examples and analogies. Check for understanding and offer to elaborate on complex topics.",
        temperature=0.6,
        enable_web_search=True,
        description="Learning mode with detailed explanations (Ctrl+5)"
    ),
}


def get_mode_config(mode: ConversationMode) -> ModeConfig:
    """Get configuration for a specific mode"""
    return MODE_CONFIGS.get(mode, MODE_CONFIGS[ConversationMode.STANDARD])


def get_all_modes() -> list[ConversationMode]:
    """Get all available conversation modes"""
    return list(MODE_CONFIGS.keys())
