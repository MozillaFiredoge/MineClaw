# MineClaw SKILL.md

> OpenClaw Minecraft Agent 技能接口

## 架构

```
OpenClaw (我)  →  Agent (Python)  →  Mineflayer Bot (Node.js)  →  Minecraft 服务器
    发号施令         执行任务            HTTP API 控制               游戏执行
```

**职责分工：**
- **OpenClaw (我)**: 只负责给 Agent 下**高层次任务命令**，验收结果
- **Agent**: 接收任务，调用 LLM 决策，自动执行动作直到完成
- **Mineflayer**: 实际在 Minecraft 中执行动作（headless 模式）

---

## 使用方法

### 1. 启动 Bot（在你电脑上）
```bash
cd minecraft-agent
node scripts/start_bot.js
```

### 2. 创建 Agent 并发号施令
```python
from minecraft.agent import create_agent

# 创建 Agent
agent = create_agent()

# 发号施令 - 给高层次任务
agent.run_task("建一个房子")
agent.run_task("去挖10块石头")
agent.run_task("杀掉附近的僵尸")
```

---

## 增强的 Status 信息

`/status` 端点现在返回丰富的环境信息：

```json
{
  "health": 20,
  "food": 20,
  "position": {"x": 0, "y": 64, "z": 0},
  "dimension": "minecraft:overworld",
  "gameMode": "survival",
  "heldItem": {"name": "minecraft:iron_pickaxe", "count": 1},
  "time": {"age": 1000, "timeOfDay": 6000, "isDay": true},
  "weather": {"isRaining": false, "isThunder": false},
  "nearbyEntities": [
    {"name": "zombie", "position": {"x": 5, "y": 64, "z": 3}, "distance": 5}
  ],
  "nearbyBlocks": [
    {"name": "minecraft:stone", "position": {"x": 1, "y": 63, "z": 0}, "hardness": 1.5}
  ],
  "version": "1.20.4"
}
```

**新增字段：**
- `heldItem` - 当前手持物品
- `time` - 游戏时间
- `weather` - 天气状况
- `nearbyEntities` - 附近实体（玩家、动物、怪物等），最多20个
- `nearbyBlocks` - 附近方块（4格范围内），最多50个
- `version` - 游戏版本

---

## Skill（技能）系统

Skill 是**可复用的代码**，而非简单的动作序列：

```python
# Skill 示例：挖石头
# === 检查条件 ===
def check(context):
    status = context.get('status', {})
    nearby = status.get('nearbyBlocks', [])
    return any(b['name'] == 'minecraft:stone' for b in nearby)

# === 执行动作 ===
def execute(agent):
    agent.execute('move forward')
    agent.execute('attack')

# === 验证成功 ===
def verify(context):
    inventory = context.get('inventory', {})
    items = inventory.get('items', [])
    stone = sum(i.get('count',0) for i in items if 'stone' in i.get('name',''))
    return stone >= 10
```

**特点：**
1. **检查条件** - 判断当前环境是否适合使用该技能
2. **执行逻辑** - 具体的动作步骤
3. **验证逻辑** - 如何判断任务成功完成

---

## 配置 (config.yml)

```yaml
llm:
  model: "Qwen/Qwen3-VL-235B-A22B-Instruct"
  endpoint: "https://api.siliconflow.cn/v1"
  api_key: "${OPENAI_API_KEY}"

minecraft:
  host: java.applemc.fun
  port: 25565
  username: MineClawBot

api:
  host: "localhost"
  port: 3005
```

---

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/status` | GET | 获取增强后的游戏状态（包含附近方块、实体等） |
| `/inventory` | GET | 获取物品栏 |
| `/command?cmd=<action>` | POST | 执行动作 |
| `/control/state` | POST | 设置移动控制状态 |
| `/control/attack` | POST | 攻击 |

**已废弃：**
- `/screenshot` - headless 模式无截图
- `/render` - headless 模式无渲染

---

## 工作流程

```
我: "去挖10块石头"

Agent:
  1. 获取 status（包含附近方块信息）
  2. LLM 分析场景 → 决策
  3. 执行动作
  4. 检查物品栏判断是否完成
  5. 成功则存入技能库（生成可复用代码）
  6. 返回结果

我: 验收结果
```

---

## 注意事项

1. **用 run_task()** - 任务级别的命令，不是具体动作
2. **headless 模式** - 没有截图，使用文本状态进行决策
3. **Skill 是代码** - 不是动作序列，包含检查/执行/验证逻辑
