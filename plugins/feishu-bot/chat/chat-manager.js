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
 * 群聊管理器类
 */
export class ChatManager {
    constructor(client) {
        this.client = client || createFeishuClient();
    }

    /**
     * 创建群聊
     * @param {Object} options - 创建选项
     * @param {string} options.name - 群名称
     * @param {string} [options.description] - 群描述
     * @param {string[]} options.user_id_list - 初始成员 open_id 列表
     * @param {string} [options.chat_mode='group'] - 群聊模式
     * @param {string} [options.chat_type='private'] - 群类型
     * @returns {Promise<Object>} 创建结果 { chat_id, name }
     */
    async createChat(options) {
        const { name, description, user_id_list, chat_mode = 'group', chat_type = 'private' } = options;

        if (!name) {
            throw new Error('群名称不能为空');
        }
        if (!user_id_list || user_id_list.length === 0) {
            throw new Error('至少需要一个初始成员');
        }

        try {
            const response = await this.client.im.chat.create({
                data: {
                    name,
                    description: description || '',
                    user_id_list,
                    chat_mode,
                    chat_type
                }
            });

            console.log(`[ChatManager] 群聊创建成功: ${name}`);
            return {
                chat_id: response.data.chat_id,
                name: response.data.name
            };
        } catch (error) {
            console.error('[ChatManager] 创建群聊失败:', error.message);
            throw error;
        }
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
}

/**
 * 创建群聊管理器实例
 * @param {Object} [client] - 飞书客户端实例
 * @returns {ChatManager} 群聊管理器实例
 */
export function createChatManager(client) {
    return new ChatManager(client);
}