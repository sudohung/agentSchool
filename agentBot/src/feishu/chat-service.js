/**
 * 飞书群聊服务
 * 单一职责：只封装飞书 IM 群相关 API 与客户端持有
 * Agent 上下文/权限状态由 SessionManager 负责（拆分旧版 ChatManager 神类）
 */

/**
 * 群聊服务类
 */
export class ChatService {
    /**
     * @param {lark.Client} client - 飞书客户端实例
     */
    constructor(client) {
        if (!client) {
            throw new Error('ChatService 初始化失败：缺少飞书客户端');
        }
        this.client = client;
    }

    /** 获取飞书客户端实例 */
    getClient() {
        return this.client;
    }

    /**
     * 发送群消息（通用）
     * @param {string} chatId
     * @param {string} content - 文本内容或 JSON 字符串（非 text 类型）
     * @param {string} [msgType='text']
     */
    async sendMessage(chatId, content, msgType = 'text') {
        if (!chatId) throw new Error('发送消息失败：chatId 为空');
        const data = {
            receive_id: chatId,
            msg_type: msgType,
            content: msgType === 'text' ? JSON.stringify({ text: content }) : content,
        };
        const res = await this.client.im.message.create({
            params: { receive_id_type: 'chat_id' },
            data,
        });
        return { success: true, message_id: res.data?.message_id };
    }

    /**
     * 创建群聊
     * @param {{name:string, description?:string, userIdList:string[], chatType?:string}} options
     */
    async createChat({ name, description = '', userIdList, chatType = 'private' }) {
        if (!name) throw new Error('创建群聊失败：群名称为空');
        if (!userIdList?.length) throw new Error('创建群聊失败：至少需要一个初始成员');

        const res = await this.client.im.chat.create({
            data: {
                name,
                description,
                user_id_list: userIdList,
                chat_mode: 'group',
                chat_type: chatType,
            },
        });
        return {
            chatId: res.data?.chat_id,
            name: res.data?.name,
            chatType,
        };
    }

    /**
     * 添加群成员
     * @param {string} chatId
     * @param {string[]} userIdList
     */
    async addMembers(chatId, userIdList) {
        if (!chatId || !userIdList?.length) throw new Error('添加成员失败：参数不完整');
        const res = await this.client.im.chatMembers.create({
            path: { chat_id: chatId },
            data: { member_id_type: 'open_id', user_id_list: userIdList },
        });
        return { added: userIdList.length, invalid: res.data?.invalid_users || [] };
    }

    /**
     * 移除群成员
     * @param {string} chatId
     * @param {string[]} userIdList
     */
    async removeMembers(chatId, userIdList) {
        if (!chatId || !userIdList?.length) throw new Error('移除成员失败：参数不完整');
        await this.client.im.chatMembers.delete({
            path: { chat_id: chatId },
            data: { member_id_type: 'open_id', user_id_list: userIdList },
        });
        return { removed: userIdList.length };
    }

    /**
     * 获取群信息
     * @param {string} chatId
     */
    async getChatInfo(chatId) {
        if (!chatId) throw new Error('获取群信息失败：chatId 为空');
        const res = await this.client.im.chat.get({ path: { chat_id: chatId } });
        return res.data;
    }
}
