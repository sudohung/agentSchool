/**
 * 对话页：流式打字机
 *
 * 渲染策略：
 *  - 流式过程中每来一帧都改 data 会触发高频 setData，容易卡顿
 *  - 这里把 delta 先累积到内存，用 60ms 节流批量 setData
 *  - 只 setData 变化的那条消息路径，避免整列表重渲染
 */

const auth = require('../../utils/auth');
const { request } = require('../../utils/request');
const { streamChat, Frame } = require('../../utils/stream');

/** 流式内容刷新节流（毫秒） */
const FLUSH_INTERVAL = 60;

Page({
    data: {
        sessionId: '',
        title: '',
        messages: [],
        input: '',
        sending: false,
        scrollIntoView: '',
        error: '',
        keyboardHeight: 0,
    },

    /** 流式控制句柄 */
    streamTask: null,
    /** 待刷新的流式内容 */
    pending: { content: '', reasoning: '' },
    /** 节流定时器 */
    flushTimer: null,
    /** 当前流式消息在 messages 中的下标 */
    streamIndex: -1,

    onLoad(query) {
        const sessionId = query.id;
        if (!sessionId) {
            wx.showToast({ title: '缺少会话 ID', icon: 'none' });
            return;
        }
        this.setData({ sessionId });
        this.loadHistory();
    },

    onUnload() {
        this.stopStream(true);
        this.clearFlush();
    },

    onHide() {
        // 页面被切走不中断（用户可能只是想看一眼别的页面），仅在卸载时停止
    },

    /**
     * 加载历史消息
     */
    async loadHistory() {
        try {
            await auth.ensureLogin();
            const [sessionRes, messageRes] = await Promise.all([
                request({ path: `/api/sessions/${this.data.sessionId}` }),
                request({ path: `/api/sessions/${this.data.sessionId}/messages` }),
            ]);

            const messages = (messageRes.messages || []).map(toViewMessage);
            this.setData({
                title: sessionRes.session.title,
                messages,
                sending: Boolean(messageRes.busy),
            });
            wx.setNavigationBarTitle({ title: sessionRes.session.title || 'AI 助手' });
            this.scrollToBottom();

            // 若上次异常退出导致有 streaming 状态的消息，提示用户重新提问
            const stuck = messages.some((item) => item.status === 'streaming');
            if (stuck) {
                this.setData({ error: '上一条回答未正常结束，可重新提问' });
            }
        } catch (error) {
            this.setData({ error: error.message || '加载失败' });
        }
    },

    /**
     * 输入
     * @param {Object} e
     */
    onInput(e) {
        this.setData({ input: e.detail.value });
    },

    /**
     * 键盘高度变化（避免输入框被遮挡）
     * @param {Object} e
     */
    onKeyboard(e) {
        this.setData({ keyboardHeight: e.detail.height || 0 });
    },

    /**
     * 发送
     */
    onSend() {
        const text = (this.data.input || '').trim();
        if (!text) return;
        if (this.data.sending) {
            wx.showToast({ title: '正在生成中，请先停止', icon: 'none' });
            return;
        }

        const userMessage = toViewMessage({
            id: `local_${Date.now()}`,
            role: 'user',
            content: text,
            status: 'done',
            createdAt: Date.now(),
        });
        const assistantMessage = toViewMessage({
            id: `pending_${Date.now()}`,
            role: 'assistant',
            content: '',
            reasoning: '',
            status: 'streaming',
            createdAt: Date.now(),
        });

        const messages = [...this.data.messages, userMessage, assistantMessage];
        this.streamIndex = messages.length - 1;
        this.pending = { content: '', reasoning: '' };

        this.setData({
            messages,
            input: '',
            sending: true,
            error: '',
        });
        this.scrollToBottom();

        this.streamTask = streamChat({
            sessionId: this.data.sessionId,
            text,
            onFrame: (frame) => this.handleFrame(frame),
            onError: (error) => this.handleStreamError(error),
            onComplete: (frame) => this.handleStreamDone(frame),
        });
    },

    /**
     * 停止生成
     */
    async onStop() {
        if (!this.data.sending) return;
        this.stopStream(false);
        try {
            await request({ path: `/api/sessions/${this.data.sessionId}/stop`, method: 'POST' });
        } catch (error) {
            // 停止失败不阻塞界面
        }
        this.finalizeAssistant('aborted', '已停止生成');
    },

    /**
     * 处理流式帧
     * @param {Object} frame
     */
    handleFrame(frame) {
        switch (frame.t) {
            case Frame.START:
                // 用服务端消息 ID 替换本地占位 ID，便于与历史对齐
                if (frame.messageId) this.updateStreamField({ id: frame.messageId });
                break;
            case Frame.DELTA:
                this.pending.content += frame.text || '';
                this.scheduleFlush();
                break;
            case Frame.REASONING:
                this.pending.reasoning += frame.text || '';
                this.scheduleFlush();
                break;
            case Frame.TOOL:
                this.updateStreamField({
                    toolText: `${frame.title || frame.tool} · ${translateStatus(frame.status)}`,
                });
                break;
            case Frame.QUESTION:
                this.handleQuestion(frame);
                break;
            case Frame.PERMISSION:
                this.handlePermission(frame);
                break;
            case Frame.ERROR:
                this.handleStreamError(new Error(frame.message || '生成失败'));
                break;
            case Frame.DONE:
                this.handleStreamDone(frame);
                break;
            default:
                break;
        }
    },

    /**
     * 节流刷新流式内容
     */
    scheduleFlush() {
        if (this.flushTimer) return;
        this.flushTimer = setTimeout(() => {
            this.flushTimer = null;
            const { content, reasoning } = this.pending;
            this.updateStreamField({ content, reasoning });
            this.scrollToBottom();
        }, FLUSH_INTERVAL);
    },

    /** 清理节流定时器 */
    clearFlush() {
        if (this.flushTimer) clearTimeout(this.flushTimer);
        this.flushTimer = null;
    },

    /**
     * 更新流式消息的某个字段（只 setData 单条路径）
     * @param {Object} patch
     */
    updateStreamField(patch) {
        if (this.streamIndex < 0) return;
        const data = {};
        Object.keys(patch).forEach((key) => {
            data[`messages[${this.streamIndex}].${key}`] = patch[key];
        });
        this.setData(data);
    },

    /**
     * 表单提问：转成选项按钮
     * @param {Object} frame
     */
    handleQuestion(frame) {
        if (frame.closed) return;
        if (!frame.questions || !frame.questions.length) return;

        const question = frame.questions[0];
        const options = question.options || [];
        if (!options.length) {
            // 纯文本输入型表单，提示用户直接在输入框补充
            this.updateStreamField({ toolText: `需要补充：${question.question}` });
            return;
        }

        wx.showActionSheet({
            itemList: options.map((item) => item.label).slice(0, 6),
            success: async (res) => {
                const picked = options[res.tapIndex];
                try {
                    await request({
                        path: `/api/sessions/${this.data.sessionId}/form`,
                        method: 'POST',
                        data: { formId: frame.id, answers: [picked.value || picked.label] },
                    });
                    this.updateStreamField({ toolText: `已选择：${picked.label}` });
                } catch (error) {
                    wx.showToast({ title: error.message || '提交失败', icon: 'none' });
                }
            },
        });
    },

    /**
     * 权限申请：交给用户决定
     * @param {Object} frame
     */
    handlePermission(frame) {
        wx.showModal({
            title: 'AI 请求执行操作',
            content: frame.action || '是否允许本次操作？',
            confirmText: '允许',
            cancelText: '拒绝',
            success: async (res) => {
                try {
                    await request({
                        path: `/api/sessions/${this.data.sessionId}/permission`,
                        method: 'POST',
                        data: { requestId: frame.id, decision: res.confirm ? 'once' : 'reject' },
                    });
                } catch (error) {
                    wx.showToast({ title: error.message || '提交失败', icon: 'none' });
                }
            },
        });
    },

    /**
     * 流式出错
     * @param {Error} error
     */
    handleStreamError(error) {
        if (!this.data.sending) return;
        this.finalizeAssistant('error', error.message || '网络异常');
        this.setData({ error: error.message || '网络异常' });
    },

    /**
     * 流式结束
     * @param {Object} frame
     */
    handleStreamDone(frame) {
        if (!this.data.sending) return;
        const status = frame.status || 'done';
        if (status === 'done') {
            this.finalizeAssistant('done');
        } else {
            this.finalizeAssistant(status === 'aborted' ? 'aborted' : 'error', frame.error);
        }
    },

    /**
     * 收尾：把累积内容刷进消息并复位状态
     * @param {string} status
     * @param {string} [errorText]
     */
    finalizeAssistant(status, errorText) {
        this.clearFlush();
        this.streamTask = null;
        const patch = {
            content: this.pending.content,
            reasoning: this.pending.reasoning,
            status,
        };
        if (errorText && status !== 'aborted') patch.errorText = errorText;
        this.updateStreamField(patch);
        this.setData({ sending: false });
        this.pending = { content: '', reasoning: '' };
        this.streamIndex = -1;
        this.scrollToBottom();
    },

    /**
     * 主动断开流（不打 stop 接口）
     * @param {boolean} silent
     */
    stopStream(silent) {
        if (this.streamTask) {
            this.streamTask.abort();
            this.streamTask = null;
        }
        this.clearFlush();
        if (!silent && this.data.sending) {
            this.setData({ sending: false });
        }
    },

    /**
     * 滚动到底部
     * scroll-into-view 值不变时不会重新触发滚动，这里在两个底部锚点间交替
     */
    scrollToBottom() {
        if (!this.data.messages.length) return;
        this.anchorFlip = !this.anchorFlip;
        this.setData({ scrollIntoView: this.anchorFlip ? 'anchor-a' : 'anchor-b' });
    },

    /**
     * 复制消息
     * @param {Object} e
     */
    onCopy(e) {
        const content = e.currentTarget.dataset.content;
        if (!content) return;
        wx.setClipboardData({ data: content });
    },
});

/**
 * 转成视图层消息
 * @param {Object} message
 */
function toViewMessage(message) {
    return {
        id: message.id,
        role: message.role,
        content: message.content || '',
        reasoning: message.reasoning || '',
        status: message.status || 'done',
        errorText: '',
        toolText: '',
        timeText: formatClock(message.createdAt),
    };
}

/**
 * HH:mm
 * @param {number} ts
 */
function formatClock(ts) {
    const date = new Date(ts || Date.now());
    const pad = (n) => String(n).padStart(2, '0');
    return `${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/**
 * 工具状态中文
 * @param {string} status
 */
function translateStatus(status) {
    return {
        running: '执行中',
        pending: '等待中',
        completed: '已完成',
        error: '失败',
    }[status] || status;
}