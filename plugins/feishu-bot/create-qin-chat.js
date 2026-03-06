/**
 * 创建名为'琴女'的群聊脚本
 * 使用指定的 open_id 创建群聊
 */

import { createChatManager } from './chat/index.js';
import * as lark from '@larksuiteoapi/node-sdk';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(__dirname, '../.env') });

const feishuClient = new lark.Client({
    appId: process.env.FEISHU_APP_ID,
    appSecret: process.env.FEISHU_APP_SECRET
});

const chatManager = createChatManager(feishuClient);

// 用户信息
const USER_INFO = {
    open_id: 'ou_03bddb45268dc5a725067f671a8e8c80',
    union_id: 'on_a5e4f1a44ec54825be879f0ff634f25a'
};

async function createQinChat() {
    try {
        console.log('正在创建群聊...');
        console.log('使用用户 open_id:', USER_INFO.open_id);
        
        const result = await chatManager.createChat({
            name: '琴女',
            description: '琴女群聊',
            user_id_list: [USER_INFO.open_id],
            chat_mode: 'group',
            chat_type: 'private'
        });
        
        console.log('\n✅ 群聊创建成功!');
        console.log('群聊 ID:', result.chat_id);
        console.log('群聊名称:', result.name);
        return result;
    } catch (error) {
        console.error('❌ 创建群聊失败:', error.message);
        if (error.response?.data) {
            console.error('详细错误:', JSON.stringify(error.response.data, null, 2));
        }
        throw error;
    }
}

createQinChat().catch(console.error);
