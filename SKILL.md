# MineClaw SKILL.md

> OpenClaw Minecraft Agent 技能接口

## 架构

```
OpenClaw (我)  →  Agent (Python)  →  Mineflayer Bot (Node.js)  →  Minecraft 服务器
    发号施令         执行任务            HTTP API 控制               游戏执行
```

**职责分工：**
- **OpenClaw (我)**: 只负责给 Agent 下指令，验收结果
- **Agent**: 接收指令，调用 LLM 决策，操作 Mineflayer
- **Mineflayer**: 实际在 Minecraft 中执行动作

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

# 发号施令
agent.execute('move forward')   # 移动
agent.execute('jump')           # 跳跃
agent.execute('say 你好')       # 聊天
agent.execute('attack')         # 攻击
agent.execute('stop')           # 停止
```

---

## 可用指令

| 指令 | 说明 |
|------|------|
| `move <方向>` | 移动 forward/backward/left/right |
| `jump` | 跳跃 |
| `attack` | 攻击 |
| `say <消息>` | 发送聊天 |
| `stop` | 停止移动 |
| `place <方块>` | 放置方块 |
| `look <yaw> <pitch>` | 视角旋转 |

---

## 配置 (config.yml)

```yaml
llm:
  model: "Qwen/Qwen3-VL-235B-A22B-Instruct"
  endpoint: "https://api.siliconflow.cn/v1"
  api_key: "${OPENAI_API_KEY}"  # 环境变量

minecraft:
  host: java.applemc.fun
  port: 25565
  username: MineClawBot

api:
  port: 3005
```

---

## 注意事项

1. **不要用 curl 直接访问 Mineflayer** - 那是 Agent 的工作
2. **通过 Agent 发号施令** - 我会帮你创建 agent 并执行命令
3. 需要先启动 Bot 才能发指令
