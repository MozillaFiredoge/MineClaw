"""
OpenClaw Minecraft Agent
让 AI 能够玩 Minecraft
"""

from .agent import MinecraftAgent, create_agent
from .mineflayer_client import MineflayerClient, MCAPIClient

__version__ = "0.1.0"
__all__ = ["MinecraftAgent", "create_agent", "MineflayerClient", "MCAPIClient"]
