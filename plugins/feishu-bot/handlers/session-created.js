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
            `会话 ID: ${event.properties?.info?.id}`
        );
    }
}
