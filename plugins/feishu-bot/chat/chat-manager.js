/**
 * 飞书群聊管理模块
 * 提供建群、拉人、群信息管理等功能
 */

import * as lark from '@larksuiteoapi/node-sdk';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(__dirname, '../.env') });

/**
 * 创建飞书客户端
 */
function createFeishuClient() {
    return new lark.Client({
        appId: process.env.FEISHU_APP_ID,
        appSecret: process.env.FEISHU_APP_SECRET
    });
}

/**
 * 聊天管理器类
 */
export class ChatManager {
    constructor(client, agentManager = null) {
        this.client = client || createFeishuClient();
        this.agentManager = agentManager;
        
        // Agent 上下文管理：chatId -> { agentKey, sessionId, metadata }
        this.#agentContextMap = new Map();
        this.#permissionRequestMap = new Map();
    }
    
    /**
     * Agent 上下文映射表
     * @type {Map<string, Object>}
     */
    #agentContextMap;

    /**
     * 权限请求映射表：chatId -> { permissionId, details }
     * @type {Map<string, Object>}
     */
    #permissionRequestMap;

/**
     * 创建群聊
     * @param {Object} options - 创建选项
     * @param {string} options.name - 群名称
     * @param {string} [options.description] - 群描述
     * @param {string[]} options.user_id_list - 初始成员 ID 列表
     * @param {string} [options.user_id_type='open_id'] - 用户 ID 类型: open_id, union_id, user_id
     * @param {string} [options.chat_mode='group'] - 群聊模式: group, p2p_chat
     * @param {string} [options.chat_type='private'] - 群类型: private, public, union
     * @param {string} [options.owner_id=''] - 指定群主的用户ID（open_id），默认空则创建者为群主
     * @returns {Promise<Object>} 创建结果 { chat_id, name, chat_type }
     */
    async createChat(options) {
        const { 
            name, 
            description, 
            user_id_list, 
            user_id_type = 'open_id',
            chat_mode = 'group', 
            chat_type = 'private',
            owner_id = ''
        } = options;

        if (!name) {
            throw new Error('群名称不能为空');
        }
        if (!user_id_list || user_id_list.length === 0) {
            throw new Error('至少需要一个初始成员');
        }

        if (chat_type === 'union' && user_id_type !== 'union_id') {
            console.warn('[ChatManager] 创建联合群时建议使用 union_id 类型的用户 ID');
        }

        try {
            const response = await this.client.im.chat.create({
                data: {
                    name,
                    description: description || '',
                    user_id_list,
                    chat_mode,
                    chat_type,
                    owner_id
                }
            });

            console.log(`[ChatManager] 群聊创建成功: ${name} (类型: ${chat_type})`);
            return {
                chat_id: response.data.chat_id,
                name: response.data.name,
                chat_type
            };
        } catch (error) {
            console.error('[ChatManager] 创建群聊失败:', error.message);
            if (error.response?.data) {
                console.error('[ChatManager] 错误详情:', JSON.stringify(error.response.data, null, 2));
            }
            throw error;
        }
    }

    /**
     * 创建外部群/联合群
     * @param {Object} options - 创建选项
     * @param {string} options.name - 群名称
     * @param {string} [options.description] - 群描述
     * @param {string[]} options.member_list - 成员列表，支持混合类型: { open_id: 'ou_xxx' } 或 { union_id: 'on_xxx' }
     * @returns {Promise<Object>} 创建结果 { chat_id, name }
     */
    async createUnionChat(options) {
        const { name, description, member_list } = options;

        if (!name) {
            throw new Error('群名称不能为空');
        }
        if (!member_list || member_list.length === 0) {
            throw new Error('至少需要一个初始成员');
        }

        const userIdList = member_list.map(member => {
            if (member.open_id) return member.open_id;
            if (member.union_id) return member.union_id;
            if (member.user_id) return member.user_id;
            throw new Error('成员必须包含 open_id, union_id 或 user_id');
        });

        return await this.createChat({
            name,
            description,
            user_id_list: userIdList,
            user_id_type: 'union_id',
            chat_mode: 'group',
            chat_type: 'union'
        });
    }

