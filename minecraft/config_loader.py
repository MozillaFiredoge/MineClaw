"""
配置加载器 - 从 config.yml 读取配置
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

_config: Optional[Dict[str, Any]] = None


def load_config(config_path: str = None) -> Dict[str, Any]:
    """加载配置文件"""
    global _config
    
    if _config is not None:
        return _config
    
    if config_path is None:
        # 默认查找当前目录或父目录的 config.yml
        config_path = os.environ.get(
            "MINECLAW_CONFIG",
            str(Path(__file__).parent / "config.yml")
        )
    
    config_file = Path(config_path)
    if not config_file.exists():
        # 尝试父目录
        config_file = Path(__file__).parent.parent / "config.yml"
    
    if config_file.exists():
        with open(config_file) as f:
            _config = yaml.safe_load(f)
    else:
        # 返回默认配置
        _config = get_default_config()
    
    return _config


def get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return {
        "llm": {
            "model": "custom-api-edgefn-net/MiniMax-M2.5",
            "endpoint": "https://api.custom-api.edgefn.net/v1/chat/completions",
            "api_key": os.environ.get("OPENAI_API_KEY", ""),
            "max_tokens": 2048,
            "temperature": 0.7
        },
        "minecraft": {
            "host": "localhost",
            "port": 25565,
            "username": "OpenClawBot"
        },
        "bot": {
            "api_url": "http://localhost:3000"
        },
        "agent": {
            "max_steps": 100,
            "action_interval": 0.5,
            "screenshot_dir": "./screenshots",
            "skills_path": "./skills"
        }
    }


def get_llm_config() -> Dict[str, Any]:
    """获取 LLM 配置"""
    config = load_config()
    return config.get("llm", {})


def get_minecraft_config() -> Dict[str, Any]:
    """获取 Minecraft 配置"""
    config = load_config()
    return config.get("minecraft", {})


def get_bot_config() -> Dict[str, Any]:
    """获取 Bot 配置"""
    config = load_config()
    return config.get("bot", {})


def get_agent_config() -> Dict[str, Any]:
    """获取 Agent 配置"""
    config = load_config()
    return config.get("agent", {})


def reload_config():
    """重新加载配置"""
    global _config
    _config = None
    return load_config()
