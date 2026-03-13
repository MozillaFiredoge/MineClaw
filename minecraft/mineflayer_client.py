"""
Mineflayer 客户端
通过 Mineflayer (Node.js) 与 Minecraft 通信
"""

import asyncio
import json
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import threading
import socket


class MineflayerClient:
    """
    Mineflayer 客户端
    
    通过子进程启动 Mineflayer Bot 并通过 stdin/stdout 通信
    或通过 HTTP API 通信
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 25565,
        username: str = "OpenClawBot",
        bot_path: Optional[Path] = None
    ):
        self.host = host
        self.port = port
        self.username = username
        self.bot_path = bot_path or Path(__file__).parent.parent / "scripts" / "start_bot.js"
        
        self.process: Optional[subprocess.Popen] = None
        self.connected = False
        self.api_port = 3000  # Bot HTTP API 端口
        
    def start(self) -> bool:
        """启动 Mineflayer Bot"""
        if not self.bot_path.exists():
            print(f"Bot script not found: {self.bot_path}")
            return False
            
        try:
            # 启动 Node.js 进程
            self.process = subprocess.Popen(
                ["node", str(self.bot_path), 
                 "--host", self.host,
                 "--port", str(self.port),
                 "--username", self.username,
                 "--api-port", str(self.api_port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True
            )
            
            # 等待连接
            time.sleep(2)
            
            if self.process.poll() is None:
                self.connected = True
                print(f"Mineflayer bot started: {self.username}@{self.host}:{self.port}")
                return True
            else:
                print("Failed to start Mineflayer bot")
                return False
                
        except Exception as e:
            print(f"Error starting bot: {e}")
            return False
            
    def stop(self):
        """停止 Bot"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.connected = False
            print("Mineflayer bot stopped")
            
    def send_command(self, command: str) -> Dict[str, Any]:
        """
        发送命令到 Bot
        
        Args:
            command: 命令 (JSON 格式)
            
        Returns:
            响应
        """
        if not self.connected:
            return {"error": "Not connected"}
            
        try:
            # 通过 HTTP API 发送命令
            import urllib.request
            import urllib.parse
            
            url = f"http://localhost:{self.api_port}/command"
            data = urllib.parse.urlencode({"cmd": command}).encode()
            
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode())
                
        except Exception as e:
            return {"error": str(e)}
            
    def get_status(self) -> Dict[str, Any]:
        """获取 Bot 状态"""
        return self.send_command("status")
        
    def get_inventory(self) -> List[Dict]:
        """获取物品栏"""
        result = self.send_command("inventory")
        return result.get("items", [])
        
    def get_position(self) -> Dict[str, float]:
        """获取位置"""
        result = self.send_command("position")
        return result.get("position", {"x": 0, "y": 0, "z": 0})
        
    def move(self, direction: str, duration: float = 1.0):
        """移动"""
        self.send_command(f"move {direction} {duration}")
        
    def jump(self):
        """跳跃"""
        self.send_command("jump")
        
    def attack(self):
        """攻击"""
        self.send_command("attack")
        
    def place_block(self, x: int, y: int, z: int, block: str):
        """放置方块"""
        self.send_command(f"place {x} {y} {z} {block}")
        
    def use_item(self, slot: Optional[int] = None):
        """使用物品"""
        if slot:
            self.send_command(f"use {slot}")
        else:
            self.send_command("use")
            
    def craft(self, recipe: str, count: int = 1):
        """合成"""
        self.send_command(f"craft {recipe} {count}")
        
    def look(self, yaw: float, pitch: float):
        """调整视角"""
        self.send_command(f"look {yaw} {pitch}")
        
    def chat(self, message: str):
        """发送聊天消息"""
        self.send_command(f"chat {message}")
        
    def screenshot(self) -> Optional[str]:
        """截图"""
        result = self.send_command("screenshot")
        return result.get("path")


class MCAPIClient:
    """
    Minecraft RCON 或 HTTP API 客户端
    
    用于直接与 Minecraft 服务端通信
    """
    
    def __init__(self, host: str = "localhost", port: int = 25575, password: str = ""):
        self.host = host
        self.port = port
        self.password = password
        self.socket: Optional[socket.socket] = None
        
    def connect(self) -> bool:
        """连接 RCON"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            
            # RCON 认证
            auth_packet = self._create_packet(3, self.password)
            self.socket.send(auth_packet)
            response = self.socket.recv(4096)
            
            return True
        except Exception as e:
            print(f"RCON connection failed: {e}")
            return False
            
    def disconnect(self):
        """断开连接"""
        if self.socket:
            self.socket.close()
            self.socket = None
            
    def _create_packet(self, request_id: int, packet_type: int, payload: str) -> bytes:
        """创建 RCON 数据包"""
        import struct
        
        data = payload.encode('utf-8')
        packet = struct.pack('<ii', request_id, packet_type) + data + b'\x00\x00'
        length = struct.pack('<i', len(packet))
        return length + packet
        
    def execute(self, command: str) -> str:
        """执行命令"""
        if not self.socket:
            return "Not connected"
            
        try:
            packet = self._create_packet(1, 2, command)
            self.socket.send(packet)
            
            response = self.socket.recv(4096)
            # 解析响应...
            return response.decode('utf-8', errors='ignore')
        except Exception as e:
            return f"Error: {e}"
            
    def get_players(self) -> List[str]:
        """获取在线玩家"""
        result = self.execute("list")
        # 解析玩家列表
        return []
        
    def get_world_info(self) -> Dict[str, Any]:
        """获取世界信息"""
        return {
            "dimension": self.execute("execute if dimension _"),
            "time": self.execute("time query day"),
            "weather": self.execute("weather query")
        }


if __name__ == "__main__":
    # 测试
    client = MineflayerClient()
    # client.start()
    # time.sleep(5)
    # client.stop()
    print("MineflayerClient module loaded")
