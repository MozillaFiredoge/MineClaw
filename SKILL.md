---
name: minecraft-agent
description: 让 AI 能够玩 Minecraft。通过截取游戏画面、使用视觉模型理解场景、LLM 决策动作，并控制鼠标键盘执行操作。当用户要求 AI 玩 Minecraft、要在 MC 中执行任务、获取游戏状态时使用此技能。
---

# Minecraft Agent Skill

本技能让 OpenClaw 能够作为 AI Agent 玩 Minecraft 游戏。

## 核心功能

- **游戏连接**: 通过 Mineflayer 连接本地 Minecraft 服务端
- **视觉理解**: 截取游戏画面，分析场景、物品、敌怪
- **动作执行**: 控制键盘鼠标执行移动、挖掘、放置、合成等操作
- **状态反馈**: 获取物品栏、血量、饱食度、游戏状态

## 使用方式

### 1. 启动 Minecraft 服务

用户需要先启动 Minecraft 并开放 LAN 服务器：

```
1. 启动 Minecraft (版本 1.19+)
2. 创建或进入一个世界
3. 设为创造模式 / 简单难度
4. 按 ESC → 开放给 LAN
5. 允许作弊: ON
6. 记住端口号 (默认 25565)
```

### 2. 启动 Mineflayer Bot

```bash
cd minecraft-agent
npm install
node scripts/start_bot.js --port 25565 --username OpenClawBot
```

### 3. 通过对话控制

用户可以通过 QQ/Discord 告诉 AI 要做什么，例如：
- "去挖点石头"
- "造一个房子"
- "杀掉附近的僵尸"

## 可用动作

- `move(direction)`: 移动 (forward/back/left/right)
- `jump()`: 跳跃
- `look(yaw, pitch)`: 视角
- `attack()`: 攻击/挖掘
- `useItem()`: 使用物品
- `placeBlock(position, block)`: 放置方块
- `craft(recipe, count)`: 合成
- `getInventory()`: 获取物品栏
- `getStatus()`: 获取状态 (血量、饱食度等)
- `screenshot()`: 截取屏幕

## 文件结构

```
minecraft-agent/
├── SKILL.md
├── README.md
├── minecraft/
│   ├── __init__.py
│   ├── agent.py          # 主 Agent 类
│   ├── mineflayer_client.py  # Mineflayer 通信
│   └── vision.py         # 视觉处理
├── prompts/
│   ├── system.txt        # 系统提示词
│   └── action.txt        # 动作提示词
└── scripts/
    ├── start_bot.js      # 启动 Bot 脚本
    └── screenshot.js     # 截图脚本
```

## 依赖

- Node.js ≥ 16.13.0
- Minecraft 服务端 (本地)
- Mineflayer
- pynput (Python 鼠标键盘控制)
- mss (屏幕截图)
