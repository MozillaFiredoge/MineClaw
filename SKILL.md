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

# 发号施令 - 给高层次任务，而不是具体动作
agent.run_task("建一个房子")      # 让 Agent 自己规划和执行
agent.run_task("去挖10块石头")    # Agent 会自己判断怎么挖
agent.run_task("杀掉附近的僵尸")  # Agent 会自己找僵尸并攻击
agent.run_task("探索周围环境")    # Agent 会自己探索
```

**注意：** 是 `run_task("任务")` 而不是 `execute("move forward")`

---

## 可用任务命令

| 命令 | 说明 |
|------|------|
| `建一个房子` | 自动收集材料并建造房子 |
| `去挖石头` | 挖掘指定数量石头 |
| `去砍树` | 找到树并砍倒 |
| `杀僵尸` | 找到并击杀僵尸 |
| `烤食物` | 找动物、杀、烤熟 |
| `找钻石` | 探索矿井寻找钻石 |

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

## 工作流程

```
我: "建一个房子"

Agent:
  1. 获取截图 + 状态
  2. LLM 分析场景 → 决策
  3. 执行动作 (砍树 → 收集木头 → 造木块 → 放置)
  4. 循环直到任务完成
  5. 返回结果给我

我: 验收结果
```

---

## 注意事项

1. **用 run_task() 而不是 execute()** - 任务级别的命令
2. **不要用 curl 直接访问 Mineflayer** - 那是 Agent 的工作
3. **需要先启动 Bot** 才能发指令
