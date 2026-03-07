/**
 * 设置群主脚本
 * 将指定群聊的群主转让给指定用户
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

// 配置信息
const CONFIG = {
    chat_id: 'oc_xxxxxxxxxxxxxxxx',
    new_owner_open_id: 'ou_876aae79dd601923ba73d825d5e1d155'
};

async function setChatOwner() {
    try {
        console.log('正在设置群主...');
        console.log('群ID:', CONFIG.chat_id);
        console.log('新群主 open_id:', CONFIG.new_owner_open_id);
        
        const result = await chatManager.setOwner(
            CONFIG.chat_id,
            CONFIG.new_owner_open_id,
            'open_id'
        );
        
        console.log('\n✅ 群主设置成功!');
        console.log('新群主 ID:', result.owner_id);
        return result;
    } catch (error) {
        console.error('❌ 设置群主失败:', error.message);
        if (error.response?.data) {
            console.error('详细错误:', JSON.stringify(error.response.data, null, 2));
        }
        throw error;
    }
}

setChatOwner().catch(console.error);