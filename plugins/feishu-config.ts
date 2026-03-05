/**
 * 飞书机器人配置管理（TypeScript版本）
 */
export interface FeishuConfig {
  appId: string;
  appSecret: string;
  defaultChatId: string;
  opencodeApiUrl: string;
  messageConfig: {
    messageIdTtl: number;
    messageExpiryTime: number;
    processingTimeout: number;
  };
  logConfig: {
    level: string;
    enableDebug: boolean;
  };
}

export const getFeishuConfig = (): FeishuConfig => {
  return {
    appId: process.env.FEISHU_APP_ID || '',
    appSecret: process.env.FEISHU_APP_SECRET || '',
    defaultChatId: process.env.FEISHU_DEFAULT_CHAT_ID || '',
    opencodeApiUrl: process.env.OPENCODE_API_URL || 'http://localhost:4096',
    messageConfig: {
      messageIdTtl: parseInt(process.env.FEISHU_MESSAGE_ID_TTL || '3600000'),
      messageExpiryTime: parseInt(process.env.FEISHU_MESSAGE_EXPIRY_TIME || '120000'),
      processingTimeout: parseInt(process.env.FEISHU_PROCESSING_TIMEOUT || '5000'),
    },
    logConfig: {
      level: process.env.FEISHU_LOG_LEVEL || 'info',
      enableDebug: process.env.FEISHU_DEBUG === 'true',
    },
  };
};

export const isValidConfig = (config: FeishuConfig): boolean => {
  return !!(config.appId && config.appSecret);
};

export const getLogPrefix = (): string => {
  return '[FeishuBot]';
};

export const isDebugEnabled = (config: FeishuConfig): boolean => {
  return config.logConfig.enableDebug;
};