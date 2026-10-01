/**
 * 飞书群聊服务
 * 单一职责：只封装飞书 IM 群相关 API 与客户端持有
 * Agent 上下文/权限状态由 SessionManager 负责（拆分旧版 ChatManager 神类）
 */

/**
 * 群聊服务类
 */
export class ChatService {
    /** @type {{openId:string}|null} 机器人自身信息缓存 */
    #botInfo = null;

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
     * 获取机器人自身 open_id（用于从 @ 名单中排除自己），结果缓存
     * @returns {Promise<string>} 获取失败返回空字符串
     */
    async getBotOpenId() {
        if (this.#botInfo) return this.#botInfo.openId || '';
        try {
            const res = await this.client.request({ method: 'GET', url: '/open-apis/bot/v3/info' });
            const openId = res?.data?.open_id || res?.open_id || '';
            this.#botInfo = { openId };
            return openId;
        } catch (error) {
            console.warn(`[ChatService] 获取机器人信息失败: ${error.message}`);
            return '';
        }
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

    /**
     * 按消息 ID 查询消息（引用回复场景反查父消息）
     * @param {string} messageId
     * @returns {Promise<{messageId:string, parentId:string, msgType:string, text:string}|null>} 无权限/不存在时返回 null
     */
    async getMessageById(messageId) {
        if (!messageId) return null;
        try {
            const res = await this.client.im.v1.message.get({ path: { message_id: messageId } });
            const item = res.data?.items?.[0];
            if (!item) return null;
            return {
                messageId: item.message_id,
                parentId: item.parent_id || '',
                msgType: item.msg_type,
                text: extractMessageText(item.msg_type, item.body?.content || ''),
            };
        } catch (error) {
            console.warn(`[ChatService] 查询消息失败 ${messageId}: ${error.message}`);
            return null;
        }
    }
}

/**
 * 从消息 body.content 中提取可读文本（text/post/interactive 三类，其他类型给占位符）
 * @param {string} msgType
 * @param {string} content - 消息 content JSON 字符串
 * @returns {string}
 */
export function extractMessageText(msgType, content) {
    let parsed;
    try {
        parsed = JSON.parse(content || '{}');
    } catch {
        return '';
    }

    switch (msgType) {
        case 'text':
            return (parsed.text || '').trim();
        case 'post': {
            // 富文本：结构可能多层嵌套（content.post.<locale>.content 为段落数组），递归收集段落节点
            const root = parsed.content || {};
            const out = [];
            if (root.title) out.push(root.title);
            const collect = (node) => {
                if (!node || typeof node !== 'object' || Array.isArray(node)) return;
                if (Array.isArray(node.content)) {
                    if (node.title && node.title !== root.title) out.push(node.title);
                    for (const paragraph of node.content) {
                        const line = (paragraph || []).map((el) => {
                            if (!el || typeof el !== 'object') return '';
                            if (el.tag === 'text' || el.tag === 'a') return el.text || '';
                            if (el.tag === 'at') return `@${el.user_name || el.user_id || '某人'}`;
                            if (el.tag === 'img') return '[图片]';
                            if (el.tag === 'emotion') return el.emoji || '';
                            return '';
                        }).join('').trim();
                        if (line) out.push(line);
                    }
                    return;
                }
                for (const value of Object.values(node)) collect(value);
            };
            collect(root);
            return out.join('\n').trim();
        }
        case 'interactive': {
            // 卡片提取，兼容三种结构：
            // 1) 新版 schema 2.0：elements 数组，文本节点 tag=markdown/plain_text，内容在 content
            // 2) 新版 v1 语法：文本节点 tag=lark_md，内容在 content
            // 3) 旧版消息卡：elements 为段落数组的数组，节点 tag=text/a，内容在 text 属性
            const textTags = new Set(['plain_text', 'lark_md', 'markdown']);
            const walk = (node) => {
                if (typeof node === 'string' || !node) return '';
                if (Array.isArray(node)) {
                    const parts = node.map(walk).filter(Boolean);
                    // 元素是数组的段落结构：段落间换行；否则视为行内元素，直接拼接
                    return node.some((x) => Array.isArray(x)) ? parts.join('\n') : parts.join('');
                }
                if (typeof node === 'object') {
                    if (textTags.has(node.tag)) return node.content || '';
                    if (node.tag === 'text' || node.tag === 'a') return node.text || '';
                    if (node.tag === 'at') return `@${node.user_name || node.user_id || '某人'}`;
                    if (node.tag === 'img') return '[图片]';
                    if (node.tag === 'hr') return '';
                    // div/header/note 等容器：递归子字段
                    return Object.values(node).map(walk).filter(Boolean).join('\n');
                }
                return '';
            };
            const parts = [];
            // 旧版卡片 title 是纯字符串
            if (typeof parsed.title === 'string' && parsed.title) parts.push(parsed.title);
            parts.push(walk(parsed));
            return parts.filter(Boolean).join('\n').trim();
        }
        case 'image':
            return '[图片]';
        case 'file':
            return `[文件:${parsed.file_name || '未命名'}]`;
        case 'audio':
            return '[语音]';
        case 'media':
            return '[视频]';
        default:
            return `[不支持的消息类型:${msgType}]`;
    }
}
