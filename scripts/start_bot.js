/**
 * Mineflayer Bot 启动脚本
 * 支持从 config.yml 读取配置
 * 
 * 用法: node start_bot.js
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

// 加载 config.yml
function loadConfig() {
  const configPath = path.join(__dirname, '..', 'config.yml');
  
  if (!fs.existsSync(configPath)) {
    console.log('[Config] config.yml not found, using defaults');
    return getDefaultConfig();
  }
  
  try {
    const yaml = require('yaml');
    const configFile = fs.readFileSync(configPath, 'utf8');
    const config = yaml.parse(configFile);
    console.log('[Config] Loaded config.yml');
    return config;
  } catch (e) {
    console.error('[Config] Error loading config.yml:', e.message);
    return getDefaultConfig();
  }
}

function getDefaultConfig() {
  return {
    minecraft: {
      host: 'java.applemc.fun',
      port: 25565,
      username: 'MineClawBot'
    },
    api: {
      port: 3005
    }
  };
}

// 加载配置
const config = loadConfig();
const mcConfig = config.minecraft || {};
const apiConfig = config.api || {};

// 命令行参数会覆盖 config.yml
const args = process.argv.slice(2);
const botConfig = {
  host: mcConfig.host || 'localhost',
  port: mcConfig.port || 25565,
  username: mcConfig.username || 'OpenClawBot',
  apiPort: apiConfig.port || 3005,
  viewDistance: mcConfig.viewDistance || 2
};

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--host' && args[i + 1]) botConfig.host = args[++i];
  if (args[i] === '--port' && args[i + 1]) botConfig.port = parseInt(args[++i]);
  if (args[i] === '--username' && args[i + 1]) botConfig.username = args[++i];
  if (args[i] === '--api-port' && args[i + 1]) botConfig.apiPort = parseInt(args[++i]);
}

console.log(`[Mineflayer] Connecting to ${botConfig.host}:${botConfig.port} as ${botConfig.username}`);

// 创建 Bot
const bot = mineflayer.createBot({
  host: botConfig.host,
  port: botConfig.port,
  username: botConfig.username,
  viewDistance: botConfig.viewDistance,
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
  console.log(`[Mineflayer] ✅ Logged in as ${botConfig.username}`);
  console.log(`[Mineflayer] ✅ Connected to ${botConfig.host}:${botConfig.port}`);
});

bot.on('death', () => {
  console.log('[Mineflayer] 💀 Bot died! Respawning...');
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
  console.log('[Mineflayer] 📦 Window opened:', window.title);
});

bot.on('windowClose', (window) => {
  console.log('[Mineflayer] 📦 Window closed:', window.title);
});

bot.on('chat', (username, message) => {
  console.log(`[Chat] ${username}: ${message}`);
});

bot.on('error', (err) => {
  console.error('[Mineflayer] ❌ Error:', err.message);
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
        else if (direction === 'backward') bot.setControlState('back', true);
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
    try {
      // 使用 setControlState 跳跃
      bot.setControlState('jump', true);
      // 100ms 后释放
      setTimeout(() => {
        try {
          bot.setControlState('jump', false);
        } catch (e) {}
      }, 100);
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
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
  place: (block) => {
    try {
      // 简单的放置 - 放在脚下
      const pos = bot.entity.position;
      const placePos = new mineflayer.Vec3(pos.x, pos.y - 1, pos.z);
      const blockType = bot.registry.blocksByName[block] || bot.registry.blocksByName['stone'];
      bot.placeBlock(placePos, new mineflayer.Item(blockType, 1));
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
  
  // 挖掘
  mine: (blockName) => {
    // 简化版
    return { success: false, error: 'Mining not fully implemented' };
  },
  
  // 调整视角
  look: (yaw, pitch) => {
    try {
      const yawRad = (yaw || 0) * (Math.PI / 180);
      const pitchRad = (pitch || 0) * (Math.PI / 180);
      bot.look(yawRad, pitchRad);
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  },
  
  // 发送聊天
  say: (message) => {
    try {
      // 尝试多种方式发送聊天
      if (typeof bot.chat === 'function') {
        bot.chat(message);
        return { success: true };
      } else if (bot._client && typeof bot._client.writeChat === 'function') {
        bot._client.writeChat(message);
        return { success: true };
      } else {
        // 使用命令方式发送
        bot._client.write(`say ${message}`);
        return { success: true };
      }
    } catch (e) {
      // 使用命令方式作为后备
      try {
        bot.executeCommand(`/say ${message}`);
        return { success: true };
      } catch (e2) {
        return { success: false, error: e2.message };
      }
    }
  },
  
  // 状态
  get_status: () => {
    return {
      health: state.health,
      food: state.food,
      position: state.position,
      inventory: state.inventory,
      dimension: bot.game?.dimension || 'unknown',
      gameMode: bot.game?.gameMode || 'unknown'
    };
  },
  
  // 物品栏
  get_inventory: () => {
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
    const screenshotTools = ['gnome-screenshot', 'scrot', 'import', 'screencapture', 'maim'];
    
    for (const tool of screenshotTools) {
      try {
        const { execSync } = require('child_process');
        execSync(`${tool} "${filepath}"`, { timeout: 5000 });
        if (fs.existsSync(filepath)) {
          state.lastScreenshot = filepath;
          console.log(`[Mineflayer] 📷 Screenshot saved: ${filepath}`);
          return { path: filepath, tool };
        }
      } catch (e) {
        // 尝试下一个工具
        continue;
      }
    }
    
    return { error: 'No screenshot tool available. Install gnome-screenshot, scrot, or ImageMagick.' };
  },
  
  // 停止移动
  stop: () => {
    bot.setControlState('forward', false);
    bot.setControlState('back', false);
    bot.setControlState('left', false);
    bot.setControlState('right', false);
    bot.setControlState('jump', false);
    return { success: true };
  }
};

// HTTP API 服务器
const server = http.createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Content-Type', 'application/json');
  
  // 处理 OPTIONS 预检请求
  if (req.method === 'OPTIONS') {
    res.statusCode = 200;
    res.end();
    return;
  }
  
  try {
    const url = new URL(req.url, `http://localhost:${botConfig.apiPort}`);
    const pathname = url.pathname;
    const method = req.method;
    
    console.log(`[API] ${method} ${pathname}`);
    
    // POST /command
    if (method === 'POST' && pathname === '/command') {
      let body = '';
      for await (const chunk of req) {
        body += chunk;
      }
      
      let cmd = url.searchParams.get('cmd');
      
      // 如果 body 有 JSON 数据，优先使用
      if (body) {
        try {
          const data = JSON.parse(body);
          if (data.cmd) cmd = data.cmd;
        } catch (e) {
          // 忽略
        }
      }
      
      if (!cmd) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: 'Missing cmd parameter' }));
        return;
      }
      
      console.log(`[API] 🔧 Executing: ${cmd}`);
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
    
    // POST /control/state (移动控制)
    if (method === 'POST' && pathname === '/control/state') {
      let body = '';
      for await (const chunk of req) {
        body += chunk;
      }
      
      const data = JSON.parse(body || '{}');
      
      if (data.forward) bot.setControlState('forward', true);
      else bot.setControlState('forward', false);
      
      if (data.backward) bot.setControlState('back', true);
      else bot.setControlState('back', false);
      
      if (data.left) bot.setControlState('left', true);
      else bot.setControlState('left', false);
      
      if (data.right) bot.setControlState('right', true);
      else bot.setControlState('right', false);
      
      if (data.jump) bot.setControlState('jump', true);
      else bot.setControlState('jump', false);
      
      res.end(JSON.stringify({ success: true }));
      return;
    }
    
    // POST /control/attack
    if (method === 'POST' && pathname === '/control/attack') {
      bot.attack();
      res.end(JSON.stringify({ success: true }));
      return;
    }
    
    // GET /status
    if (method === 'GET' && pathname === '/status') {
      res.end(JSON.stringify(actions.get_status()));
      return;
    }
    
    // GET /inventory
    if (method === 'GET' && pathname === '/inventory') {
      res.end(JSON.stringify(actions.get_inventory()));
      return;
    }
    
    // GET /screenshot
    if (method === 'GET' && pathname === '/screenshot') {
      const result = await actions.screenshot();
      res.end(JSON.stringify(result));
      return;
    }
    
    // GET /render (POV)
    if (method === 'GET' && pathname === '/render') {
      res.end(JSON.stringify({ 
        note: 'Use external screenshot tool',
        endpoint: '/screenshot'
      }));
      return;
    }
    
    // 404
    res.statusCode = 404;
    res.end(JSON.stringify({ error: 'Not found', available_endpoints: [
      'POST /command',
      'POST /control/state',
      'POST /control/attack',
      'GET /status',
      'GET /inventory',
      'GET /screenshot'
    ]}));
    
  } catch (e) {
    res.statusCode = 500;
    console.error('[API] ❌ Error:', e.message);
    res.end(JSON.stringify({ error: e.message }));
  }
});

server.listen(botConfig.apiPort, () => {
  console.log(`[HTTP API] 🌐 Server running on http://localhost:${botConfig.apiPort}`);
  console.log(`[HTTP API] Available endpoints:`);
  console.log(`  - POST /command?cmd=<action> [args...]`);
  console.log(`  - GET  /status`);
  console.log(`  - GET  /inventory`);
  console.log(`  - GET  /screenshot`);
});

console.log('[Mineflayer] 🚀 Starting bot...');
