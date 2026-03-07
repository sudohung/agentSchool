import { EventHandler } from './handler.js';
import { sendEventNotification } from '../webhook/index.js';

export class ToolExecuteHandler extends EventHandler {
    constructor() {
        super('tool.execute.after');
    }

    async process(event, context) {
        const toolName = event.tool?.name;
        if (!toolName) return null;

        return await sendEventNotification(
            `工具执行：${toolName}`,
            `工具 ${toolName} 已执行完成`
        );
    }
}
