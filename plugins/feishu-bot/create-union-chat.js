/**
 * 创建外部群/联合群脚本
 * 演示如何使用机器人创建跨组织群聊
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

// 用户信息示例
const INTERNAL_USER = {
    open_id: 'ou_03bddb45268dc5a725067f671a8e8c80',
    union_id: 'on_a5e4f1a44ec54825be879f0ff634f25a'
};

// 外部用户示例（需要替换为实际的 union_id）
const EXTERNAL_USER = {
    union_id: 'on_external_user_xxxxx' // 替换为外部用户的实际 union_id
};

/**
 * 创建普通群聊（内部群）
 */
async function createInternalChat() {
    try {
        console.log('=== 创建内部群聊 ===\n');
        
        const result = await chatManager.createChat({
            name: '内部协作群',
            description: '团队内部协作群',
            user_id_list: [INTERNAL_USER.open_id],
            user_id_type: 'open_id',
            chat_mode: 'group',
            chat_type: 'private'
        });
        
        console.log('✅ 内部群创建成功:');
        console.log('  群 ID:', result.chat_id);
        console.log('  群名称:', result.name);
        console.log('  群类型:', result.chat_type);
        console.log();
        
        return result;
    } catch (error) {
        console.error('❌ 创建内部群失败:', error.message);
        throw error;
    }
}

/**
 * 创建外部群/联合群
 */
async function createUnionChat() {
    try {
        console.log('=== 创建外部群/联合群 ===\n');
        
        const result = await chatManager.createUnionChat({
            name: '跨组织协作群',
            description: '与外部合作伙伴的协作群',
            member_list: [
                { open_id: INTERNAL_USER.open_id },     // 内部用户使用 open_id
                { union_id: EXTERNAL_USER.union_id }    // 外部用户必须使用 union_id
            ]
        });
        
        console.log('✅ 外部群创建成功:');
        console.log('  群 ID:', result.chat_id);
        console.log('  群名称:', result.name);
        console.log('  群类型:', result.chat_type);
        console.log();
        
        return result;
    } catch (error) {
        console.error('❌ 创建外部群失败:', error.message);
        if (error.response?.data) {
            console.error('错误详情:', JSON.stringify(error.response.data, null, 2));
        }
        throw error;
    }
}

/**
 * 使用 createChat 方法创建外部群（另一种方式）
 */
async function createUnionChatAlt() {
    try {
        console.log('=== 使用 createChat 创建外部群 ===\n');
        
        const result = await chatManager.createChat({
            name: '跨组织项目群',
            description: '项目协作群',
            user_id_list: [INTERNAL_USER.union_id],
            user_id_type: 'union_id',
            chat_mode: 'group',
            chat_type: 'union'
        });
        
        console.log('✅ 外部群创建成功:');
        console.log('  群 ID:', result.chat_id);
        console.log('  群名称:', result.name);
        console.log();
        
        return result;
    } catch (error) {
        console.error('❌ 创建外部群失败:', error.message);
        throw error;
    }
}

/**
 * 主函数
 */
async function main() {
    console.log('🚀 开始测试飞书群聊创建\n');
    console.log('⚠️  注意：创建外部群需要：');
    console.log('  1. 应用已申请 im:union_chat 权限');
    console.log('  2. 双方企业已建立飞书商务合作关系');
    console.log('  3. 外部用户使用 union_id\n');
    
    try {
        // 1. 创建内部群（测试基本功能）
        await createInternalChat();
        
        // 2. 尝试创建外部群（需要配置真实的 union_id）
        // await createUnionChat();
        
        console.log('✅ 所有测试完成');
    } catch (error) {
        console.error('\n❌ 测试失败:', error.message);
        process.exit(1);
    }
}

// 只运行创建内部群
createInternalChat().catch(console.error);

// 如需测试外部群，请取消注释并配置真实的外部用户 union_id
// main().catch(console.error);