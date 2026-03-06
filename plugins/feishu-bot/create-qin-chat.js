/**
 * 创建名为'琴女'的群聊脚本
 */

import { createChatManager } from './chat/index.js';
import * as lark from '@larksuiteoapi/node-sdk';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(__dirname, '.env') });

const feishuClient = new lark.Client({
    appId: process.env.FEISHU_APP_ID,
    appSecret: process.env.FEISHU_APP_SECRET
});

const chatManager = createChatManager(feishuClient);

async function createQinChat() {
    try {
        const result = await chatManager.createChat({
            name: '琴女',
            description: '琴女群聊',
            user_id_list: [process.env.FEISHU_USER_ID],
            chat_mode: 'group',
            chat_type: 'private'
        });
        
        console.log('群聊创建成功:', result);
        console.log('群聊 ID:', result.chat_id);
        console.log('群聊名称:', result.name);
    } catch (error) {
        console.error('创建群聊失败:', error.message);
        throw error;
    }
}

createQinChat().catch(console.error);
