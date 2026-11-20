/**
 * OpenCode 事件归一化
 *
 * 把 v1（{type, properties}）与 v2（{type, data}）的原始事件转成内部统一事件：
 *   text / reasoning / tool / idle / error / question / questionClosed / permission / status / retry
 *
 * 这里保持纯逻辑（不碰网络、不发请求），便于单测。
 */

/** v1 的 delta 只带 partID，需要靠 part.updated 建立类型映射 */
const PART_TYPE_CACHE_LIMIT = 2000;

export class EventNormalizer {
    /** @type {Map<string, string>} partID -> part.type */
    #partTypes = new Map();

    /**
     * 归一化一帧
     * @param {any} payload 事件体
     * @param {string} [eventName] SSE 的 event: 字段
     * @returns {Array<Object>}
     */
    normalize(payload, eventName = '') {
        const type = payload?.type || eventName;
        if (!type) return [];
        if (payload?.properties) return this.#normalizeV1(type, payload.properties);
        if (payload?.data !== undefined) return this.#normalizeV2(type, payload.data);
        return [];
    }

    /** 清空 part 类型缓存 */
    reset() {
        this.#partTypes.clear();
    }

    /**
     * v1 事件（properties 结构）
     * @param {string} type
     * @param {Object} props
     */
    #normalizeV1(type, props) {
        const sessionId = props?.sessionID;
        switch (type) {
            case 'message.part.delta': {
                if (!sessionId || !props.delta) return [];
                const partType = this.#partTypes.get(props.partID) || '';
                return [{
                    kind: partType === 'reasoning' ? 'reasoning' : 'text',
                    sessionId,
                    delta: props.delta,
                }];
            }
            case 'message.part.updated': {
                const part = props.part || {};
                if (part.id && part.type) this.#rememberPartType(part.id, part.type);
                if (part.type === 'tool' && part.state) {
                    return [{
                        kind: 'tool',
                        sessionId,
                        tool: part.tool,
                        status: part.state.status,
                        title: part.state.title || part.tool,
                    }];
                }
                return [];
            }
            case 'session.idle':
                return sessionId ? [{ kind: 'idle', sessionId }] : [];
            case 'session.error':
                return sessionId ? [{ kind: 'error', sessionId, message: describeError(props.error) }] : [];
            case 'question.asked':
                return sessionId
                    ? [{ kind: 'question', sessionId, id: props.id, questions: normalizeQuestions(props.questions) }]
                    : [];
            case 'permission.asked':
                return sessionId
                    ? [{ kind: 'permission', sessionId, id: props.id, action: props.permission || '' }]
                    : [];
            case 'session.status':
                return sessionId ? [{ kind: 'status', sessionId, status: props.status?.type || '' }] : [];
            default:
                return [];
        }
    }

    /**
     * v2 事件（data 结构）
     * @param {string} type
     * @param {Object} data
     */
    #normalizeV2(type, data) {
        const sessionId = data?.sessionID;
        switch (type) {
            case 'session.text.delta':
                return sessionId && data.delta ? [{ kind: 'text', sessionId, delta: data.delta }] : [];
            case 'session.reasoning.delta':
                return sessionId && data.delta ? [{ kind: 'reasoning', sessionId, delta: data.delta }] : [];
            case 'session.tool.called':
                return sessionId
                    ? [{
                        kind: 'tool',
                        sessionId,
                        tool: data.tool || data.name || 'tool',
                        status: 'running',
                        title: data.tool || data.name || '工具调用',
                    }]
                    : [];
            case 'session.tool.success':
            case 'session.tool.failed':
                return sessionId
                    ? [{
                        kind: 'tool',
                        sessionId,
                        tool: data.tool || 'tool',
                        status: type === 'session.tool.success' ? 'completed' : 'error',
                        title: data.tool || '工具调用',
                    }]
                    : [];
            case 'session.idle':
            case 'session.execution.succeeded':
            case 'session.execution.interrupted':
                return sessionId ? [{ kind: 'idle', sessionId }] : [];
            case 'session.execution.failed':
                return sessionId ? [{ kind: 'error', sessionId, message: describeError(data.error) }] : [];
            case 'session.retry.scheduled':
                return sessionId ? [{ kind: 'status', sessionId, status: 'retry' }] : [];
            case 'form.created': {
                const form = data.form;
                if (!form?.id || !form?.sessionID) return [];
                return [{
                    kind: 'question',
                    sessionId: form.sessionID,
                    id: form.id,
                    questions: normalizeQuestions(form.fields),
                }];
            }
            case 'form.cancelled':
                return sessionId ? [{ kind: 'questionClosed', sessionId, id: data.id }] : [];
            case 'permission.asked':
                return sessionId ? [{ kind: 'permission', sessionId, id: data.id, action: data.action || '' }] : [];
            default:
                return [];
        }
    }

    /**
     * 记录 part 类型，限制容量避免长跑内存膨胀
     * @param {string} partId
     * @param {string} type
     */
    #rememberPartType(partId, type) {
        if (this.#partTypes.size > PART_TYPE_CACHE_LIMIT) {
            const keys = [...this.#partTypes.keys()].slice(0, PART_TYPE_CACHE_LIMIT / 2);
            keys.forEach((key) => this.#partTypes.delete(key));
        }
        this.#partTypes.set(partId, type);
    }
}

/**
 * 把 v1 的 questions 或 v2 的 fields 统一成前端可渲染结构
 * @param {Array<Object>} fields
 */
function normalizeQuestions(fields) {
    return (fields || [])
        .filter((field) => !field?.hidden)
        .map((field) => ({
            question: field.title || field.description || field.key || field.question || '',
            header: field.title || '请选择',
            multiple: field.type === 'multiselect' || field.multiple === true,
            options: (field.options || []).map((option) => ({
                label: option.label,
                value: option.value ?? option.label,
            })),
        }));
}

/**
 * 提取结构化错误里的可读信息
 * @param {any} error
 */
function describeError(error) {
    if (!error) return '未知错误';
    if (typeof error === 'string') return error;
    return error?.data?.message || error?.message || JSON.stringify(error).slice(0, 200);
}