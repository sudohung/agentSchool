import { EventHandler } from './handler.js';
import { sendErrorMessage } from '../webhook/index.js';

export class SessionErrorHandler extends EventHandler {
    constructor() {
        super('session.error');
    }

    async process(event, context) {
        return await sendErrorMessage(
            event.error?.message,
            "❌ 发生错误"
        );
    }
}
