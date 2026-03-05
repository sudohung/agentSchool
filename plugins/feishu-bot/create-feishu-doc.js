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

async function createDocument() {
    try {
        const response = await feishuClient.docx.document.create({
            data: {
                title: '使用文档'
            }
        });

        console.log('文档创建成功！');
        console.log('文档 ID:', response.data.document.document_id);
        console.log('文档标题:', response.data.document.title);
        console.log('访问链接:', `https://feishu.cn/docx/${response.data.document.document_id}`);
    } catch (error) {
        console.error('创建文档失败:', error.message);
        if (error.response) {
            console.error('错误详情:', error.response.data);
        }
    }
}

createDocument();