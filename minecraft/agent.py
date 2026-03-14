"""
Minecraft Agent - 基于 LLM 的自主决策 Agent
"""
import os
import json
import base64
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from PIL import Image
from io import BytesIO
import yaml

from .mineflayer_client import MineflayerClient
from .voyager import SkillLibrary


class MinecraftAgent:
    """Minecraft Voyager Agent - 自主学习决策"""
    
    def __init__(self, config_path: str = None):
        # 加载配置
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yml"
        
        with open(config_path, 'r') as f:
            # 支持环境变量替换
            import re
            content = f.read()
            content = re.sub(r'\$\{(\w+)\}', lambda m: os.getenv(m.group(1), ''), content)
            self.config = yaml.safe_load(content)
        
        # LLM 配置
        self.llm_config = self.config.get('llm', {})
        self.model = self.llm_config.get('model', 'gpt-4o-mini')
        self.endpoint = self.llm_config.get('endpoint', 'https://api.openai.com/v1')
        self.api_key = self.llm_config.get('api_key', '')
        self.vision_base64 = self.llm_config.get('vision_base64', True)
        self.max_retries = self.llm_config.get('max_retries', 3)
        
        # Minecraft 配置
        mc_config = self.config.get('minecraft', {})
        self.host = mc_config.get('host', 'java.applemc.fun')
        self.port = mc_config.get('port', 25565)
        self.username = mc_config.get('username', 'MineClaw')
        self.http_port = mc_config.get('http_port', 3005)
        
        # Voyager 配置
        voyager_config = self.config.get('voyager', {})
        self.skill_library_path = voyager_config.get('skill_library_path', './data/skills.json')
        
        # 初始化客户端
        self.client = MineflayerClient(
            host='localhost',
            port=self.http_port
        )
        
        # 初始化技能库
        self.skill_library = SkillLibrary(self.skill_library_path)
        
        # 加载系统提示词
        self.system_prompt = self._load_prompt('system.txt')
        self.action_prompt = self._load_prompt('action.txt')
    
    def _load_prompt(self, filename: str) -> str:
        """加载提示词文件"""
        prompt_path = Path(__file__).parent.parent / 'prompts' / filename
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _encode_image(self, image_data: bytes) -> str:
        """将图片编码为 base64"""
        return base64.b64encode(image_data).decode('utf-8')
    
    def _call_llm(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """调用 LLM API (OpenAI 兼容接口)"""
        url = f"{self.endpoint}/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content']
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"LLM 调用失败: {e}")
                print(f"LLM 调用失败，尝试重试 ({attempt + 1}/{self.max_retries}): {e}")
        
        return ""
    
    def think(self, task: str, screenshot_data: bytes = None, context: dict = None) -> str:
        """
        核心决策方法：根据任务、截图、上下文进行决策
        """
        # 构建消息
        messages = [
            {
                "role": "system",
                "content": f"{self.system_prompt}\n\n{self.action_prompt}"
            }
        ]
        
        # 用户消息
        user_content = []
        
        # 添加任务描述
        user_content.append({
            "type": "text",
            "text": f"任务: {task}"
        })
        
        # 添加截图（如果有）
        if screenshot_data:
            if self.vision_base64:
                # Base64 编码
                image_base64 = self._encode_image(screenshot_data)
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}"
                    }
                })
            else:
                # TODO: 支持 URL 方式
                pass
        
        # 添加上下文（状态、物品栏等）
        if context:
            context_text = json.dumps(context, ensure_ascii=False, indent=2)
            user_content.append({
                "type": "text",
                "text": f"游戏状态:\n{context_text}"
            })
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        # 调用 LLM
        response = self._call_llm(messages)
        return response
    
    def execute(self, action: str, **kwargs) -> dict:
        """执行动作"""
        action = action.lower().strip()
        
        # 解析动作
        parts = action.split()
        action_name = parts[0] if parts else ""
        action_params = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        # 执行对应动作
        if action_name == "move":
            direction = action_params or "forward"
            return self.client.move(direction)
        
        elif action_name == "jump":
            return self.client.jump()
        
        elif action_name == "attack":
            return self.client.attack()
        
        elif action_name == "place_block":
            block = action_params or "dirt"
            return self.client.place_block(block)
        
        elif action_name == "use_item":
            return self.client.use_item()
        
        elif action_name == "look":
            return self.client.look(action_params)
        
        elif action_name == "craft":
            item = action_params
            return self.client.craft(item)
        
        elif action_name == "mine":
            block = action_params or "stone"
            return self.client.mine(block)
        
        elif action_name == "say":
            message = action_params
            return self.client.say(message)
        
        else:
            return {"success": False, "error": f"未知动作: {action_name}"}
    
    def run_task(self, task: str, max_steps: int = 100) -> dict:
        """
        运行任务的主循环
        """
        print(f"🎮 开始任务: {task}")
        
        for step in range(max_steps):
            print(f"\n--- 步骤 {step + 1}/{max_steps} ---")
            
            # 1. 获取截图
            screenshot_data = self.client.screenshot()
            
            # 2. 获取状态
            status = self.client.get_status()
            inventory = self.client.get_inventory()
            
            context = {
                "status": status,
                "inventory": inventory
            }
            
            # 3. LLM 决策
            decision = self.think(task, screenshot_data, context)
            print(f"🤔 决策: {decision}")
            
            # 4. 解析并执行动作
            # 这里可以解析 LLM 返回的动作并执行
            # 简化版本：假设 LLM 返回的是动作名称
            
            # 5. 检查是否完成
            # 可以根据状态判断任务是否完成
            
        return {"success": True, "steps": max_steps}


def create_agent(config_path: str = None) -> MinecraftAgent:
    """创建 Agent 实例的工厂函数"""
    return MinecraftAgent(config_path)
