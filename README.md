# OpenClaw Minecraft Agent

让 AI 能够玩 Minecraft！基于 Voyager 思想，接入 OpenClaw。

![OpenClaw Minecraft](https://img.shields.io/badge/OpenClaw-Minecraft-blue)

## 功能特性

- 🎮 **游戏控制** - 移动、跳跃、挖掘、放置方块、合成
- 👁️ **视觉理解** - 截取游戏画面，分析场景
- 🧠 **LLM 决策** - 使用 OpenClaw 的模型进行智能决策
- 📱 **多平台控制** - 通过 QQ/Discord 等平台控制

## 快速开始

### 1. 安装依赖

```bash
# Node.js 依赖
cd minecraft-agent
npm install

# Python 依赖
pip install mss pynput asyncio
```

### 2. 启动 Minecraft

1. 启动 Minecraft 1.19+
2. 创建世界，设为创造模式
3. ESC → 开放给 LAN
4. 允许作弊: ON

记住端口号（默认 25565）

### 3. 启动 Bot

```bash
node scripts/start_bot.js --port 25565 --username OpenClawBot
```

### 4. 使用 Python API

```python
from minecraft.agent import create_agent

# 创建 Agent
agent = create_agent(host="localhost", port=25565, username="OpenClawBot")

# 或使用 async
import asyncio

async def main():
    agent = create_agent()
    await agent.execute_task("去挖一些石头")

asyncio.run(main())
```

## 项目结构

```
minecraft-agent/
├── SKILL.md              # OpenClaw Skill 定义
├── README.md             # 本文件
├── package.json          # Node.js 依赖
├── minecraft/
│   ├── __init__.py
│   ├── agent.py          # 主 Agent 类
│   ├── mineflayer_client.py  # Mineflayer 通信
│   └── vision.py         # 视觉处理
├── prompts/
│   ├── system.txt        # 系统提示词
│   └── action.txt       # 动作提示词
└── scripts/
    ├── start_bot.js      # Bot 启动脚本
    └── screenshot.js     # 截图脚本
```

## 可用动作

| 动作 | 说明 | 参数 |
|------|------|------|
| `move` | 移动 | `direction`: forward/back/left/right, `duration`: 秒 |
| `jump` | 跳跃 | - |
| `attack` | 攻击/挖掘 | `target`: 目标(可选) |
| `place_block` | 放置方块 | `position`: {x,y,z}, `block`: 方块ID |
| `craft` | 合成 | `recipe`: 配方, `count`: 数量 |
| `look` | 调整视角 | `yaw`: 水平角度, `pitch`: 垂直角度 |
| `use_item` | 使用物品 | `slot`: 槽位(可选) |
| `screenshot` | 截图 | - |
| `get_status` | 获取状态 | - |
| `get_inventory` | 获取物品栏 | - |

## HTTP API

Bot 启动后可通过 HTTP API 控制：

```bash
# 获取状态
curl http://localhost:3000/status

# 获取物品栏
curl http://localhost:3000/inventory

# 截图
curl http://localhost:3000/screenshot

# 执行动作
curl -X POST "http://localhost:3000/command?cmd=move+forward+1"
curl -X POST "http://localhost:3000/command?cmd=jump"
curl -X POST "http://localhost:3000/command?cmd=look+90+0"
```

## 接入 OpenClaw

1. 将本项目作为 OpenClaw 的 Skill
2. 通过 QQ/Discord 等平台发送指令
3. Agent 会自动解析任务、执行动作

## 参考

- [Voyager](https://github.com/MineDojo/Voyager) - NVIDIA 的 Minecraft AI Agent
- [Mineflayer](https://github.com/PrismarineJS/mineflayer) - Node.js Minecraft 客户端
- [OpenClaw](https://github.com/openclaw/openclaw) - AI Agent 框架

## License

MIT
