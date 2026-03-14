# MineClaw SKILL.md

> Minecraft AI Agent - 操作文档

## 快速启动

```bash
# 1. 安装依赖
cd minecraft-agent
npm install

# 2. 启动 Bot（自动读取 config.yml）
node scripts/start_bot.js

# 3. 使用 Python API
python3 -c "
from minecraft.agent import create_agent
agent = create_agent()
agent.run_task('去挖10块石头')
"
```

---

## 我如何控制 Bot

### HTTP API 端点

基础 URL: `http://localhost:3005`

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/status` | 获取 Bot 状态（血量、饱食度、坐标、物品栏） |
| GET | `/inventory` | 获取物品栏 |
| GET | `/screenshot` | 获取截图 |
| POST | `/command?cmd=<动作>` | 执行动作 |
| POST | `/control/state` | 控制移动/跳跃（JSON body） |
| POST | `/control/attack` | 攻击 |

### 可用动作 (via /command)

```
move <方向>           # forward, backward, left, right
jump                  # 跳跃
attack                # 攻击/挖掘
place <方块名>        # 放置方块 (如 dirt, stone)
use                   # 使用物品
look <yaw> <pitch>   # 视角旋转（角度）
say <消息>            # 聊天
stop                  # 停止移动
```

### 控制移动 (via /control/state)

```json
{
  "forward": true,
  "backward": false,
  "left": false,
  "right": false,
  "jump": true
}
```

---

## 我的决策流程

当我收到任务时，我会：

1. **获取截图** → `GET /screenshot`
2. **获取状态** → `GET /status`
3. **获取物品栏** → `GET /inventory`
4. **分析场景** → 用 LLM 看图 + 状态，理解当前情况
5. **规划动作** → 决定下一步做什么
6. **执行动作** → 调用 HTTP API
7. **观察结果** → 回到步骤 1，直到任务完成

---

## 示例任务流

### 任务：去挖 10 块石头

```
我: "去挖10块石头"

↓ 获取截图 + 状态

LLM 分析: "看到自己在出生点，周围有石头"

↓ 执行动作
POST /command?cmd=move forward
POST /command?cmd=move forward
...

↓ 挖掘
POST /control/attack

↓ 检查物品栏
GET /inventory
{"items": [{"name": "stone", "count": 1}, ...]}

↓ 重复直到 10 块石头
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

## 代码调用示例

### Python

```python
from minecraft.agent import create_agent

# 创建 Agent（自动读取 config.yml）
agent = create_agent()

# 运行任务
agent.run_task("去森林找棵树砍掉")

# 或者手动控制
agent.client.screenshot()  # 获取截图
agent.client.move("forward")  # 移动
agent.client.attack()  # 攻击
```

### 直接用 curl

```bash
# 查看状态
curl http://localhost:3005/status

# 移动
curl -X POST "http://localhost:3005/command?cmd=move forward"

# 跳跃
curl -X POST "http://localhost:3005/command?cmd=jump"

# 攻击
curl -X POST http://localhost:3005/control/attack

# 聊天
curl -X POST "http://localhost:3005/command?cmd=say Hello"
```

---

## 注意事项

1. Bot 需要先在 Minecraft 服务器登录
2. HTTP API 默认端口 3005（在 config.yml 中配置）
3. 截图需要安装截图工具（gnome-screenshot, scrot 等）
4. LLM 需要配置 API Key 才能进行决策
