/**
 * 权限请求事件处理器
 * 监听 permission.asked 事件并通知用户
 */

import { EventHandler } from './handler.js';
import { sendTextMessage } from '../message/index.js';

/**
 * 权限请求事件处理器
 */
export class PermissionAskedHandler extends EventHandler {
    constructor(project) {
        super('permission.asked');
        this.project = project;
    }

    async process(event, context) {
        const { properties } = event;
        const { id, sessionID, permission, patterns, metadata, always, tool } = properties;

        console.log(`[PermissionAskedHandler] 收到权限请求：${id}, 类型：${permission}`);

        try {
            const { chatManager, agentManager } = context;
            
            // 通过 sessionId 查找对应的 chatId
            const chatId = agentManager?.getChatIdBySessionId(sessionID);
            
            if (!chatId) {
                console.warn(`[PermissionAskedHandler] 未找到会话 ${sessionID} 对应的 chatId`);
                return null;
            }

            // 记录 chatId 和 permissionId 的关系
            chatManager.setPermissionRequest(sessionID, id, {
                sessionId: sessionID,
                permission,
                patterns,
                metadata,
                always,
                tool,
                createdAt: Date.now()
            });
            
            console.log(`[PermissionAskedHandler] 已记录权限请求映射：chatId=${chatId}, permissionId=${id}`);

            // 构建权限请求卡片消息
            const cardContent = this.buildPermissionCard(id, permission, patterns, metadata, always);
            
            // 发送权限请求通知
//            await sendCardMessage(chatManager, chatId, cardContent);
            await sendTextMessage(
                                chatManager,
                                chatId,
                                `工具调用权限请求：${event.properties.permission}，\n请求内容：${event.properties.patterns}，\n 是否允许？`,
                            )

            console.log(`[PermissionAskedHandler] 已发送权限请求通知到 chatId: ${chatId}`);
            
            return {
                success: true,
                id,
                chatId
            };
        } catch (error) {
            console.error(`[PermissionAskedHandler] 处理权限请求失败:`, error.message);
            throw error;
        }
    }

    /**
     * 构建权限请求卡片
     * @param {string} permissionId - 权限 ID
     * @param {string} permission - 权限类型
     * @param {string[]} patterns - 访问模式
     * @param {Object} metadata - 元数据
     * @param {string[]} always - 总是允许的模式
     * @returns {Object} 卡片内容
     */
    buildPermissionCard(permissionId, permission, patterns = [], metadata = {}, always = []) {
        const permissionTypeMap = {
            'external_directory': '外部目录访问',
            'external_file': '外部文件访问',
            'command': '命令执行',
            'network': '网络访问',
            'tool': '工具调用'
        };

        const permissionText = permissionTypeMap[permission] || permission;
        
        // 构建访问路径描述
        const pathText = patterns.length > 0 
            ? patterns.map(p => `• ${p}`).join('\n')
            : '未指定路径';

        // 构建卡片内容
        return {
            config: {
                wide_screen_mode: true
            },
            header: {
                template: 'orange',
                title: {
                    tag: 'plain_text',
                    content: '🔐 权限请求',
                    is_bold: true
                }
            },
            elements: [
                {
                    tag: 'div',
                    text: {
                        tag: 'lark_md',
                        content: `**权限类型:** ${permissionText}`
                    }
                },
                {
                    tag: 'div',
                    text: {
                        tag: 'lark_md',
                        content: `**访问路径:**\n${pathText}`
                    }
                },
                metadata.filepath ? {
                    tag: 'div',
                    text: {
                        tag: 'lark_md',
                        content: `**文件路径:** ${metadata.filepath}`
                    }
                } : null,
                metadata.parentDir ? {
                    tag: 'div',
                    text: {
                        tag: 'lark_md',
                        content: `**父目录:** ${metadata.parentDir}`
                    }
                } : null,
                always.length > 0 ? {
                    tag: 'div',
                    text: {
                        tag: 'lark_md',
                        content: `**总是允许:** ${always.join(', ')}`
                    }
                } : null,
                {
                    tag: 'hr'
                },
                {
                    tag: 'action',
                    actions: [
                        {
                            tag: 'button',
                            text: {
                                tag: 'plain_text',
                                content: '✅ 允许',
                                is_bold: true
                            },
                            type: 'primary',
                            value: {
                                action: 'permit',
                                permissionId,
                                decision: 'allow'
                            }
                        },
                        {
                            tag: 'button',
                            text: {
                                tag: 'plain_text',
                                content: '❌ 拒绝'
                            },
                            type: 'default',
                            value: {
                                action: 'permit',
                                permissionId,
                                decision: 'deny'
                            }
                        },
                        {
                            tag: 'button',
                            text: {
                                tag: 'plain_text',
                                content: '📋 详情'
                            },
                            type: 'default',
                            value: {
                                action: 'view_permission',
                                permissionId
                            }
                        }
                    ]
                },
                {
                    tag: 'div',
                    text: {
                        tag: 'lark_md',
                        content: `💡 使用命令响应：\n\`/permit:${permissionId}\` 允许\n\`/permit:${permissionId}:deny\` 拒绝`
                    }
                }
            ].filter(Boolean)
        };
    }
}
