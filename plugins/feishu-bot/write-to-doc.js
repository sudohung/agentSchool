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

const documentId = 'Pdl2dTmHvocxUSxhYFscDkOVnUd';

async function addContentToDocument() {
    try {
        const response = await feishuClient.docx.documentBlockChildren.create({
            path: {
                document_id: documentId,
                block_id: documentId
            },
            data: {
                children: [
                    {
                        block_type: 2,
                        text: {
                            elements: [
                                {
                                    text_run: {
                                        content: '欢迎使用 OpenCode 飞书机器人插件！'
                                    }
                                }
                            ],
                            style: {}
                        }
                    },
                    {
                        block_type: 2,
                        text: {
                            elements: [
                                {
                                    text_run: {
                                        content: ''
                                    }
                                }
                            ],
                            style: {}
                        }
                    },
                    {
                        block_type: 2,
                        text: {
                            elements: [
                                {
                                    text_run: {
                                        content: '这是一个基于 OpenCode 平台的飞书通知插件，支持以下功能：'
                                    }
                                }
                            ],
                            style: {}
                        }
                    },
                    {
                        block_type: 2,
                        text: {
                            elements: [
                                {
                                    text_run: {
                                        content: '• 实时接收飞书消息并转发给 OpenCode AI'
                                    }
                                }
                            ],
                            style: {}
                        }
                    },
                    {
                        block_type: 2,
                        text: {
                            elements: [
                                {
                                    text_run: {
                                        content: '• 支持消息去重和过期处理'
                                    }
                                }
                            ],
                            style: {}
                        }
                    },
                    {
                        block_type: 2,
                        text: {
                            elements: [
                                {
                                    text_run: {
                                        content: '• 支持 WebSocket 长连接'
                                    }
                                }
                            ],
                            style: {}
                        }
                    },
                    {
                        block_type: 2,
                        text: {
                            elements: [
                                {
                                    text_run: {
                                        content: '• 支持事件监听和通知'
                                    }
                                }
                            ],
                            style: {}
                        }
                    },
                    {
                        block_type: 2,
                        text: {
                            elements: [
                                {
                                    text_run: {
                                        content: ''
                                    }
                                }
                            ],
                            style: {}
                        }
                    },
                    {
                        block_type: 2,
                        text: {
                            elements: [
                                {
                                    text_run: {
                                        content: '快速开始：'
                                    }
                                }
                            ],
                            style: {}
                        }
                    },
                    {
                        block_type: 2,
                        text: {
                            elements: [
                                {
                                    text_run: {
                                        content: '1. 配置环境变量（FEISHU_APP_ID、FEISHU_APP_SECRET）'
                                    }
                                }
                            ],
                            style: {}
                        }
                    },
                    {
                        block_type: 2,
                        text: {
                            elements: [
                                {
                                    text_run: {
                                        content: '2. 启动插件：在 OpenCode 中加载此插件'
                                    }
                                }
                            ],
                            style: {}
                        }
                    },
                    {
                        block_type: 2,
                        text: {
                            elements: [
                                {
                                    text_run: {
                                        content: '3. 在飞书中发送消息给机器人即可开始使用'
                                    }
                                }
                            ],
                            style: {}
                        }
                    }
                ],
                index: 0
            }
        });

        console.log('✅ 内容添加成功！');
        console.log('📄 文档链接: https://feishu.cn/docx/' + documentId);
    } catch (error) {
        console.error('❌ 添加内容失败:', error.message);
        if (error.response) {
            console.error('错误详情:', JSON.stringify(error.response.data, null, 2));
        }
    }
}

addContentToDocument();