    /**
     * 添加群成员
     * @param {string} chatId - 群ID
     * @param {string[]} userIdList - 用户 open_id 列表
     * @param {string} [memberIdType='open_id'] - 成员ID类型
     * @returns {Promise<Object>} 添加结果
     */
    async addMembers(chatId, userIdList, memberIdType = 'open_id') {
        if (!chatId) {
            throw new Error('群ID不能为空');
        }
        if (!userIdList || userIdList.length === 0) {
            throw new Error('成员列表不能为空');
        }

        try {
            const response = await this.client.im.chatMembers.create({
                path: { chat_id: chatId },
                data: {
                    member_id_type: memberIdType,
                    user_id_list: userIdList
                }
            });

            console.log(`[ChatManager] 成员添加成功: ${userIdList.length} 人`);
            return {
                success: true,
                added_count: userIdList.length,
                invalid_users: response.data?.invalid_users || []
            };
        } catch (error) {
            console.error('[ChatManager] 添加成员失败:', error.message);
            throw error;
        }
    }

    /**
     * 移除群成员
     * @param {string} chatId - 群ID
     * @param {string[]} userIdList - 用户 open_id 列表
     * @param {string} [memberIdType='open_id'] - 成员ID类型
     * @returns {Promise<Object>} 移除结果
     */
    async removeMembers(chatId, userIdList, memberIdType = 'open_id') {
        if (!chatId) {
            throw new Error('群ID不能为空');
        }
        if (!userIdList || userIdList.length === 0) {
            throw new Error('成员列表不能为空');
        }

        try {
            const response = await this.client.im.chatMembers.delete({
                path: { chat_id: chatId },
                data: {
                    member_id_type: memberIdType,
                    user_id_list: userIdList
                }
            });

            console.log(`[ChatManager] 成员移除成功: ${userIdList.length} 人`);
            return {
                success: true,
                removed_count: userIdList.length
            };
        } catch (error) {
            console.error('[ChatManager] 移除成员失败:', error.message);
            throw error;
        }
    }

    /**
     * 获取群信息
     * @param {string} chatId - 群ID
     * @returns {Promise<Object>} 群信息
     */
    async getChatInfo(chatId) {
        if (!chatId) {
            throw new Error('群ID不能为空');
        }

        try {
            const response = await this.client.im.chat.get({
                path: { chat_id: chatId }
            });

            return response.data;
        } catch (error) {
            console.error('[ChatManager] 获取群信息失败:', error.message);
            throw error;
        }
    }

    /**
     * 获取群成员列表
     * @param {string} chatId - 群ID
     * @param {string} [memberIdType='open_id'] - 成员ID类型
     * @param {number} [pageSize=50] - 每页数量
     * @returns {Promise<Object>} 成员列表
     */
    async getMembers(chatId, memberIdType = 'open_id', pageSize = 50) {
        if (!chatId) {
            throw new Error('群ID不能为空');
        }

        try {
            const response = await this.client.im.chatMembers.get({
                path: { chat_id: chatId },
                params: {
                    member_id_type: memberIdType,
                    page_size: pageSize
                }
            });

            return {
                members: response.data?.items || [],
                has_more: response.data?.has_more || false,
                page_token: response.data?.page_token
            };
        } catch (error) {
            console.error('[ChatManager] 获取群成员失败:', error.message);
            throw error;
        }
    }

    /**
     * 更新群信息
     * @param {string} chatId - 群ID
     * @param {Object} options - 更新选项
     * @param {string} [options.name] - 群名称
     * @param {string} [options.description] - 群描述
     * @returns {Promise<Object>} 更新结果
     */
    async updateChatInfo(chatId, options) {
        if (!chatId) {
            throw new Error('群ID不能为空');
        }

        try {
            const updateData = {};
            if (options.name) updateData.name = options.name;
            if (options.description) updateData.description = options.description;

            await this.client.im.chat.update({
                path: { chat_id: chatId },
                data: updateData
            });

            console.log(`[ChatManager] 群信息更新成功`);
            return { success: true };
        } catch (error) {
            console.error('[ChatManager] 更新群信息失败:', error.message);
            throw error;
        }
    }

