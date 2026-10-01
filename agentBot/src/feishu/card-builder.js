/**
 * 飞书卡片构建器
 * 构建带选项按钮的提问卡片与按钮点击后的回执卡片
 * 卡片回调（card.action.trigger）返回的卡片 JSON 会被飞书原地替换展示
 */

import { CardActionType } from '../constants.js';

/** 单张卡片最多渲染按钮的选项数，超出时降级为文字列表（飞书单卡片元素数有限制） */
const MAX_BUTTON_OPTIONS = 6;

/**
 * 构建提问卡片：每个问题一组选项按钮，按钮 value 内嵌 requestId/qIndex/label
 * @param {Array<{question:string, header:string, options:Array<{label:string, description:string}>, multiple?:boolean}>} questions
 * @param {string} requestId - OpenCode question 请求 ID
 * @returns {Object} 飞书卡片 JSON
 */
export function buildQuestionCard(questions, requestId) {
    const elements = [];
    questions.forEach((q, qIndex) => {
        // 问题正文（含多选标识）
        const multiTag = q.multiple ? '（多选，请打字回复）' : '';
        elements.push({
            tag: 'div',
            text: {
                tag: 'lark_md',
                content: `**${qIndex + 1}. ${q.question}**${multiTag}`,
            },
        });

        const options = q.options || [];
        if (options.length > 0 && options.length <= MAX_BUTTON_OPTIONS && !q.multiple) {
            // 选项按钮组：点击后由 card.action.trigger 回调闭环
            elements.push({
                tag: 'action',
                actions: options.map((option) => ({
                    tag: 'button',
                    text: { tag: 'plain_text', content: option.label },
                    type: 'default',
                    value: {
                        type: CardActionType.QUESTION_REPLY,
                        requestId,
                        qIndex,
                        label: option.label,
                    },
                })),
            });
            // 选项说明（label + description）
            const desc = options
                .map((option) => `- **${option.label}**：${option.description}`)
                .join('\n');
            elements.push({ tag: 'div', text: { tag: 'lark_md', content: desc } });
        } else if (options.length > 0) {
            // 选项过多或多选题：降级为文字列表，走打字回复闭环
            const labels = options.map((option) => option.label).join(' / ');
            elements.push({
                tag: 'div',
                text: { tag: 'lark_md', content: `选项：${labels}` },
            });
        }
    });

    elements.push({ tag: 'hr' });
    elements.push({
        tag: 'note',
        elements: [{
            tag: 'plain_text',
            content: '💡 点击选项作答，也可直接打字回复；超时未回复将自动拒绝本次提问',
        }],
    });

    return {
        config: { wide_screen_mode: true },
        header: {
            title: { tag: 'plain_text', content: '🤔 Agent 提问' },
            template: 'orange',
        },
        elements,
    };
}

/**
 * 构建回执卡片（按钮点击后原地替换原提问卡片）
 * @param {string} title - 标题
 * @param {string} content - lark_md 内容
 * @param {'blue'|'green'|'red'|'grey'|'orange'} [template] - 标题栏配色
 * @returns {Object} 飞书卡片 JSON
 */
export function buildReceiptCard(title, content, template = 'green') {
    return {
        config: { wide_screen_mode: true },
        header: { title: { tag: 'plain_text', content: title }, template },
        elements: [{ tag: 'div', text: { tag: 'lark_md', content } }],
    };
}
