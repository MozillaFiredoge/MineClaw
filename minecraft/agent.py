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
        支持终身学习：完成任务后存入技能库（可复用代码），下次直接调用
        """
        import requests
        
        print(f"🎮 开始任务: {task}")
        
        # ========== 检查技能库 ==========
        # 先检查是否已经学习过这个任务或类似的
        existing_skill = self.skill_library.find_similar(task)
        if existing_skill and existing_skill.code:
            print(f"📚 发现已学习技能: {existing_skill.name}")
            print(f"   描述: {existing_skill.description}")
            print(f"   成功率: {existing_skill.success_rate:.1%}")
            
            # 执行保存的技能代码
            skill_code = existing_skill.code
            print(f"📋 执行技能代码:\n{skill_code}")
            
            try:
                # 使用 exec 执行技能代码（需要安全上下文）
                # 这里简化为执行动作序列
                actions = skill_code.split('\n')
                for action in actions:
                    action = action.strip()
                    if action and not action.startswith('#'):
                        print(f"⚡ 执行: {action}")
                        result = self.execute(action)
                        print(f"📋 结果: {result}")
                
                # 更新技能统计
                self.skill_library.update_stats(existing_skill.name, True)
                
                return {
                    "success": True, 
                    "skill_name": existing_skill.name,
                    "reason": f"使用已学习的技能 '{existing_skill.name}'",
                    "from_skill_library": True
                }
            except Exception as e:
                print(f"⚠️ 执行技能失败: {e}")
                self.skill_library.update_stats(existing_skill.name, False)
                # 继续尝试重新学习
        
        # ========== 没有技能，重新学习 ==========
        action_history = []  # 记录执行过的动作
        
        for step in range(max_steps):
            print(f"\n--- 步骤 {step + 1}/{max_steps} ---")
            
            # 1. 获取增强后的状态（包含附近方块、实体等）
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
            
            # 打印关键信息
            print(f"📍 位置: {status.get('position', {})}")
            print(f"❤️ 健康: {status.get('health', 0)}/{status.get('food', 0)}")
            print(f"📦 物品数: {len(inventory.get('items', []))}")
            
            # 显示附近实体（如果有）
            nearby_entities = status.get('nearbyEntities', [])
            if nearby_entities:
                print(f"👾 附近实体: {nearby_entities[:5]}")
            
            # 显示附近方块（简化显示）
            nearby_blocks = status.get('nearbyBlocks', [])
            if nearby_blocks:
                block_types = list(set(b['name'] for b in nearby_blocks[:10]))
                print(f"🧱 附近方块: {block_types}")
            
            # 2. LLM 决策（无截图，使用文本状态）
            decision = self.think(task, None, context)
            print(f"🤔 决策: {decision}")
            
            # 3. 解析并执行动作
            action = None
            try:
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', decision, re.DOTALL)
                if not json_match:
                    json_match = re.search(r'(\{.*?\})', decision, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(1)
                    action_data = json.loads(json_str)
                    action = action_data.get('action', '')
                    params = action_data.get('params', {})
                    if params:
                        action = f"{action} {params.get('direction', params.get('block', ''))}"
                else:
                    lines = [l.strip() for l in decision.split('\n') if l.strip() and not l.strip().startswith('```')]
                    action = lines[0] if lines else ""
            except Exception as e:
                print(f"⚠️ 解析失败: {e}")
                action = decision.strip().split('\n')[0].strip()
            
            # 执行动作并记录
            if action:
                print(f"⚡ 执行: {action}")
                result = self.execute(action)
                print(f"📋 结果: {result}")
                action_history.append(action)
                
                # 4. 检查是否完成任务
                check_context = {
                    "status": status,
                    "inventory": inventory,
                    "last_action": action,
                    "last_result": result,
                    "original_task": task
                }
                
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
                            reason = check_data.get('reason', '')
                            print(f"✅ 任务完成: {reason}")
                            
                            # ========== 存入技能库（可复用代码）==========
                            if action_history:
                                # 生成可复用的技能代码
                                skill_code = self._generate_skill_code(task, action_history, context)
                                print(f"📚 存入技能库: {task}")
                                print(f"   代码:\n{skill_code}")
                                
                                from .voyager import Skill
                                skill = Skill(
                                    name=task,
                                    description=f"完成任务 '{task}' 的技能",
                                    code=skill_code,
                                    success_rate=1.0
                                )
                                self.skill_library.add(skill)
                            
                            return {
                                "success": True, 
                                "steps": step + 1, 
                                "reason": reason,
                                "skill_saved": True,
                                "action_sequence": action_history
                            }
                except:
                    pass
            
            # 最多执行 max_steps 次
            if step >= max_steps - 1:
                print(f"⚠️ 达到最大步数 {max_steps}，停止")
                break
            
        return {"success": True, "steps": step + 1, "action_sequence": action_history}

    def _generate_skill_code(self, task: str, action_history: list, context: dict) -> str:
        """
        生成可复用的技能代码
        
        不同于简单的动作序列，生成的代码包含：
        1. 检查条件（什么情况下使用这个技能）
        2. 执行逻辑（具体的动作步骤）
        3. 验证逻辑（如何判断成功）
        """
        from datetime import datetime
        
        status = context.get('status', {})
        task_lower = task.lower()
        
        code_parts = []
        code_parts.append(f"# Skill: {task}")
        code_parts.append(f"# Generated: {datetime.now().isoformat()}")
        code_parts.append("")
        code_parts.append("# === 检查条件 ===")
        
        # 根据任务类型生成检查条件
        if "挖" in task and "石头" in task:
            code_parts.append("def check(context):")
            code_parts.append("    status = context.get('status', {})")
            code_parts.append("    nearby = status.get('nearbyBlocks', [])")
            code_parts.append("    return any(b['name'] == 'minecraft:stone' for b in nearby)")
        elif "挖" in task and "木头" in task:
            code_parts.append("def check(context):")
            code_parts.append("    status = context.get('status', {})")
            code_parts.append("    nearby = status.get('nearbyBlocks', [])")
            code_parts.append("    return any('log' in b['name'] for b in nearby)")
        elif "杀" in task and "僵尸" in task:
            code_parts.append("def check(context):")
            code_parts.append("    status = context.get('status', {})")
            code_parts.append("    entities = status.get('nearbyEntities', [])")
            code_parts.append("    return any(e.get('name') == 'zombie' for e in entities)")
        else:
            code_parts.append("def check(context):")
            code_parts.append("    return True")
        
        code_parts.append("")
        code_parts.append("# === 执行动作 ===")
        for i, action in enumerate(action_history, 1):
            code_parts.append(f"# 步骤 {i}: {action}")
        
        code_parts.append("def execute(agent):")
        for action in action_history:
            code_parts.append(f"    agent.execute('{action}')")
        
        code_parts.append("")
        code_parts.append("# === 验证成功 ===")
        code_parts.append("def verify(context):")
        
        if "挖" in task and "石头" in task:
            code_parts.append("    inventory = context.get('inventory', {})")
            code_parts.append("    items = inventory.get('items', [])")
            code_parts.append("    stone = sum(i.get('count',0) for i in items if 'stone' in i.get('name',''))")
            code_parts.append("    return stone >= 10")
        elif "挖" in task and "木头" in task:
            code_parts.append("    inventory = context.get('inventory', {})")
            code_parts.append("    items = inventory.get('items', [])")
            code_parts.append("    wood = sum(i.get('count',0) for i in items if 'log' in i.get('name',''))")
            code_parts.append("    return wood >= 10")
        else:
            code_parts.append("    return True")
        
        return "\n".join(code_parts)


def create_agent(config_path: str = None) -> MinecraftAgent:
    """创建 Agent 实例的工厂函数"""
    return MinecraftAgent(config_path)