    /**
     * 解散群聊
     * @param {string} chatId - 群ID
     * @returns {Promise<Object>} 解散结果
     */
    async disbandChat(chatId) {
        if (!chatId) {
            throw new Error('群ID不能为空');
        }

        try {
            await this.client.im.chat.delete({
                path: { chat_id: chatId }
            });

            console.log(`[ChatManager] 群聊已解散: ${chatId}`);
            return { success: true };
        } catch (error) {
            console.error('[ChatManager] 解散群聊失败:', error.message);
            throw error;
        }
    }

/**
     * 设置群主
     * @param {string} chatId - 群ID
     * @param {string} ownerId - 新群主的用户ID
     * @param {string} [ownerIdType='open_id'] - 用户ID类型: open_id, union_id, user_id
     * @returns {Promise<Object>} 设置结果
     */
    async setOwner(chatId, ownerId, ownerIdType = 'open_id') {
        if (!chatId) {
            throw new Error('群ID不能为空');
        }
        if (!ownerId) {
            throw new Error('新群主ID不能为空');
        }

        try {
            const response = await this.client.request({
                method: 'POST',
                url: `/im/v1/chats/${chatId}/set_owner?user_id_type=${ownerIdType}`,
                data: {
                    owner_id: ownerId
                }
            });

            console.log(`[ChatManager] 群主设置成功: ${ownerId}`);
            return {
                success: true,
                owner_id: response.data?.owner_id
            };
        } catch (error) {
            console.error('[ChatManager] 设置群主失败:', error.message);
            if (error.response?.data) {
                console.error('[ChatManager] 错误详情:', JSON.stringify(error.response.data, null, 2));
            }
            throw error;
        }
    }

    /**
     * 设置群管理员
     * @param {string} chatId - 群ID
     * @param {string[]} adminIds - 管理员用户ID列表
     * @param {string} [adminIdType='open_id'] - 用户ID类型: open_id, union_id, user_id
     * @returns {Promise<Object>} 设置结果
     */
    async setAdmin(chatId, adminIds, adminIdType = 'open_id') {
        if (!chatId) {
            throw new Error('群ID不能为空');
        }
        if (!adminIds || adminIds.length === 0) {
            throw new Error('管理员ID列表不能为空');
        }

        try {
            const response = await this.client.im.chat.setAdmin({
                path: { chat_id: chatId },
                params: { user_id_type: adminIdType },
                data: {
                    admin_ids: adminIds
                }
            });

            console.log(`[ChatManager] 管理员设置成功: ${adminIds.length} 人`);
            return {
                success: true,
                admin_ids: response.data?.admin_ids || []
            };
        } catch (error) {
            console.error('[ChatManager] 设置管理员失败:', error.message);
            if (error.response?.data) {
                console.error('[ChatManager] 错误详情:', JSON.stringify(error.response.data, null, 2));
            }
            throw error;
        }
    }

    /**
     * 发送群消息
     * @param {string} chatId - 群ID
     * @param {string} content - 消息内容
     * @param {string} [msgType='text'] - 消息类型
     * @returns {Promise<Object>} 发送结果
     */
    async sendMessage(chatId, content, msgType = 'text') {
        if (!chatId) {
            throw new Error('群ID不能为空');
        }

        try {
            let msgContent;
            if (msgType === 'text') {
                msgContent = JSON.stringify({ text: content });
            } else {
                msgContent = content;
            }

            const response = await this.client.im.message.create({
                params: { receive_id_type: 'chat_id' },
                data: {
                    receive_id: chatId,
                    msg_type: msgType,
                    content: msgContent
                }
            });

            console.log(`[ChatManager] 消息发送成功`);
            return {
                success: true,
                message_id: response.data?.message_id
            };
        } catch (error) {
            console.error('[ChatManager] 发送消息失败:', error.message);
            throw error;
        }
    }

    // 客户端基础管理

    /**
     * 获取飞书客户端实例
     * @returns {Object} 飞书客户端实例
     */
    getClient() {
        console.log(`[ChatManager] 获取飞书客户端实例 ${this.client ? '成功' : '失败'}`);
        return this.client;
    }

