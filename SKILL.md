# Voyager Minecraft Skill

让 AI 能够像 Voyager 一样玩 Minecraft。

## 架构

```
┌─────────────────────────────────────────────┐
│         OpenClaw (我)                        │
│  - 理解用户意图                              │
│  - 下达任务                                  │
│  - 监督/反思                                 │
└──────────────────┬──────────────────────────┘
                   │ 任务指令
                   ▼
┌─────────────────────────────────────────────┐
│       Voyager Agent (本地运行)               │
│  ┌─────────────────────────────────────────┐│
│  │ Skill Library (终身学习)                ││
│  │ - 存储学会的技能                         ││
│  │ - 持续改进                               ││
│  └─────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────┐│
│  │ 循环: 观察 → 思考 → 执行 → 反思          ││
│  └─────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────┐│
│  │ Minecraft (Mineflayer)                  ││
│  │ - 视觉输入                               ││
│  │ - 动作执行                               ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

## 使用方式

### 1. 启动 Minecraft

```
1. 启动 Minecraft 1.19+
2. 创建世界，设为创造模式
3. ESC → 开放给 LAN
4. 记住端口 (默认 25565)
```

### 2. 启动 Bot

```bash
cd MineClaw
npm install
node scripts/start_bot.js --port 25565
```

### 3. 我来控制

你可以通过 QQ/Discord 给我下达任务，例如：

- "去挖 10 块石头"
- "造一个房子"
- "杀掉附近的僵尸"

我会：
1. 理解任务
2. 通过 HTTP API 控制 Bot
3. 观察结果
4. 反思改进

## 技能库

Agent 会从任务中学习，自动保存成功的策略到 `skills/library.json`。

每次执行任务：
- 观察游戏状态
- 决定动作
- 执行并观察结果
- 成功? 存入技能库
- 失败? 反思改进

## API

Bot 提供 HTTP API:

```
GET  /status      - 获取状态 (血量、位置等)
GET  /inventory   - 获取物品栏
GET  /screenshot  - 截图
POST /command?cmd=<action> - 执行动作
```

## 动作

| 动作 | 参数 | 说明 |
|------|------|------|
| move | direction, duration | 移动 |
| jump | - | 跳跃 |
| attack | target | 挖掘/攻击 |
| place | x, y, z, block | 放置方块 |
| craft | recipe, count | 合成 |
| use | slot | 使用物品 |
| look | yaw, pitch | 视角 |

## 文件结构

```
MineClaw/
├── SKILL.md              # 本文件
├── README.md
├── package.json
├── minecraft/
│   ├── __init__.py
│   ├── agent.py          # 基础 Agent
│   ├── voyager.py        # Voyager 终身学习版 ⭐
│   ├── mineflayer_client.py
│   └── vision.py         # 视觉处理
├── prompts/
│   ├── system.txt        # 系统提示
│   ├── action.txt        # 动作提示
│   └── reflection.txt    # 反思提示
├── skills/
│   └── library.json      # 技能库 (自动生成)
└── scripts/
    └── start_bot.js      # Bot 启动
```
