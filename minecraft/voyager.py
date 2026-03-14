"""
Minecraft Voyager Agent - 终身学习版
像 Voyager 一样：视觉理解 → LLM决策 → 动作执行 → 反思学习
"""

import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Skill:
    """学会的技能"""
    name: str
    description: str
    code: str  # 可执行的代码或动作序列
    success_rate: float = 0.0
    attempts: int = 0
    successes: int = 0
    created_at: str = ""
    last_used: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class SkillLibrary:
    """技能库 - 存储和管理学到的技能"""
    
    def __init__(self, storage_path: str = "./skills"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.skills: Dict[str, Skill] = {}
        self.load()
        
    def add(self, skill: Skill):
        """添加或更新技能"""
        self.skills[skill.name] = skill
        self.save()
        
    def get(self, name: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(name)
    
    def list_skills(self) -> List[Skill]:
        """列出所有技能"""
        return list(self.skills.values())
    
    def update_stats(self, name: str, success: bool):
        """更新技能统计"""
        if name in self.skills:
            skill = self.skills[name]
            skill.attempts += 1
            if success:
                skill.successes += 1
            skill.success_rate = skill.successes / skill.attempts if skill.attempts > 0 else 0
            skill.last_used = datetime.now().isoformat()
            self.save()
            
    def save(self):
        """保存到文件"""
        data = {name: asdict(skill) for name, skill in self.skills.items()}
        with open(self.storage_path / "library.json", "w") as f:
            json.dump(data, f, indent=2)
            
    def load(self):
        """从文件加载"""
        path = self.storage_path / "library.json"
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                self.skills = {name: Skill(**s) for name, s in data.items()}


class MinecraftVoyager:
    """
    Minecraft Voyager Agent
    
    核心循环:
    1. 观察 - 截图获取游戏画面
    2. 思考 - LLM 决策下一步动作
    3. 执行 - 控制 Minecraft 做动作
    4. 反思 - 成功? 存入技能库; 失败? 反思改进
    """
    
    def __init__(
        self,
        api_url: str = "http://localhost:3000",
        skills_path: str = "./skills"
    ):
        self.api_url = api_url
        self.skill_library = SkillLibrary(skills_path)
        
        # 当前任务状态
        self.current_task = ""
        self.task_history: List[Dict] = []  # 任务执行历史
        self.max_retries = 3
        
    def _call_api(self, endpoint: str) -> Dict:
        """调用 Bot HTTP API"""
        import urllib.request
        try:
            url = f"{self.api_url}/{endpoint}"
            with urllib.request.urlopen(url, timeout=10) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            return {"error": str(e)}
            
    def observe(self) -> Dict[str, Any]:
        """
        观察 - 获取游戏状态
        """
        status = self._call_api("status")
        inventory = self._call_api("inventory")
        
        # 截图
        screenshot_result = self._call_api("screenshot")
        
        return {
            "status": status,
            "inventory": inventory,
            "screenshot": screenshot_result,
            "timestamp": time.time()
        }
        
    async def think(self, observation: Dict, task: str) -> Dict[str, Any]:
        """
        思考 - LLM 决策
        
        这里需要接入 OpenClaw 的 LLM!
        """
        # 构建 prompt
        prompt = f"""
你是一个 Minecraft AI Agent (Voyager 风格)。

当前任务: {task}

游戏状态:
{json.dumps(observation.get('status', {}), indent=2)}

物品栏:
{json.dumps(observation.get('inventory', {}), indent=2)}

技能库:
{json.dumps([s.name for s in self.skill_library.list_skills()], indent=2)}

任务历史:
{json.dumps(self.task_history[-3:], indent=2)}

请决定下一步动作。
动作格式 (JSON):
{{
  "action": "动作名",
  "params": {{...}},
  "reasoning": "为什么这么做"
}}

可用动作:
- move(direction, duration) - 移动
- jump() - 跳跃  
- attack(target) - 攻击/挖掘
- place_block(position, block) - 放置方块
- craft(recipe, count) - 合成
- use_item(slot) - 使用物品
- chat(message) - 发送聊天(执行命令)

Respond ONLY with JSON, no other text.
"""
        
        # TODO: 接入 OpenClaw LLM
        # 现在返回默认动作
        return {
            "action": "move",
            "params": {"direction": "forward", "duration": 1.0},
            "reasoning": "探索环境"
        }
        
    def execute(self, action: str, params: Dict) -> Dict:
        """
        执行动作
        """
        # 构建命令
        if action == "move":
            cmd = f"move {params.get('direction', 'forward')} {params.get('duration', 1)}"
        elif action == "jump":
            cmd = "jump"
        elif action == "attack":
            target = params.get("target", "")
            cmd = f"attack {target}" if target else "attack"
        elif action == "place_block":
            pos = params.get("position", {"x": 0, "y": 0, "z": 0})
            block = params.get("block", "stone")
            cmd = f"place {pos['x']} {pos['y']} {pos['z']} {block}"
        elif action == "craft":
            cmd = f"craft {params.get('recipe', '')} {params.get('count', 1)}"
        elif action == "use_item":
            cmd = f"use {params.get('slot', '')}"
        elif action == "chat":
            cmd = f"chat {params.get('message', '')}"
        else:
            cmd = action
            
        result = self._call_api(f"command?cmd={cmd}")
        
        # 记录执行
        self.task_history.append({
            "action": action,
            "params": params,
            "result": result,
            "timestamp": time.time()
        })
        
        return result
        
    def reflect(self, task: str, success: bool, details: str = "") -> str:
        """
        反思 - 任务完成/失败后的复盘
        """
        if success:
            # 成功 - 可能学到了新技能
            reflection = f"任务'{task}'成功完成！"
            
            # 检查是否应该存入技能库
            if len(self.task_history) > 5:
                # 从历史中提取模式，存入技能库
                skill = Skill(
                    name=f"task_{task.replace(' ', '_')}",
                    description=f"完成任务: {task}",
                    code=json.dumps(self.task_history[-10:])
                )
                self.skill_library.add(skill)
                reflection += f" 已存入技能库"
        else:
            # 失败 - 分析原因，尝试改进
            reflection = f"任务'{task}'失败: {details}"
            
            # 检查之前的尝试次数
            failures = sum(1 for h in self.task_history if not h.get("success", True))
            if failures >= self.max_retries:
                reflection += " 已达最大重试次数，需要人工介入"
                
        return reflection
        
    async def run_task(self, task: str, max_steps: int = 100) -> bool:
        """
        运行任务 - 主循环
        """
        self.current_task = task
        print(f"🎯 开始任务: {task}")
        
        for step in range(max_steps):
            # 1. 观察
            observation = self.observe()
            
            # 2. 思考
            decision = await self.think(observation, task)
            print(f"  Step {step+1}: {decision.get('action')} - {decision.get('reasoning')}")
            
            # 3. 执行
            result = self.execute(decision["action"], decision.get("params", {}))
            
            # 检查结果
            if "error" in result:
                print(f"  ❌ 执行错误: {result['error']}")
                self.task_history[-1]["success"] = False
                reflection = self.reflect(task, False, result["error"])
                print(f"  💭 {reflection}")
                continue
                
            # 4. 简单检查任务是否完成 (可以更复杂)
            # 这里简化处理 - 检查是否完成
            task_completed = self._check_task_completion(task, observation)
            
            if task_completed:
                reflection = self.reflect(task, True)
                print(f"  ✅ 任务完成! {reflection}")
                return True
                
            # 等待一下
            time.sleep(0.5)
            
        print(f"  ⚠️ 达到最大步数，任务未完成")
        return False
        
    def _check_task_completion(self, task: str, observation: Dict) -> bool:
        """
        检查任务是否完成 - 简单的规则匹配
        """
        inventory = observation.get("inventory", {}).get("items", [])
        item_counts = {}
        for item in inventory:
            name = item.get("name", "")
            count = item.get("count", 1)
            item_counts[name] = item_counts.get(name, 0) + count
            
        task_lower = task.lower()
        
        # 简单规则
        if "挖" in task and "石头" in task:
            return item_counts.get("minecraft:stone", 0) >= 10
        if "挖" in task and "木头" in task:
            return item_counts.get("minecraft:log", 0) >= 10
        if "杀" in task and "僵尸" in task:
            # 需要检查敌怪
            pass
            
        return False


# 便捷函数
def create_voyager(**kwargs) -> MinecraftVoyager:
    return MinecraftVoyager(**kwargs)


if __name__ == "__main__":
    import asyncio
    
    voyager = create_voyager()
    
    async def test():
        # 测试任务
        await voyager.run_task("去挖 10 块石头")
        
    asyncio.run(test())