    /**
     * 设置当前 Agent
     * @param {string} chatId - 聊天 ID
     * @param {string} agentKey - Agent 键
     * @returns {boolean} 设置结果
     */
    setCurrentAgent(chatId, agentKey) {
        if (!this.agentManager) {
            console.warn('[ChatManager] agentManager 未初始化，无法切换 Agent');
            return false;
        }

        const success = this.agentManager.existsAgent(agentKey); // 验证 Agent 是否存在

        if (success) {
            // 更新上下文
            const context = this.#getOrCreateContext(chatId);
            context.agentKey = agentKey;
            console.log(`[ChatManager] 已更新 chatId=${chatId} 的 Agent 上下文：${agentKey}`);
        }

        return success;
    }

    /**
     * 获取当前 Agent 名称
     * @param {string} chatId - 聊天 ID
     * @returns {string} Agent 名称
     */
    getCurrentAgentName(chatId) {
        if (!this.agentManager) {
            console.warn('[ChatManager] agentManager 未初始化，无法获取 Agent 名称');
            return 'unknown';
        }

        return this.agentManager.getCurrentAgentName(this.getCurrentAgentKey(chatId));
    }
    
    /**
     * 获取当前 Agent Key
     * @param {string} chatId - 聊天 ID
     * @returns {string|null} Agent Key，如果未设置返回 null
     */
    getCurrentAgentKey(chatId, defaultKey) {
        const context = this.#agentContextMap.get(chatId);
        if (!context?.agentKey && defaultKey) {
            this.setCurrentAgent(chatId, defaultKey)
            return defaultKey
        };
        return context?.agentKey;
    }

    /**
     * 列出当前 Agent 的所有会话
     * @returns {Promise<Array>} 会话列表
     */
    async listSessions() {
        if (!this.agentManager) {
            console.warn('[ChatManager] agentManager 未初始化，无法列出会话');
            return [];
        }
        return await this.agentManager.listSessions();
    }

    /**
     * 切换当前会话
     * @param {string} chatId - 聊天 ID
     * @param {string} sessionId - 新的会话 ID
     * @returns {string} 切换后的会话 ID
     */
    switchSession(chatId, sessionId) {
        if (!this.agentManager) {
            console.warn('[ChatManager] agentManager 未初始化，无法切换会话');
            return sessionId;
        }
        
        const result = this.agentManager.switchSession(chatId, sessionId);
        
        // 更新上下文
        const context = this.#getOrCreateContext(chatId);
        context.sessionId = sessionId;
        console.log(`[ChatManager] 已更新 chatId=${chatId} 的会话上下文：${sessionId}`);
        
        return result;
    }

    /**
     * 获取会话消息列表
     * @param {string} sessionId - 会话 ID
     * @returns {Promise<Array>} 消息列表
     */
    async getSessionMessages(sessionId) {
        if (!this.agentManager) {
            console.warn('[ChatManager] agentManager 未初始化，无法获取会话消息');
            return [];
        }
        return await this.agentManager.getSessionMessages(sessionId);
    }
    
