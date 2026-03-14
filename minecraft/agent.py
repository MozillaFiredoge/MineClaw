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
        # HTTP API 配置
        api_config = self.config.get('api', {})
        self.api_host = api_config.get('host', 'localhost')
        self.http_port = api_config.get('port', 3005)
        self.api_url = f"http://{self.api_host}:{self.http_port}"
        
        # Voyager 配置
        voyager_config = self.config.get('voyager', {})
        self.skill_library_path = voyager_config.get('skill_library_path', './data/skills.json')
        
        # 初始化客户端
        self.client = MineflayerClient(api_url=self.api_url)
        
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
    
    def execute(self, action_str: str, **kwargs) -> dict:
        """执行动作 - 使用同步 HTTP 请求"""
        import requests
        
        action = action_str.lower().strip()
        parts = action.split()
        action_name = parts[0] if parts else ""
        action_params = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        base_url = self.api_url
        
        try:
            if action_name == "move":
                r = requests.post(f"{base_url}/command", params={"cmd": f"move {action_params or 'forward'}"}, timeout=5)
                return r.json()
            elif action_name == "jump":
                r = requests.post(f"{base_url}/command", params={"cmd": "jump"}, timeout=5)
                return r.json()
            elif action_name == "attack":
                r = requests.post(f"{base_url}/control/attack", timeout=5)
                return r.json()
            elif action_name == "place_block":
                r = requests.post(f"{base_url}/command", params={"cmd": f"place {action_params or 'dirt'}"}, timeout=5)
                return r.json()
            elif action_name == "use_item":
                r = requests.post(f"{base_url}/command", params={"cmd": "use"}, timeout=5)
                return r.json()
            elif action_name == "look":
                r = requests.post(f"{base_url}/command", params={"cmd": f"look {action_params}"}, timeout=5)
                return r.json()
            elif action_name == "craft":
                r = requests.post(f"{base_url}/command", params={"cmd": f"craft {action_params}"}, timeout=5)
                return r.json()
            elif action_name == "mine":
                r = requests.post(f"{base_url}/command", params={"cmd": f"mine {action_params or 'stone'}"}, timeout=5)
                return r.json()
            elif action_name == "say":
                r = requests.post(f"{base_url}/command", params={"cmd": f"say {action_params}"}, timeout=5)
                return r.json()
            elif action_name == "stop":
                r = requests.post(f"{base_url}/command", params={"cmd": "stop"}, timeout=5)
                return r.json()
            else:
                return {"success": False, "error": f"未知动作: {action_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_task(self, task: str, max_steps: int = 100) -> dict:
        """
        运行任务的主循环 (同步版本)
        """
        import requests
        
        print(f"🎮 开始任务: {task}")
        
        for step in range(max_steps):
            print(f"\n--- 步骤 {step + 1}/{max_steps} ---")
            
            # 1. 获取截图 (暂时跳过)
            screenshot_data = None
            # try:
            #     import asyncio
            #     screenshot_data = asyncio.run(self.client.screenshot())
            # except:
            #     pass
            
            # 2. 获取状态 (同步方式)
            try:
                status = requests.get(f"{self.api_url}/status", timeout=5).json()
                inventory = requests.get(f"{self.api_url}/inventory", timeout=5).json()
            except Exception as e:
                print(f"⚠️ 获取状态失败: {e}")
                status = {"error": str(e)}
                inventory = {"items": []}
            
            context = {
                "status": status,
                "inventory": inventory
            }
            print(f"📊 状态: {status}")
            
            # 3. LLM 决策
            decision = self.think(task, screenshot_data, context)
            print(f"🤔 决策: {decision}")
            
            # 4. 解析并执行动作
            action = None
            try:
                import re
                # 尝试提取 JSON 块 (支持多行)
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', decision, re.DOTALL)
                if not json_match:
                    # 尝试直接找 JSON
                    json_match = re.search(r'(\{.*?\})', decision, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(1)
                    action_data = json.loads(json_str)
                    action = action_data.get('action', '')
                    params = action_data.get('params', {})
                    if params:
                        action = f"{action} {params.get('direction', params.get('block', ''))}"
                else:
                    # 提取第一行纯文本
                    lines = [l.strip() for l in decision.split('\n') if l.strip() and not l.strip().startswith('```')]
                    action = lines[0] if lines else ""
            except Exception as e:
                print(f"⚠️ 解析失败: {e}")
                action = decision.strip().split('\n')[0].strip()
                action = decision.strip().split('\n')[0].strip()
            
            # 执行动作
            if action:
                print(f"⚡ 执行: {action}")
                result = self.execute(action)
                print(f"📋 结果: {result}")
                
                # 检查是否完成任务
                # 让 LLM 判断是否需要继续
                check_context = {
                    "status": status,
                    "inventory": inventory,
                    "last_action": action,
                    "last_result": result,
                    "original_task": task
                }
                
                # 让 LLM 判断任务是否完成
                check_prompt = f"""
任务: {task}
刚才执行的动作: {action}
执行结果: {result}
当前状态: {status}
当前物品栏: {inventory}

请判断任务是否已经完成。如果完成了，返回:
```json
{{"action": "finished", "completed": true, "reason": "原因"}}
```

如果还没完成，需要继续，返回:
```json
{{"action": "下一步动作", "reason": "为什么"}}
```

只返回 JSON，不要其他内容。
"""
                check_decision = self.think(check_prompt, None, check_context)
                print(f"🔄 检查任务状态: {check_decision}")
                
                # 检查是否完成
                try:
                    import re
                    check_match = re.search(r'```json\s*(\{.*?\})\s*```', check_decision, re.DOTALL)
                    if not check_match:
                        check_match = re.search(r'(\{.*?\})', check_decision, re.DOTALL)
                    if check_match:
                        check_data = json.loads(check_match.group(1))
                        if check_data.get('completed', False):
                            print(f"✅ 任务完成: {check_data.get('reason', '')}")
                            return {"success": True, "steps": step + 1, "reason": check_data.get('reason', '')}
                except:
                    pass
            
            # 最多执行 max_steps 次
            if step >= max_steps - 1:
                print(f"⚠️ 达到最大步数 {max_steps}，停止")
                break
            
        return {"success": True, "steps": step + 1}


def create_agent(config_path: str = None) -> MinecraftAgent:
    """创建 Agent 实例的工厂函数"""
    return MinecraftAgent(config_path)
