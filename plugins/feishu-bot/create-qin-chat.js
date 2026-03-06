/**
 * 创建名为'新建群聊'的群聊脚本
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
    open_id: 'ou_876aae79dd601923ba73d825d5e1d155',
    union_id: 'on_006375bc8efbc960f1a698e9b920f48c'
};

async function createQinChat() {
    try {
        console.log('正在创建群聊...');
        console.log('使用用户 open_id:', USER_INFO.open_id);
        
        const result = await chatManager.createChat({
            name: '新建群聊',
            description: '新建群聊',
            owner_id: USER_INFO.open_id,
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
