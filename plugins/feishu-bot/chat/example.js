/**
 * 群聊管理模块使用示例
 * 演示如何创建群聊、添加成员、发送消息等操作
 */

import { createChatManager } from './index.js';
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

/**
 * 示例1：创建群聊
 */
async function exampleCreateChat() {
    try {
        const result = await chatManager.createChat({
            name: '测试群聊',
            description: '这是一个测试群',
            user_id_list: ['ou_xxxxxx'], // 替换为实际的 open_id
            chat_mode: 'group',
            chat_type: 'private'
        });
        
        console.log('群聊创建成功:', result);
        return result.chat_id;
    } catch (error) {
        console.error('创建群聊失败:', error.message);
    }
}

/**
 * 示例2：添加成员到群聊
 */
async function exampleAddMembers(chatId) {
    try {
        const result = await chatManager.addMembers(chatId, [
            'ou_yyyyyy', // 替换为实际的 open_id
            'ou_zzzzzz'
        ]);
        
        console.log('成员添加结果:', result);
    } catch (error) {
        console.error('添加成员失败:', error.message);
    }
}

/**
 * 示例3：获取群信息
 */
async function exampleGetChatInfo(chatId) {
    try {
        const info = await chatManager.getChatInfo(chatId);
        console.log('群信息:', info);
        return info;
    } catch (error) {
        console.error('获取群信息失败:', error.message);
    }
}

/**
 * 示例4：获取群成员列表
 */
async function exampleGetMembers(chatId) {
    try {
        const result = await chatManager.getMembers(chatId);
        console.log('群成员列表:', result.members);
        console.log('成员数量:', result.members.length);
    } catch (error) {
        console.error('获取群成员失败:', error.message);
    }
}

/**
 * 示例5：发送群消息
 */
async function exampleSendMessage(chatId) {
    try {
        const result = await chatManager.sendMessage(
            chatId,
            '大家好，这是机器人发送的测试消息！'
        );
        console.log('消息发送结果:', result);
    } catch (error) {
        console.error('发送消息失败:', error.message);
    }
}

/**
 * 示例6：更新群信息
 */
async function exampleUpdateChatInfo(chatId) {
    try {
        const result = await chatManager.updateChatInfo(chatId, {
            name: '新群名称',
            description: '更新后的群描述'
        });
        console.log('更新结果:', result);
    } catch (error) {
        console.error('更新群信息失败:', error.message);
    }
}

/**
 * 示例7：移除成员
 */
async function exampleRemoveMembers(chatId) {
    try {
        const result = await chatManager.removeMembers(chatId, ['ou_yyyyyy']);
        console.log('移除成员结果:', result);
    } catch (error) {
        console.error('移除成员失败:', error.message);
    }
}

/**
 * 示例8：解散群聊
 */
async function exampleDisbandChat(chatId) {
    try {
        const result = await chatManager.disbandChat(chatId);
        console.log('解散结果:', result);
    } catch (error) {
        console.error('解散群聊失败:', error.message);
    }
}

/**
 * 主函数 - 运行所有示例
 */
async function main() {
    console.log('=== 飞书群聊管理模块示例 ===\n');
    
    // 1. 创建群聊
    console.log('1. 创建群聊...');
    const chatId = await exampleCreateChat();
    
    if (chatId) {
        // 2. 获取群信息
        console.log('\n2. 获取群信息...');
        await exampleGetChatInfo(chatId);
        
        // 3. 添加成员
        console.log('\n3. 添加成员...');
        await exampleAddMembers(chatId);
        
        // 4. 获取成员列表
        console.log('\n4. 获取成员列表...');
        await exampleGetMembers(chatId);
        
        // 5. 发送消息
        console.log('\n5. 发送消息...');
        await exampleSendMessage(chatId);
        
        // 6. 更新群信息
        console.log('\n6. 更新群信息...');
        await exampleUpdateChatInfo(chatId);
        
        // 7. 移除成员
        // console.log('\n7. 移除成员...');
        // await exampleRemoveMembers(chatId);
        
        // 8. 解散群聊（谨慎操作）
        // console.log('\n8. 解散群聊...');
        // await exampleDisbandChat(chatId);
    }
}

main().catch(console.error);