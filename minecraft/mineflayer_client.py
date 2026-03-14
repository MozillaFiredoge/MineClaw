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
    
    def __init__(self, api_url: str = "http://localhost:3000", screenshot_dir: str = "./screenshots"):
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
    
    # ==================== 核心功能 ====================
    
    async def get_status(self) -> Dict[str, Any]:
        """
        获取 Bot 状态
        TODO: 完成状态获取
        """
        result = await self._call_api("status")
        # 增强状态信息
        if "success" not in result:
            result["success"] = "error" not in result
        return result
    
    async def get_inventory(self) -> Dict[str, Any]:
        """
        获取物品栏
        """
        result = await self._call_api("inventory")
        # 规范化物品数据
        if result.get("success"):
            items = result.get("items", [])
            result["items"] = [
                {
                    "slot": item.get("slot"),
                    "name": item.get("name", ""),
                    "count": item.get("count", 1),
                    "metadata": item.get("metadata", 0),
                    "displayName": item.get("displayName", item.get("name", ""))
                }
                for item in items
            ]
        return result
    
    async def get_position(self) -> Dict[str, Any]:
        """
        获取 Bot 位置
        """
        result = await self._call_api("position")
        if result.get("success"):
            pos = result.get("position", {})
            return {
                "success": True,
                "x": pos.get("x", 0),
                "y": pos.get("y", 0),
                "z": pos.get("z", 0),
                "yaw": pos.get("yaw", 0),
                "pitch": pos.get("pitch", 0),
                "dimension": pos.get("dimension", "overworld")
            }
        return result
    
    async def get_entities(self) -> List[Dict]:
        """
        获取周围实体
        """
        result = await self._call_api("entities")
        if result.get("success"):
            return result.get("entities", [])
        return []
    
    async def get_blocks(self, x: int, y: int, z: int, width: int = 1, height: int = 1, depth: int = 1) -> List[Dict]:
        """
        获取指定区域的方块
        """
        result = await self._call_api(f"blocks/{x}/{y}/{z}?width={width}&height={height}&depth={depth}")
        if result.get("success"):
            return result.get("blocks", [])
        return []
    
    # ==================== 动作控制 ====================
    
    async def chat(self, message: str) -> Dict:
        """
        发送聊天消息
        """
        return await self._call_api("chat", method="POST", data={"message": message})
    
    async def move(self, direction: str = "forward", duration: float = 1.0) -> Dict:
        """
        移动
        direction: forward, backward, left, right
        duration: 持续时间(秒)
        """
        return await self._call_api("move", method="POST", data={
            "direction": direction,
            "duration": duration
        })
    
    async def jump(self) -> Dict:
        """
        跳跃
        """
        return await self._call_api("jump", method="POST")
    
    async def attack(self, entityId: Optional[int] = None) -> Dict:
        """
        攻击实体
        """
        if entityId is not None:
            return await self._call_api("attack", method="POST", data={"entityId": entityId})
        return await self._call_api("attack", method="POST")
    
    async def place_block(self, position: Dict[str, int], block: str = "stone") -> Dict:
        """
        放置方块
        position: {"x": 0, "y": 0, "z": 0}
        block: 方块名称
        """
        return await self._call_api("place", method="POST", data={
            "position": position,
            "block": block
        })
    
    async def use_item(self, slot: int) -> Dict:
        """
        使用物品栏中的物品
        """
        return await self._call_api("use", method="POST", data={"slot": slot})
    
    async def equip(self, item: str, destination: str = "hand") -> Dict:
        """
        装备物品
        destination: hand, head, chest, legs, feet
        """
        return await self._call_api("equip", method="POST", data={
            "item": item,
            "destination": destination
        })
    
    async def craft(self, recipe: str, count: int = 1) -> Dict:
        """
        合成物品
        """
        return await self._call_api("craft", method="POST", data={
            "recipe": recipe,
            "count": count
        })
    
    # ==================== 截图功能 ====================
    
    async def screenshot(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        截图
        TODO: 需要实现截图功能
        
        返回:
        {
            "success": true,
            "path": "screenshots/xxx.png",
            "base64": "data:image/png;base64,..."
        }
        """
        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        # 确保文件名有 .png 后缀
        if not filename.endswith(".png"):
            filename += ".png"
        
        filepath = self.screenshot_dir / filename
        
        try:
            # 调用截图 API
            result = await self._call_api("screenshot")
            
            if result.get("success") and result.get("base64"):
                # 保存 base64 图片
                image_data = result["base64"]
                # 移除 data:image/png;base64, 前缀
                if "," in image_data:
                    image_data = image_data.split(",")[1]
                
                # 解码并保存
                image_bytes = base64.b64decode(image_data)
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
                
                return {
                    "success": True,
                    "path": str(filepath),
                    "filename": filename,
                    "base64": result["base64"]
                }
            else:
                # API 不支持截图，返回错误信息
                return {
                    "success": False,
                    "error": result.get("error", "Screenshot API not available"),
                    "path": str(filepath),
                    "filename": filename
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": str(filepath),
                "filename": filename
            }
    
    async def screenshot_base64(self) -> Optional[str]:
        """
        获取截图的 base64 编码（用于 LLM 视觉理解）
        TODO: 需要实现
        
        返回 base64 字符串或 None
        """
        result = await self.screenshot()
        if result.get("success"):
            return result.get("base64")
        return None
    
    # ==================== 便捷方法 ====================
    
    async def connect(self) -> Dict:
        """
        连接服务器
        TODO: 需要实现
        
        返回连接状态
        """
        return await self._call_api("connect", method="POST")
    
    async def disconnect(self) -> Dict:
        """
        断开连接
        """
        return await self._call_api("disconnect", method="POST")
    
    async def is_connected(self) -> bool:
        """
        检查是否连接到服务器
        """
        status = await self.get_status()
        return status.get("success", False) and status.get("connected", False)
    
    async def wait_for_connection(self, timeout: float = 30.0, check_interval: float = 1.0) -> bool:
        """
        等待连接到服务器
        """
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            if await self.is_connected():
                return True
            await asyncio.sleep(check_interval)
        return False
    
    # ==================== 实用工具 ====================
    
    async def look_at(self, x: float, y: float, z: float) -> Dict:
        """
        看向指定位置
        """
        return await self._call_api("look", method="POST", data={
            "x": x, "y": y, "z": z
        })
    
    async def set_hotbar_slot(self, slot: int) -> Dict:
        """
        设置主手物品栏 slot (0-8)
        """
        return await self._call_api("hotbar", method="POST", data={"slot": slot})
    
    async def drop_item(self, count: int = -1) -> Dict:
        """
        丢弃物品
        count: -1 表示全部
        """
        return await self._call_api("drop", method="POST", data={"count": count})
    
    async def consume(self) -> Dict:
        """
        消耗/吃/喝当前手持物品
        """
        return await self._call_api("consume", method="POST")
    
    async def open_block(self, x: int, y: int, z: int) -> Dict:
        """
        打开方块 (箱子、箱子等)
        """
        return await self._call_api(f"open_block/{x}/{y}/{z}", method="POST")
    
    async def open_entity(self, entityId: int) -> Dict:
        """
        打开实体界面 (村民交易等)
        """
        return await self._call_api(f"open_entity/{entityId}", method="POST")


# 便捷函数
def create_client(api_url: str = "http://localhost:3000", **kwargs) -> MineflayerClient:
    """创建 Mineflayer 客户端"""
    return MineflayerClient(api_url=api_url, **kwargs)
