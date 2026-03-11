import * as lark from '@larksuiteoapi/node-sdk';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readFileSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(__dirname, '.env') });

const feishuClient = new lark.Client({
    appId: process.env.FEISHU_APP_ID,
    appSecret: process.env.FEISHU_APP_SECRET
});

async function createDocument() {
    try {
        const readmePath = join(__dirname, 'README.md');
        const readmeContent = readFileSync(readmePath, 'utf-8');

        const response = await feishuClient.docx.document.create({
            data: {
                title: '飞书机器人插件使用文档'
            }
        });

        const documentId = response.data.document.document_id;
        console.log('文档创建成功！');
        console.log('文档 ID:', documentId);
        console.log('文档标题:', response.data.document.title);
        
        const convertResponse = await feishuClient.docx.document.convert({
            data: {
                content_type: 'markdown',
                content: readmeContent
            }
        });
        
        const blocks = convertResponse.data.blocks;
        if (blocks && blocks.length > 0) {
            const children = blocks.map(block => ({
                block_type: block.block_type,
                text: block.text,
                heading1: block.heading1,
                heading2: block.heading2,
                heading3: block.heading3,
                bullet: block.bullet,
                ordered: block.ordered,
                code: block.code
            }));
            
            const batchSize = 50;
            for (let i = 0; i < children.length; i += batchSize) {
                const batch = children.slice(i, i + batchSize);
                await feishuClient.docx.documentBlockChildren.create({
                    path: { 
                        document_id: documentId,
                        block_id: documentId
                    },
                    data: {
                        children: batch
                    }
                });
                console.log(`已添加 ${Math.min(i + batchSize, children.length)}/${children.length} 个块`);
            }
        }
        
        console.log('文档内容已更新！');
        console.log('访问链接:', `https://feishu.cn/docx/${documentId}`);
    } catch (error) {
        console.error('创建文档失败:', error.message);
        if (error.response) {
            console.error('错误详情:', JSON.stringify(error.response.data, null, 2));
        }
    }
}

createDocument();
