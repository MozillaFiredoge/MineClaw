# MineClaw SKILL.md

> Minecraft AI Agent 技能接口 - 让 AI 自主玩 Minecraft

## 快速开始

```bash
# 1. 安装依赖
cd minecraft-agent
npm install
yarn install

# 2. 配置 config.yml（必须）
# - 填写你的 OpenAI API Key
# - 设置 Minecraft 服务器信息

# 3. 启动 Mineflayer Bot
node scripts/start_bot.js --host java.applemc.fun --port 25565 --username YourBotName

# 4. 使用 Agent（Python）
python -c "
from minecraft.agent import create_agent
agent = create_agent()
agent.run_task('去挖10块石头')
"
```

---

## 配置文件 config.yml

```yaml
# LLM 配置（必须）
llm:
  model: gpt-4o-mini              # 模型
  endpoint: https://api.openai.com/v1  # API 端点
  api_key: ${OPENAI_API_KEY}      # API 密钥（支持环境变量）
  vision_base64: true             # 图片是否用 base64 编码

# Minecraft 服务器
minecraft:
  host: java.applemc.fun
  port: 25565
  username: MineClaw
  http_port: 3005                 # Mineflayer HTTP API 端口

# Voyager 技能库（可选）
voyager:
  skill_library_path: ./data/skills.json
  auto_save: true
```

---

## 使用方式

### 方式一：Python API

```python
from minecraft.agent import create_agent

# 创建 Agent
agent = create_agent('config.yml')

# 执行任务
agent.run_task('去森林找一棵树然后砍掉')
```

### 方式二：HTTP API（推荐）

启动 Bot 后，用 curl 控制：

```bash
# 获取状态
curl http://localhost:3005/status

# 获取截图
curl http://localhost:3005/screenshot -o screenshot.png

# 移动
curl -X POST http://localhost:3005/command?cmd=move%20forward

# 放置方块
curl -X POST http://localhost:3005/blocks/place -H "Content-Type: application/json" -d '{"name": "dirt"}'

# 挖掘
curl -X POST http://localhost:3005/mine -H "Content-Type: application/json" -d '{"block": "stone"}'

# 合成
curl -X POST http://localhost:3005/craft -H "Content-Type: application/json" -d '{"item": "stick", "count": 4}'

# 攻击
curl -X POST http://localhost:3005/control/attack

# 聊天
curl -X POST "http://localhost:3005/command?cmd=say%20Hello%20World"
```

---

## 可用动作

| 动作 | 说明 | 示例 |
|------|------|------|
| `move <方向>` | 移动 | `move forward`, `move left` |
| `jump` | 跳跃 | `jump` |
| `attack` | 攻击/挖掘 | `attack` |
| `place_block <方块>` | 放置方块 | `place_block dirt` |
| `use_item` | 使用主手物品 | `use_item` |
| `craft <物品>` | 合成 | `craft table` |
| `mine <方块>` | 挖掘指定方块 | `mine stone` |
| `look <yaw> <pitch>` | 视角旋转 | `look 90 0` |
| `screenshot` | 获取截图 | `screenshot` |
| `get_status` | 获取状态 | `get_status` |
| `get_inventory` | 获取物品栏 | `get_inventory` |

---

## 端点列表

### 状态获取
- `GET /status` - 生命值、饱食度、坐标
- `GET /inventory` - 物品栏
- `GET /screenshot` - 游戏截图
- `GET /entities` - 附近的实体
- `GET /chunks` - 加载的区块

### 动作执行
- `POST /command?cmd=<命令>` - 执行命令
- `POST /control/state` - 控制移动/跳跃
- `POST /control/attack` - 攻击
- `POST /blocks/place` - 放置方块
- `POST /mine` - 挖掘
- `POST /craft` - 合成
- `POST /items/use` - 使用物品
- `POST /pathfinder/go` - 导航

---

## 常见问题

### Q: 连接不上服务器？
- 检查服务器地址和端口是否正确
- 确认服务器允许外链 bot 登录

### Q: API 调用返回错误？
- 确认 Mineflayer HTTP API 已启动（默认 localhost:3005）
- 查看 Bot 控制台日志

### Q: LLM 调用失败？
- 检查 config.yml 中的 api_key 是否正确
- 确认 endpoint 可访问

---

## 架构图

```
┌─────────────┐     ┌──────────────────┐     ┌────────────────┐
│   用户       │────▶│   MinecraftAgent │────▶│ Mineflayer Bot │
│ (发任务)    │     │   (LLM 决策)     │     │  (游戏执行)    │
└─────────────┘     └──────────────────┘     └────────────────┘
                           │
                           ▼
                    ┌──────────────────┐
                    │    SkillLibrary  │
                    │   ( Voyager 技能) │
                    └──────────────────┘
```

---

**需要帮助？** 随时问我！🎮
