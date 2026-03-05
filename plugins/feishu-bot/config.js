/**
 * 飞书机器人配置管理
 */
export const FeishuConfig = {
  // 从环境变量获取配置，支持本地开发和生产环境
  appId: process.env.FEISHU_APP_ID || '',
  appSecret: process.env.FEISHU_APP_SECRET || '',
  
  // 默认聊天ID（可选）
  defaultChatId: process.env.FEISHU_DEFAULT_CHAT_ID || '',
  
  // OpenCode API 配置
  opencodeApiUrl: process.env.OPENCODE_API_URL || 'http://localhost:4096',
  
  // 消息处理配置
  messageConfig: {
    // 消息去重时间窗口（毫秒）
    messageIdTtl: parseInt(process.env.FEISHU_MESSAGE_ID_TTL || '3600000'), // 1小时
    // 消息过期时间（毫秒）
    messageExpiryTime: parseInt(process.env.FEISHU_MESSAGE_EXPIRY_TIME || '120000'), // 2分钟
    // 处理标记过期时间（毫秒）
    processingTimeout: parseInt(process.env.FEISHU_PROCESSING_TIMEOUT || '5000'), // 5秒
  },
  
  // 日志配置
  logConfig: {
    level: process.env.FEISHU_LOG_LEVEL || 'info',
    enableDebug: process.env.FEISHU_DEBUG === 'true',
  },
  
  /**
   * 验证配置是否有效
   * @returns {boolean} 配置是否有效
   */
  isValid() {
    return !!(this.appId && this.appSecret);
  },
  
  /**
   * 获取日志前缀
   * @returns {string} 日志前缀
   */
  getLogPrefix() {
    return '[FeishuBot]';
  },
  
  /**
   * 是否启用调试模式
   * @returns {boolean} 是否启用调试
   */
  isDebugEnabled() {
    return this.logConfig.enableDebug;
  }
};