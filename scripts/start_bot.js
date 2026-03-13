/**
 * Mineflayer Bot 启动脚本
 * 
 * 用法: node start_bot.js --port 25565 --username OpenClawBot
 * 
 * 提供 HTTP API 用于外部控制:
 * - POST /command?cmd=<command>
 * - GET /status
 * - GET /inventory
 * - GET /screenshot
 */

const mineflayer = require('mineflayer');
const http = require('http');
const fs = require('fs');
const path = require('path');

// 命令行参数解析
const args = process.argv.slice(2);
const config = {
  host: 'localhost',
  port: 25565,
  username: 'OpenClawBot',
  apiPort: 3000,
  viewDistance: 2  // 减少视距以提高性能
};

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--host' && args[i + 1]) config.host = args[++i];
  if (args[i] === '--port' && args[i + 1]) config.port = parseInt(args[++i]);
  if (args[i] === '--username' && args[i + 1]) config.username = args[++i];
  if (args[i] === '--api-port' && args[i + 1]) config.apiPort = parseInt(args[++i]);
}

// 创建 Bot
const bot = mineflayer.createBot({
  host: config.host,
  port: config.port,
  username: config.username,
  viewDistance: config.viewDistance,
  chatLengthLimit: 1000000,
});

// 状态存储
const state = {
  health: 20,
  food: 20,
  position: { x: 0, y: 0, z: 0 },
  inventory: [],
  isMining: false,
  lastScreenshot: null
};

// Bot 事件
bot.on('login', () => {
  console.log(`[Mineflayer] Logged in as ${config.username}`);
  console.log(`[Mineflayer] Connected to ${config.host}:${config.port}`);
});

bot.on('death', () => {
  console.log('[Mineflayer] Bot died! Respawning...');
  bot.respawn();
});

bot.on('health', () => {
  state.health = bot.health;
  state.food = bot.food;
});

bot.on('position', (pos) => {
  state.position = {
    x: Math.floor(pos.x),
    y: Math.floor(pos.y),
    z: Math.floor(pos.z)
  };
});

bot.on('windowOpen', (window) => {
  console.log('[Mineflayer] Window opened:', window.title);
});

bot.on('windowClose', (window) => {
  console.log('[Mineflayer] Window closed:', window.title);
});

bot.on('chat', (username, message) => {
  console.log(`[Chat] ${username}: ${message}`);
});

bot.on('error', (err) => {
  console.error('[Mineflayer] Error:', err.message);
});

// 更新物品栏
function updateInventory() {
  try {
    const items = [];
    if (bot.inventory) {
      for (const slot of bot.inventory.slots) {
        if (slot) {
          items.push({
            name: slot.name,
            count: slot.count,
            metadata: slot.metadata,
            displayName: slot.displayName
          });
        }
      }
    }
    state.inventory = items;
  } catch (e) {
    // 忽略错误
  }
}

// 定时更新状态
setInterval(updateInventory, 1000);

