"""
Mineflayer Bot 客户端 - 通过 HTTP API 控制 Minecraft Bot
"""

import json
import base64
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime


class MineflayerClient:
    """Mineflayer Bot HTTP API 客户端"""
    
    def __init__(self, api_url: str = "http://localhost:3005", screenshot_dir: str = "./screenshots"):
        self.api_url = api_url.rstrip("/")
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
        
    async def close(self):
        """关闭 HTTP 会话"""
        if self._session and not self._session.closed:
            await self._session.close()
            
    async def _call_api(self, endpoint: str, method: str = "GET", data: Any = None) -> Dict:
        """调用 Bot HTTP API"""
        session = await self._get_session()
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        try:
            if method == "GET":
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    return await resp.json()
            elif method == "POST":
                async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    return await resp.json()
        except aiohttp.ClientError as e:
            return {"error": str(e), "success": False}
        except asyncio.TimeoutError:
            return {"error": "Request timeout", "success": False}
        except Exception as e:
            return {"error": f"Unexpected error: {e}", "success": False}
    
    async def _call_command(self, cmd: str) -> Dict:
        """通过 /command 端点执行动作"""
        return await self._call_api(f"command?cmd={cmd}", method="POST")
    
    # ==================== 核心功能 ====================
    
    async def get_status(self) -> Dict[str, Any]:
        """获取 Bot 状态"""
        result = await self._call_api("status")
        if "error" not in result:
            result["success"] = True
        return result
    
    async def get_inventory(self) -> Dict[str, Any]:
        """获取物品栏"""
        result = await self._call_api("inventory")
        return result
    
    async def screenshot(self) -> bytes:
        """获取截图"""
        result = await self._call_api("screenshot")
        if result.get("path"):
            try:
                with open(result["path"], "rb") as f:
                    return f.read()
            except:
                pass
        return b""
    
    # ==================== 动作执行 ====================
    
    async def move(self, direction: str = "forward", duration: float = 1.0) -> Dict:
        """
        移动 (调用 /command 端点)
        direction: forward, backward, left, right
        """
        return await self._call_command(f"move {direction}")
    
    async def jump(self) -> Dict:
        """跳跃"""
        return await self._call_command("jump")
    
    async def attack(self, entityId: Optional[int] = None) -> Dict:
        """攻击"""
        # 使用 /control/attack 端点
        session = await self._get_session()
        url = f"{self.api_url}/control/attack"
        try:
            async with session.post(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return await resp.json()
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def place_block(self, position: Dict[str, int] = None, block: str = "stone") -> Dict:
        """放置方块"""
        return await self._call_command(f"place {block}")
    
    async def use_item(self, slot: int = None) -> Dict:
        """使用物品"""
        return await self._call_command("use")
    
    async def look(self, yaw: float = None, pitch: float = None) -> Dict:
        """视角旋转"""
        args = []
        if yaw is not None:
            args.append(str(yaw))
        if pitch is not None:
            args.append(str(pitch))
        cmd = "look" + (" " + " ".join(args) if args else "")
        return await self._call_command(cmd)
    
    async def say(self, message: str) -> Dict:
        """发送聊天"""
        return await self._call_command(f"say {message}")
    
    async def mine(self, block: str = "stone") -> Dict:
        """挖掘"""
        return await self._call_command(f"mine {block}")
    
    async def craft(self, item: str, count: int = 1) -> Dict:
        """合成"""
        return await self._call_command(f"craft {item} {count}")
    
    async def stop(self) -> Dict:
        """停止移动"""
        return await self._call_command("stop")
    
    # ==================== 控制状态 ====================
    
    async def set_control_state(self, forward: bool = False, backward: bool = False, 
                                left: bool = False, right: bool = False, 
                                jump: bool = False, sneak: bool = False) -> Dict:
        """
        设置控制状态（持续移动）
        """
        session = await self._get_session()
        url = f"{self.api_url}/control/state"
        data = {
            "forward": forward,
            "backward": backward,
            "left": left,
            "right": right,
            "jump": jump,
            "sneak": sneak
        }
        try:
            async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return await resp.json()
        except Exception as e:
            return {"error": str(e), "success": False}
