import type { Plugin, tool } from "@opencode-ai/plugin"
import * as lark from "@larksuiteoapi/node-sdk"
import { getFeishuConfig, isValidConfig, getLogPrefix } from "./feishu-config"

/**
 * 飞书 OpenCode 机器人插件
 * 
 * 功能：
 * 1. 在插件加载时自动建立飞书长连接
 * 2. 监听飞书消息事件
 * 3. 触发 OpenCode Agent 处理任务
 * 4. 返回处理结果到飞书
 */
export const FeishuBotPlugin: Plugin = async (ctx) => {
  const { client: opencodeClient, directory, worktree } = ctx

  // 获取飞书配置
  const feishuConfig = getFeishuConfig();
  
  // 验证配置
  if (!isValidConfig(feishuConfig)) {
    await opencodeClient.app.log({
      body: {
        service: "feishu-bot",
        level: "error",
        message: "缺少必要的环境变量配置：FEISHU_APP_ID 和 FEISHU_APP_SECRET",
      },
    });
    throw new Error("飞书机器人配置不完整");
  }
  
  const baseConfig = {
    appId: feishuConfig.appId,
    appSecret: feishuConfig.appSecret,
  };

  // 创建飞书客户端
  const feishuClient = new (lark as any).Client(baseConfig)
  
  // 创建 WebSocket 客户端（长连接）
  const wsClient = new (lark as any).WSClient({
    ...baseConfig,
    loggerLevel: (lark as any).LoggerLevel.info,
  })

  // 会话映射存储
  const sessionMappings = new Map<string, {
    chatId: string
    userId: string
    task: string
    startTime: number
  }>()

  /**
   * 处理飞书消息
   */
  const handleFeishuMessage = async (data: any) => {
    try {
      const { message } = data
      const { message_type, content, chat_id, sender } = message

      // 只处理文本消息
      if (message_type !== "text") {
        return
      }

      // 解析消息
      const contentObj = JSON.parse(content)
      const text = contentObj.text || ""
      const chatId = chat_id || ""
      const userId = sender?.sender_id?.open_id || ""

      // 记录日志
      await opencodeClient.app.log({
        body: {
          service: "feishu-bot",
          level: "info",
          message: "收到飞书消息",
          extra: { chatId, userId, text },
        },
      })

      // 立即回复 "收到，处理中..."
      await feishuClient.im.v1.message.create({
        params: { receive_id_type: "chat_id" },
        data: {
          receive_id: chatId,
          msg_type: "text",
          content: JSON.stringify({ text: "收到，处理中..." }),
        }
      })

      // 直接触发 OpenCode，不需要关键词匹配
      await createOpenCodeSession(text, chatId, userId)
    } catch (error: any) {
      await opencodeClient.app.log({
        body: {
          service: "feishu-bot",
          level: "error",
          message: `处理消息失败: ${error.message}`,
        },
      })
    }
  }

  /**
   * 创建 OpenCode 会话
   */
  const createOpenCodeSession = async (task: string, chatId: string, userId: string) => {
    try {
      // 创建 OpenCode 会话
      const OPENCODE_URL = feishuConfig.opencodeApiUrl
      
      const response = await fetch(`${OPENCODE_URL}/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: `飞书任务: ${task.substring(0, 50)}`,
        }),
      })

      const session = await response.json()
      const sessionId = session.id

      // 存储映射
      sessionMappings.set(sessionId, {
        chatId,
        userId,
        task,
        startTime: Date.now()
      })

      // 发送任务给 OpenCode
      await fetch(`${OPENCODE_URL}/session/${sessionId}/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role: "user",
          content: `${task}\n\n完成后请使用 feishu.respond_task 工具发送结果到群 ${chatId}`,
        }),
      })

      await opencodeClient.app.log({
        body: {
          service: "feishu-bot",
          level: "info",
          message: `会话已创建: ${sessionId}`,
        },
      })
    } catch (error: any) {
      await opencodeClient.app.log({
        body: {
          service: "feishu-bot",
          level: "error",
          message: `创建会话失败: ${error.message}`,
        },
      })
    }
  }

  // 返回插件定义
  return {
    /**
     * 插件初始化 - OpenCode 会在加载插件时调用
     * 这是启动飞书长连接的正确位置
     */
    async init() {
      await opencodeClient.app.log({
        body: {
          service: "feishu-bot",
          level: "info",
          message: `${getLogPrefix()} 🚀 飞书机器人插件初始化中...`,
        },
      })

      // 启动飞书 WebSocket 长连接
      wsClient.start({
        eventDispatcher: new lark.EventDispatcher({}).register({
          'im.message.receive_v1': handleFeishuMessage,
        }),
      })

      await opencodeClient.app.log({
        body: {
          service: "feishu-bot",
          level: "info",
          message: `${getLogPrefix()} ✅ 飞书长连接已建立，开始监听消息`,
        },
      })
    },

    /**
     * 自定义工具 - 提供给 OpenCode Agent 使用
     */
    tool: {
      // 发送文本消息
      "feishu.send_text": tool({
        description: "发送文本消息到飞书",
        args: {
          receive_id: tool.schema.string().describe("接收者ID"),
          text: tool.schema.string().describe("消息内容"),
          receive_id_type: tool.schema.string().optional().default("chat_id"),
        },
        async execute(args) {
          try {
            const response = await feishuClient.im.v1.message.create({
              params: { receive_id_type: args.receive_id_type as any },
              data: {
                receive_id: args.receive_id,
                msg_type: "text",
                content: JSON.stringify({ text: args.text }),
              },
            })
             return `✅ 消息已发送: ${response.data?.message_id}`
          } catch (error: any) {
            return `❌ 发送失败: ${error.message}`
          }
        }
      }),

      // 响应任务结果
      "feishu.respond_task": tool({
        description: "将处理结果发送回飞书",
        args: {
          chat_id: tool.schema.string().describe("飞书群ID"),
          result: tool.schema.string().describe("处理结果"),
          success: tool.schema.boolean().default(true),
        },
        async execute(args) {
          try {
            const title = args.success ? "✅ 任务完成" : "❌ 任务失败"
            
            await feishuClient.im.v1.message.create({
              params: { receive_id_type: "chat_id" },
              data: {
                receive_id: args.chat_id,
                msg_type: "interactive",
                content: lark.messageCard.defaultCard({
                  title: title,
                  content: args.result,
                }),
              },
            })
            
            return `✅ 结果已发送到飞书群`
          } catch (error: any) {
            return `❌ 发送失败: ${error.message}`
          }
        }
      }),
    },

    /**
     * OpenCode 事件监听
     * 监听 OpenCode 的会话完成事件
     */
    event: async ({ event }) => {
      if (event.type === "session.idle") {
        const sessionId = event.properties.sessionID
        const mapping = sessionMappings.get(sessionId)
        
        if (mapping) {
          try {
            // 获取会话结果
            const OPENCODE_URL = feishuConfig.opencodeApiUrl
            const response = await fetch(`${OPENCODE_URL}/session/${sessionId}`)
            const sessionData = await response.json()
            
            const duration = Date.now() - mapping.startTime
            
            // 发送结果到飞书
            await feishuClient.im.v1.message.create({
              params: { receive_id_type: "chat_id" },
              data: {
                receive_id: mapping.chatId,
                msg_type: "interactive",
                content: lark.messageCard.defaultCard({
                  title: "✅ OpenCode 任务完成",
                  content: `任务: ${mapping.task}\n耗时: ${(duration/1000).toFixed(1)}秒\n\n${sessionData.summary || "已完成"}`,
                }),
              },
            })

            // 清理映射
            sessionMappings.delete(sessionId)
          } catch (error: any) {
            await opencodeClient.app.log({
              body: {
                service: "feishu-bot",
                level: "error",
                message: `发送结果失败: ${error.message}`,
              },
            })
          }
        }
      }
    },

    /**
     * Shell 环境变量注入
     * 确保飞书相关环境变量在 Shell 操作中可用
     */
    "shell.env": async (input, output) => {
      if (process.env.FEISHU_APP_ID) {
        output.env.FEISHU_APP_ID = process.env.FEISHU_APP_ID
      }
      if (process.env.FEISHU_APP_SECRET) {
        output.env.FEISHU_APP_SECRET = process.env.FEISHU_APP_SECRET
      }
    }
  }
}