// 动作函数
const actions = {
  // 移动
  move: (direction, duration = 1) => {
    return new Promise((resolve) => {
      const speed = 0.1;
      let moved = 0;
      
      const moveInterval = setInterval(() => {
        if (direction === 'forward') bot.setControlState('forward', true);
        else if (direction === 'back') bot.setControlState('back', true);
        else if (direction === 'left') bot.setControlState('left', true);
        else if (direction === 'right') bot.setControlState('right', true);
        
        moved += 0.1;
        if (moved >= duration) {
          bot.setControlState('forward', false);
          bot.setControlState('back', false);
          bot.setControlState('left', false);
          bot.setControlState('right', false);
          clearInterval(moveInterval);
          resolve({ success: true });
        }
      }, 100);
    });
  },
  
  // 跳跃
  jump: () => {
    if (bot.canJump()) {
      bot.jump();
      return { success: true };
    }
    return { success: false, error: 'Cannot jump' };
  },
  
  // 攻击/挖掘
  attack: () => {
    if (bot.entity) {
      bot.attack(bot.entity);
      return { success: true };
    }
    return { success: false, error: 'No target' };
  },
  
  // 放置方块
  place: (x, y, z, block) => {
    try {
      const pos = new bot.Vec3(x, y, z);
      const blockType = bot.registry.blocks[block] || bot.registry.blocks['stone'];
      bot.placeBlock(pos, new bot.Item(blockType, 1));
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  },
  
  // 使用物品
  use: (slot) => {
    try {
      if (slot >= 0 && slot <= 8) {
        bot.inventory.activateItem(slot);
      } else {
        bot.activateItem();
      }
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  },
  
  // 合成
  craft: (recipe, count) => {
    // 简化版 - 需要更复杂的实现
    return { success: false, error: 'Crafting not implemented' };
  },
  
  // 调整视角
  look: (yaw, pitch) => {
    bot.look(yaw * (Math.PI / 180), pitch * (Math.PI / 180));
    return { success: true };
  },
  
  // 发送聊天
  chat: (message) => {
    bot.chat(message);
    return { success: true };
  },
  
  // 状态
  status: () => {
    return {
      health: state.health,
      food: state.food,
      position: state.position,
      inventory: state.inventory,
      dimension: bot.game.dimension,
      gameMode: bot.game.gameMode
    };
  },
  
  // 物品栏
  inventory: () => {
    return { items: state.inventory };
  },
  
  // 截图 - 使用外部截图工具
  screenshot: async () => {
    const screenshotDir = path.join(__dirname, '..', 'screenshots');
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }
    
    const filename = `screenshot_${Date.now()}.png`;
    const filepath = path.join(screenshotDir, filename);
    
    // 尝试使用外部截图工具
    const screenshotTools = ['gnome-screenshot', 'scrot', 'import', 'screencapture'];
    
    for (const tool of screenshotTools) {
      try {
        const { execSync } = require('child_process');
        execSync(`${tool} "${filepath}"`, { timeout: 5000 });
        if (fs.existsSync(filepath)) {
          state.lastScreenshot = filepath;
          console.log(`[Mineflayer] Screenshot saved: ${filepath}`);
          return { path: filepath, tool };
        }
      } catch (e) {
        // 尝试下一个工具
        continue;
      }
    }
    
    return { error: 'No screenshot tool available. Install gnome-screenshot, scrot, or ImageMagick.' };
  }
};

// HTTP API 服务器
const server = http.createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'application/json');
  
  try {
    const url = new URL(req.url, `http://localhost:${config.apiPort}`);
    
    // POST /command
    if (req.method === 'POST' && url.pathname === '/command') {
      const cmd = url.searchParams.get('cmd');
      
      if (!cmd) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: 'Missing cmd parameter' }));
        return;
      }
      
      console.log(`[API] Executing: ${cmd}`);
      const [action, ...args] = cmd.split(' ');
      
      if (actions[action]) {
        const result = await actions[action](...args);
        res.end(JSON.stringify(result));
      } else {
        // 尝试作为原版命令执行
        bot.chat(`/${cmd}`);
        res.end(JSON.stringify({ success: true, note: 'Executed as chat command' }));
      }
      return;
    }
    
    // GET /status
    if (req.method === 'GET' && url.pathname === '/status') {
      res.end(JSON.stringify(actions.status()));
      return;
    }
    
    // GET /inventory
    if (req.method === 'GET' && url.pathname === '/inventory') {
      res.end(JSON.stringify(actions.inventory()));
      return;
    }
    
    // GET /screenshot
    if (req.method === 'GET' && url.pathname === '/screenshot') {
      const result = actions.screenshot();
      res.end(JSON.stringify(result));
      return;
    }
    
    // 404
    res.statusCode = 404;
    res.end(JSON.stringify({ error: 'Not found' }));
    
  } catch (e) {
    res.statusCode = 500;
    res.end(JSON.stringify({ error: e.message }));
  }
});

server.listen(config.apiPort, () => {
  console.log(`[HTTP API] Server running on http://localhost:${config.apiPort}`);
});

console.log('[Mineflayer] Starting bot...');
