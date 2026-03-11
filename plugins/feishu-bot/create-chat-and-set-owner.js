/**
 * 创建群聊并设置群主脚本
 * 1. 创建群聊
 * 2. 将群主转让给指定用户
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

const USER_INFO = {
    open_id: 'ou_876aae79dd601923ba73d825d5e1d155',
    union_id: 'on_006375bc8efbc960f1a698e9b920f48c'
};

async function createChatAndSetOwner() {
    try {
        console.log('=== 步骤1: 创建群聊 ===');
        console.log('使用用户 open_id:', USER_INFO.open_id);
        
        const createResult = await chatManager.createChat({
            name: '新建群聊',
            description: '新建群聊',
            user_id_list: [USER_INFO.open_id],
            owner_id: USER_INFO.open_id,
            chat_mode: 'group',
            chat_type: 'private'
        });
        
        console.log('\n✅ 群聊创建成功!');
        console.log('群聊 ID:', createResult.chat_id);
        console.log('群聊名称:', createResult.name);

        console.log('\n=== 步骤2: 设置群主 ===');
        const ownerResult = await chatManager.setOwner(
            createResult.chat_id,
            USER_INFO.open_id,
            'open_id'
        );
        
        console.log('\n✅ 群主设置成功!');
        console.log('新群主 ID:', ownerResult.owner_id);
        
        return {
            chat_id: createResult.chat_id,
            chat_name: createResult.name,
            owner_id: ownerResult.owner_id
        };
    } catch (error) {
        console.error('❌ 操作失败:', error.message);
        if (error.response?.data) {
            console.error('详细错误:', JSON.stringify(error.response.data, null, 2));
        }
        throw error;
    }
}

createChatAndSetOwner().catch(console.error);