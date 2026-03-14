"""
Mineflayer HTTP API 客户端
"""
import base64
import requests
from typing import Optional, Dict, Any


class MineflayerClient:
    """与 Mineflayer HTTP API 交互的客户端"""
    
    def __init__(self, host: str = 'localhost', port: int = 3005):
        self.base_url = f"http://{host}:{port}"
    
    def _get(self, endpoint: str) -> Dict[str, Any]:
        """GET 请求"""
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _post(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """POST 请求"""
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, json=data or {}, timeout=10)
        response.raise_for_status()
        return response.json()
    
    # ============ 状态获取 ============
    
    def get_status(self) -> Dict[str, Any]:
        """获取 bot 状态（生命值、饱食度、坐标等）"""
        return self._get('/status')
    
    def get_inventory(self) -> Dict[str, Any]:
        """获取物品栏"""
        return self._get('/inventory')
    
    def get_chunks(self) -> Dict[str, Any]:
        """获取加载的区块"""
        return self._get('/chunks')
    
    def get_entities(self) -> Dict[str, Any]:
        """获取实体列表"""
        return self._get('/entities')
    
    # ============ 视觉 ============
    
    def screenshot(self) -> bytes:
        """获取游戏截图（返回 bytes）"""
        url = f"{self.base_url}/screenshot"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    
    def get_pov(self) -> str:
        """获取玩家 POV（第一人称视角 URL）"""
        return f"{self.base_url}/render"
    
    # ============ 动作执行 ============
    
    def command(self, cmd: str) -> Dict[str, Any]:
        """执行 Minecraft 命令"""
        return self._post('/command', {'cmd': cmd})
    
    def move(self, direction: str = "forward") -> Dict[str, Any]:
        """
        移动
        direction: forward, backward, left, right
        """
        return self._post('/control/state', {
            'forward': direction == "forward",
            'backward': direction == "backward",
            'left': direction == "left",
            'right': direction == "right"
        })
    
    def stop_move(self) -> Dict[str, Any]:
        """停止移动"""
        return self._post('/control/state', {
            'forward': False,
            'backward': False,
            'left': False,
            'right': False
        })
    
    def jump(self) -> Dict[str, Any]:
        """跳跃"""
        return self._post('/control/state', {'jump': True})
    
    def stop_jump(self) -> Dict[str, Any]:
        """停止跳跃"""
        return self._post('/control/state', {'jump': False})
    
    def attack(self) -> Dict[str, Any]:
        """攻击（点击）"""
        return self._post('/control/attack')
    
    def interact(self, entityId: int) -> Dict[str, Any]:
        """与实体交互"""
        return self._post('/control/interact', {'entityId': entityId})
    
    def place_block(self, block: str, position: Dict[str, int] = None) -> Dict[str, Any]:
        """
        放置方块
        block: 方块名称（如 dirt, stone, wood 等）
        position: 放置位置（可选，默认放置在准星指向的位置）
        """
        data = {'name': block}
        if position:
            data['position'] = position
        return self._post('/blocks/place', data)
    
    def use_item(self, hand: str = "main_hand") -> Dict[str, Any]:
        """
        使用物品
        hand: main_hand, off_hand
        """
        return self._post('/items/use', {'hand': hand})
    
    def drop_item(self, count: int = 1, hand: str = "main_hand") -> Dict[str, Any]:
        """丢弃物品"""
        return self._post('/items/drop', {'count': count, 'hand': hand})
    
    def equip_item(self, item: str, destination: str = "hand") -> Dict[str, Any]:
        """装备物品"""
        return self._post('/items/equip', {'item': item, 'destination': destination})
    
    def craft(self, item: str, count: int = 1) -> Dict[str, Any]:
        """合成物品"""
        return self._post('/craft', {'item': item, 'count': count})
    
    def mine(self, block: str) -> Dict[str, Any]:
        """挖掘方块"""
        return self._post('/mine', {'block': block})
    
    def look(self, yaw: float = None, pitch: float = None) -> Dict[str, Any]:
        """
        视角旋转
        yaw: 水平角度（度）
        pitch: 垂直角度（度）
        """
        data = {}
        if yaw is not None:
            data['yaw'] = yaw
        if pitch is not None:
            data['pitch'] = pitch
        return self._post('/bot/look', data)
    
    def set_yaw(self, yaw: float) -> Dict[str, Any]:
        """设置水平视角"""
        return self.look(yaw=yaw)
    
    def set_pitch(self, pitch: float) -> Dict[str, Any]:
        """设置垂直视角"""
        return self.look(pitch=pitch)
    
    def dig(self, x: int, y: int, z: int) -> Dict[str, Any]:
        """挖掘指定位置"""
        return self._post('/dig', {'x': x, 'y': y, 'z': z})
    
    def say(self, message: str) -> Dict[str, Any]:
        """发送聊天消息"""
        return self.command(f"say {message}")
    
    def whisper(self, player: str, message: str) -> Dict[str, Any]:
        """发送私信"""
        return self.command(f"msg {player} {message}")
    
    # ============ 导航 ============
    
    def navigate_to(self, x: float, y: float, z: float) -> Dict[str, Any]:
        """导航到指定坐标"""
        return self._post('/pathfinder/go', {'x': x, 'y': y, 'z': z})
    
    def stop_navigate(self) -> Dict[str, Any]:
        """停止导航"""
        return self._post('/pathfinder/stop')
    
    # ============ 实体操作 ============
    
    def attack_entity(self, entityId: int) -> Dict[str, Any]:
        """攻击实体"""
        return self._post('/entities/attack', {'entityId': entityId})
    
    def follow_entity(self, entityId: int) -> Dict[str, Any]:
        """跟随实体"""
        return self._post('/entities/follow', {'entityId': entityId})
    
    # ============ 实用工具 ============
    
    def get_block(self, x: int, y: int, z: int) -> Dict[str, Any]:
        """获取指定位置的方块信息"""
        return self._get(f'/blocks/{x}/{y}/{z}')
    
    def get_time(self) -> Dict[str, Any]:
        """获取游戏时间"""
        return self._get('/time')
    
    def set_time(self, time: int) -> Dict[str, Any]:
        """设置游戏时间"""
        return self._post('/time', {'time': time})
    
    def weather(self, type: str = "rain") -> Dict[str, Any]:
        """设置天气"""
        return self._post('/weather', {'type': type})
    
    def give(self, item: str, count: int = 1) -> Dict[str, Any]:
        """给予物品"""
        return self._post('/give', {'item': item, 'count': count})
    
    def teleport(self, x: float, y: float, z: float) -> Dict[str, Any]:
        """传送"""
        return self._post('/teleport', {'x': x, 'y': y, 'z': z})
