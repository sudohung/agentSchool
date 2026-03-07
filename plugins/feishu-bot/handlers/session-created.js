import { EventHandler } from './handler.js';
import { sendEventNotification } from '../webhook/index.js';

export class SessionCreatedHandler extends EventHandler {
    constructor(project) {
        super('session.created');
        this.project = project;
    }

    async process(event, context) {
        return await sendEventNotification(
            "OpenCode 会话已创建",
            `项目：${this.project?.name || '未知'}\n会话 ID: ${event.session.id}`
        );
    }
}
