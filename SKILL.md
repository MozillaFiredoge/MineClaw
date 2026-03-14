# MineClaw SKILL.md

> OpenClaw Minecraft Agent 技能接口

## 角色说明

- **OpenClaw (我)**: 发号施令者，分配任务并验收结果
- **Agent (Python)**: 执行者，调用 HTTP API 控制 Minecraft Bot

## 启动方式

```bash
# 1. 启动 Minecraft Bot (Node.js)
cd minecraft-agent
node scripts/start_bot.js

# 2. 启动 Agent (Python)
cd minecraft-agent
python3 -c "from minecraft.agent import create_agent; agent = create_agent()"
```

---

## 我如何发号施令

我通过 HTTP API 控制 Agent，API 基础地址：`http://localhost:3005`

### 核心端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/status` | 获取 Bot 状态 |
| GET | `/inventory` | 获取物品栏 |
| GET | `/screenshot` | 获取截图 |
| POST | `/command?cmd=<动作>` | 执行动作 |

### 可用动作

```
move <方向>      # forward, backward, left, right
jump             # 跳跃
attack           # 攻击/挖掘
place <方块>     # 放置方块 (dirt, stone, wood 等)
use              # 使用物品
look <yaw> <pitch>  # 视角旋转
say <消息>       # 聊天
stop             # 停止移动
```

---

## 任务流程

### 我分配任务给 Agent

```
我: "去挖10块石头"

Agent 执行:
  1. curl http://localhost:3005/screenshot  (获取截图)
  2. curl http://localhost:3005/status       (获取状态)
  3. curl http://localhost:3005/inventory    (获取物品栏)
  4. 分析 → 决策 → 执行动作
  5. curl -X POST "http://localhost:3005/command?cmd=move forward"
  6. curl -X POST http://localhost:3005/control/attack
  7. 循环直到任务完成

Agent 返回结果给我
我: 验收结果 ("石头够了，任务完成")
```

---

## 我直接用 curl 控制

```bash
# 获取状态
curl http://localhost:3005/status
# 返回: {"health":20,"food":20,"position":{"x":0,"y":0,"z":0},"inventory":[]}

# 移动
curl -X POST "http://localhost:3005/command?cmd=move forward"
curl -X POST "http://localhost:3005/command?cmd=move left"

# 跳跃
curl -X POST "http://localhost:3005/command?cmd=jump"

# 攻击/挖掘
curl -X POST http://localhost:3005/control/attack

# 放置方块
curl -X POST "http://localhost:3005/command?cmd=place dirt"

# 聊天
curl -X POST "http://localhost:3005/command?cmd=say Hello World"

# 停止
curl -X POST "http://localhost:3005/command?cmd=stop"
```

---

## 持续移动/控制

```bash
# 持续向前移动 (按 Ctrl+C 停止)
curl -X POST http://localhost:3005/control/state -H "Content-Type: application/json" -d '{"forward": true}'

# 跳跃
curl -X POST http://localhost:3005/control/state -H "Content-Type: application/json" -d '{"jump": true}'

# 停止
curl -X POST http://localhost:3005/control/state -H "Content-Type: application/json" -d '{"forward": false, "jump": false}'
```

---

## 配置文件 (config.yml)

```yaml
llm:
  model: gpt-4o-mini
  endpoint: https://api.openai.com/v1
  api_key: ${OPENAI_API_KEY}

minecraft:
  host: java.applemc.fun
  port: 25565
  username: MineClawBot

api:
  port: 3005
```

---

## 注意事项

1. Bot 需要先连接 Minecraft 服务器
2. HTTP API 默认端口 3005
3. 截图需要安装截图工具（gnome-screenshot, scrot 等）
