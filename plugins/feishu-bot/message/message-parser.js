/**
 * OpenCode 响应消息解析器
 * 负责解析 OpenCode 响应的 parts 数组，提取文本和非文本内容
 */

/**
 * Part 类型定义
 * @typedef {Object} Part
 * @property {string} type - Part 类型 (text, image, code, reasoning, step-start, step-finish)
 * @property {string} id - Part ID
 * @property {string} sessionID - 会话 ID
 * @property {string} messageID - 消息 ID
 */

/**
 * 解析后的 Part 信息
 * @typedef {Object} ParsedPart
 * @property {string} type - Part 类型
 * @property {string} id - Part ID
 * @property {string} sessionId - 会话 ID
 * @property {string} messageId - 消息 ID
 * @property {boolean} isText - 是否为文本类型
 * @property {string} content - 解析后的内容
 * @property {Object} [rawData] - 原始数据（非文本类型时包含）
 */

/**
 * 解析 OpenCode 响应中的 parts
 * @param {Array} parts - OpenCode 响应的 parts 数组
 * @returns {Object} 解析结果 {textResponse, otherParts}
 */
export function parseOpenCodeParts(parts) {
    const textParts = [];
    const otherParts = [];
    
    if (!Array.isArray(parts)) {
        return { textResponse: '', otherParts: [] };
    }
    
    for (const part of parts) {
        const parsedPart = parsePartByType(part);
        
        if (parsedPart.isText) {
            textParts.push(parsedPart.content);
        } else {
            otherParts.push(parsedPart);
        }
    }
    
    return {
        textResponse: textParts.join('\n'),
        otherParts: otherParts
    };
}

/**
 * 根据 part 类型进行解析
 * @param {Part} part - 单个 part 对象
 * @returns {ParsedPart} 解析后的 part 信息
 */
export function parsePartByType(part) {
    const baseInfo = {
        type: part.type,
        id: part.id,
        sessionId: part.sessionID,
        messageId: part.messageID
    };
    
    switch (part.type) {
        case 'text':
            return {
                ...baseInfo,
                isText: true,
                content: part.text
            };
        
        case 'image':
            return {
                ...baseInfo,
                isText: false,
                content: '[图片内容待处理]',
                rawData: part
            };
        
        case 'code':
            return {
                ...baseInfo,
                isText: false,
                content: '[代码内容待处理]',
                rawData: part
            };
        
        case 'reasoning':
            return {
                ...baseInfo,
                isText: false,
                content: '[推理过程待处理]',
                rawData: part
            };
        
        case 'step-start':
        case 'step-finish':
            // 流程控制类型，不作为内容返回
            return {
                ...baseInfo,
                isText: false,
                content: '[流程控制]',
                rawData: part
            };
        
        default:
            return {
                ...baseInfo,
                isText: false,
                content: `[未知类型：${part.type}]`,
                rawData: part
            };
    }
}

/**
 * 提取 AI 回复内容
 * @param {Object} result - OpenCode 响应结果
 * @param {string} userMessage - 用户原始消息
 * @returns {Object} {aiResponse, otherParts}
 */
export function extractAIResponse(result, userMessage) {
    let aiResponse = '收到您的消息';
    let otherParts = [];
    
    // 优先从 parts 中提取
    if (result.data && result.data.parts && Array.isArray(result.data.parts)) {
        const parsed = parseOpenCodeParts(result.data.parts);
        aiResponse = parsed.textResponse || aiResponse;
        otherParts = parsed.otherParts;
        
        // 调试信息
        if (otherParts.length > 0) {
            logOtherPartStats(otherParts);
        }
    }
    // 兼容旧格式
    else if (result.data && result.data.info) {
        aiResponse = result.data.info.summary || userMessage;
    } else if (result.info) {
        aiResponse = result.info.summary || userMessage;
    }
    
    return { aiResponse, otherParts };
}

/**
 * 记录非文本 part 的统计信息
 * @param {Array} otherParts - 非文本 part 数组
 */
export function logOtherPartStats(otherParts) {
    const typeCounts = {};
    otherParts.forEach(p => {
        typeCounts[p.type] = (typeCounts[p.type] || 0) + 1;
    });
}