    /**
     * 获取或创建 Agent 上下文
     * @param {string} chatId - 聊天 ID
     * @returns {Object} Agent 上下文对象
     */
    #getOrCreateContext(chatId) {
        if (!this.#agentContextMap.has(chatId)) {
            this.#agentContextMap.set(chatId, {
                agentKey: null,
                sessionId: null,
                metadata: {},
                createdAt: Date.now(),
                updatedAt: Date.now()
            });
        }
        const context = this.#agentContextMap.get(chatId);
        context.updatedAt = Date.now();
        return context;
    }
    
    /**
     * 获取 Agent 上下文
     * @param {string} chatId - 聊天 ID
     * @returns {Object|null} Agent 上下文对象，如果不存在返回 null
     */
    getAgentContext(chatId) {
        return this.#agentContextMap.get(chatId) || null;
    }
    
    /**
     * 设置 Agent 元数据
     * @param {string} chatId - 聊天 ID
     * @param {string} key - 元数据键
     * @param {any} value - 元数据值
     */
    setAgentMetadata(chatId, key, value) {
        const context = this.#getOrCreateContext(chatId);
        context.metadata[key] = value;
        console.log(`[ChatManager] 已设置 chatId=${chatId} 的元数据 ${key}=${value}`);
    }
    
    /**
     * 获取 Agent 元数据
     * @param {string} chatId - 聊天 ID
     * @param {string} key - 元数据键
     * @returns {any} 元数据值，如果不存在返回 undefined
     */
    getAgentMetadata(chatId, key) {
        const context = this.#agentContextMap.get(chatId);
        return context?.metadata?.[key];
    }
    
    /**
     * 删除 Agent 上下文
     * @param {string} chatId - 聊天 ID
     * @returns {boolean} 是否删除成功
     */
    removeAgentContext(chatId) {
        const deleted = this.#agentContextMap.delete(chatId);
        if (deleted) {
            console.log(`[ChatManager] 已删除 chatId=${chatId} 的 Agent 上下文`);
        }
        return deleted;
    }
    
    /**
     * 获取所有 Agent 上下文
     * @returns {Map<string, Object>} Agent 上下文映射表
     */
    getAllAgentContexts() {
        return new Map(this.#agentContextMap);
    }
    
    /**
     * 清理过期的上下文（可选）
     * @param {number} maxAge - 最大存活时间（毫秒），默认 1 小时
     */
    cleanupExpiredContexts(maxAge = 3600000) {
        const now = Date.now();
        let count = 0;
        
        for (const [chatId, context] of this.#agentContextMap.entries()) {
            if (now - context.updatedAt > maxAge) {
                this.#agentContextMap.delete(chatId);
                count++;
                console.log(`[ChatManager] 清理过期上下文：chatId=${chatId}`);
            }
        }
        
        if (count > 0) {
            console.log(`[ChatManager] 共清理 ${count} 个过期上下文`);
        }
    }

    /**
     * 设置权限请求
     * @param {string} chatId - 聊天 ID
     * @param {string} permissionId - 权限 ID
     * @param {Object} details - 权限请求详情
     */
    setPermissionRequest(chatId, permissionId, details) {
        this.#permissionRequestMap.set(chatId, {
            permissionId,
            ...details
        });
        console.log(`[ChatManager] 设置权限请求：chatId=${chatId}, permissionId=${permissionId}`);
    }

    /**
     * 获取权限请求
     * @param {string} chatId - 聊天 ID
     * @returns {Object|null} 权限请求详情，如果不存在返回 null
     */
    getPermissionRequest(chatId) {
        return this.#permissionRequestMap.get(chatId) || null;
    }

    /**
     * 删除权限请求
     * @param {string} chatId - 聊天 ID
     * @returns {boolean} 是否删除成功
     */
    removePermissionRequest(chatId) {
        const deleted = this.#permissionRequestMap.delete(chatId);
        if (deleted) {
            console.log(`[ChatManager] 已删除权限请求：chatId=${chatId}`);
        }
        return deleted;
    }

    /**
     * 清理过期的权限请求
     * @param {number} maxAge - 最大存活时间（毫秒），默认 5 分钟
     */
    cleanupExpiredPermissionRequests(maxAge = 300000) {
        const now = Date.now();
        let count = 0;
        
        for (const [chatId, permissionRequest] of this.#permissionRequestMap.entries()) {
            if (now - permissionRequest.createdAt > maxAge) {
                this.#permissionRequestMap.delete(chatId);
                count++;
                console.log(`[ChatManager] 清理过期权限请求：chatId=${chatId}`);
            }
        }
        
        if (count > 0) {
            console.log(`[ChatManager] 共清理 ${count} 个过期权限请求`);
        }
    }

}

/**
 * 创建群聊管理器实例
 * @param {Object} [client] - 飞书客户端实例
 * @param {Object} [agentManager] - Agent 管理器实例（可选）
 * @returns {ChatManager} 群聊管理器实例
 */
export function createChatManager(client, agentManager = null) {
    return new ChatManager(client, agentManager);
}