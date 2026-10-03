/**
 * API 任务队列
 * 职责：
 *  1. chat 请求的任务化：同步（等待终态）/ 异步（taskId + get_result 轮询）双模式
 *  2. 全局并发上限 + 排队超时（保护 OpenCode 资源不被打垮）
 *  3. 反问闭环：question.asked -> 任务转 waiting_input，同一凭证的下一条消息自动作为答案回传
 *  4. 权限请求自动拒绝（API 通道无人值守，不允许执行需授权的写操作）
 */

import { randomUUID } from 'crypto';
import { ApiTaskStatus, LogPrefix } from '../constants.js';
import { extractTextResponse } from '../handlers/commands.js';

/** 已终结任务的保留时长（毫秒），超过后清理，避免 Map 无限膨胀 */
const TERMINAL_TASK_TTL = 60 * 60 * 1000;
/** 终结任务清理扫描间隔（毫秒） */
const TASK_SWEEP_INTERVAL = 10 * 60 * 1000;
/**
 * 待答提问等待超时（毫秒）
 * waiting_input 超过该时长无回应则自动拒绝提问并转 failed：
 * 避免调用方不回应时任务永久卡死（占用并发名额 + 会话绑定悬挂）
 */
const QUESTION_WAIT_TTL = 10 * 60 * 1000;
/**
 * 同步等待默认上限（毫秒）
 * 注意：MCP 客户端（如 opencode）工具调用默认 30s 超时（超时报 -32001），
 * 同步上限必须明显低于客户端超时，否则长任务会被客户端侧掐断
 */
const DEFAULT_SYNC_WAIT_CAP = 20000;
/**
 * get_result 长轮询等待窗口（毫秒）
 * 未到终态时在服务内等待至多该时长再返回，减少调用端空轮询次数；
 * 必须低于 MCP 客户端工具默认 30s 超时（-32001），留出网络与序列化余量
 */
const DEFAULT_LONG_POLL_WINDOW = 25000;

/**
 * 任务队列类
 */
export class TaskQueue {
    /** @type {import('./api-session-manager.js').ApiSessionManager} */
    #sessions;
    /** @type {import('../agent/instance-pool.js').InstancePool} */
    #pool;
    /** @type {import('../agent/role-registry.js').RoleRegistry} */
    #roleRegistry;
    /** @type {Map<string, Object>} taskId -> 任务 */
    #tasks = new Map();
    /** @type {Array<Object>} 排队中的任务 */
    #queue = [];
    /** @type {number} 当前执行中的任务数 */
    #runningCount = 0;
    /** @type {NodeJS.Timeout|null} 清理定时器 */
    #sweeper = null;

    /**
     * @param {import('./api-session-manager.js').ApiSessionManager} sessions
     * @param {import('../agent/instance-pool.js').InstancePool} pool
     * @param {import('../agent/role-registry.js').RoleRegistry} roleRegistry
     */
    constructor(sessions, pool, roleRegistry) {
        if (!sessions || !pool || !roleRegistry) {
            throw new Error('TaskQueue 初始化失败：缺少依赖');
        }
        this.#sessions = sessions;
        this.#pool = pool;
        this.#roleRegistry = roleRegistry;
    }

    /** 启动终结任务清理 */
    startSweeper() {
        if (this.#sweeper) return;
        this.#sweeper = setInterval(() => {
            this.#sweepTerminalTasks().catch((error) => {
                console.error(`${LogPrefix.TASK} 任务清理扫描异常: ${error.message}`);
            });
        }, TASK_SWEEP_INTERVAL);
        this.#sweeper.unref?.();
    }

    // ==================== 对外入口 ====================

    /**
     * 提交 chat 请求
     * @param {string} callerSessionId
     * @param {string} message
     * @param {{wait?:boolean, timeoutMs?:number}} [options]
     * @returns {Promise<Object>} 异步：{status:'pending', taskId}；同步：终态快照
     */
    async submitChat(callerSessionId, message, options = {}) {
        const { agent, binding, role } = this.#sessions.getAgent(callerSessionId);

        // 场景1：存在待答提问 -> 本条消息作为答案回传（不新建任务、不占用并发）
        if (binding.pendingQuestion) {
            return this.#answerPendingQuestion(callerSessionId, binding, agent, message);
        }

        // 场景2：常规提问 -> 创建任务
        const task = this.#createTask(callerSessionId, binding, role, message);
        this.#enqueue(task);

        if (!options.wait) {
            return this.#snapshot(task);
        }

        // 同步模式：等待终态（waiting_input 也是终态，调用方需回应）
        // 超时未完成时返回 running/pending 快照（含 taskId），调用方转 get_result 轮询
        const timeoutMs = Math.min(
            options.timeoutMs || this.#roleRegistry.getSessionConfig().syncWaitCapMs || DEFAULT_SYNC_WAIT_CAP,
            DEFAULT_SYNC_WAIT_CAP,
        );
        const snapshot = await Promise.race([
            task.terminalPromise.then(() => this.#snapshot(task)),
            new Promise((resolve) => setTimeout(() => resolve(this.#snapshot(task)), timeoutMs)),
        ]);
        return snapshot;
    }

    /**
     * 查询任务结果（长轮询模式）
     * 任务未到终态（pending/running）时在服务内等待至多 longPollWindowMs：
     * 等到终态立即返回；超时仍无终态则返回当前快照，调用方接着发起下一次 get_result
     * @param {string} taskId
     * @param {{longPollMs?:number}} [options]
     * @returns {Promise<Object>} 任务快照
     */
    async getResult(taskId, options = {}) {
        const task = this.#tasks.get(taskId);
        if (!task) {
            throw new Error(`任务不存在或已过期: ${taskId}`);
        }
        return this.#longPollSnapshot(task, options.longPollMs);
    }

    /**
     * 按会话凭证查询最新任务结果（长轮询模式）
     * 用途：客户端同步等待超时（如 MCP 客户端 30s 上限报 -32001）后 taskId 丢失，可凭凭证找回任务状态
     * @param {string} callerSessionId
     * @param {{longPollMs?:number}} [options]
     * @returns {Promise<Object>} 最新任务快照；该凭证尚无任务时立即返回占位
     */
    async getResultByCredential(callerSessionId, options = {}) {
        this.#sessions.requireBinding(callerSessionId);
        let latest = null;
        for (const task of this.#tasks.values()) {
            if (task.callerSessionId !== callerSessionId) continue;
            if (!latest || task.createdAt > latest.createdAt) latest = task;
        }
        if (!latest) {
            return { status: 'no_task', hint: '该会话暂无任务记录，请用 chat 提交新消息' };
        }
        return this.#longPollSnapshot(latest, options.longPollMs);
    }

    /**
     * 长轮询核心：未终态时在服务内等待至多窗口时长，终态立即返回
     */
    async #longPollSnapshot(task, longPollMs) {
        const terminal = [ApiTaskStatus.DONE, ApiTaskStatus.FAILED, ApiTaskStatus.WAITING_INPUT];
        if (terminal.includes(task.status)) {
            return this.#snapshot(task);
        }
        const windowMs = Math.max(0, Math.min(
            longPollMs || this.#roleRegistry.getSessionConfig().longPollWindowMs || DEFAULT_LONG_POLL_WINDOW,
            DEFAULT_LONG_POLL_WINDOW,
        ));
        // 等待终态（terminalPromise 在 done/failed/waiting_input 时 resolve）或窗口超时
        await Promise.race([
            task.terminalPromise,
            new Promise((resolve) => setTimeout(resolve, windowMs)),
        ]);
        return this.#snapshot(task);
    }

    // ==================== 事件回调（opencode-listener 路由） ====================

    /**
     * question.asked 事件：任务转 waiting_input，登记待答提问
     * @param {{id:string, sessionID:string, questions:Array}} properties
     */
    onQuestionAsked(properties) {
        const binding = this.#sessions.findByInternalSessionId(properties?.sessionID);
        if (!binding) return;
        const task = this.#findActiveTaskByBinding(binding);
        if (!task) {
            console.warn(`${LogPrefix.TASK} question.asked 未找到活跃任务，忽略: session=${properties.sessionID}`);
            return;
        }
        binding.pendingQuestion = {
            requestId: properties.id,
            questions: properties.questions || [],
            taskId: task.taskId,
        };
        task.status = ApiTaskStatus.WAITING_INPUT;
        task.question = properties.questions || [];
        task.updatedAt = Date.now();
        // waiting_input 对同步调用方即终态（需回应后才能继续）
        task.resolveTerminal();
        console.log(`${LogPrefix.TASK} 任务转等待输入: taskId=${task.taskId}, 问题数=${(properties.questions || []).length}`);
    }

    /**
     * permission.asked 事件：API 通道无人值守，自动拒绝权限请求
     * @param {{id:string, sessionID:string, permission:string}} properties
     */
    async onPermissionAsked(properties) {
        const binding = this.#sessions.findByInternalSessionId(properties?.sessionID);
        if (!binding) return;
        const { agent } = this.#sessions.getAgentByBinding(binding);
        const ok = await agent.respondPermission(properties.sessionID, properties.id, 'reject');
        console.log(`${LogPrefix.TASK} 权限请求自动拒绝: session=${properties.sessionID}, permission=${properties.permission}, 结果=${ok}`);
    }

    // ==================== 任务执行 ====================

    /**
     * 创建任务对象（含终态通知 promise）
     */
    #createTask(callerSessionId, binding, role, message) {
        const taskId = `task_${randomUUID().slice(0, 12)}`;
        let resolveTerminal;
        const terminalPromise = new Promise((resolve) => { resolveTerminal = resolve; });
        const task = {
            taskId,
            callerSessionId,
            internalSessionId: binding.sessionId,
            roleKey: role.key,
            message,
            status: ApiTaskStatus.PENDING,
            reply: '',
            question: null,
            error: '',
            createdAt: Date.now(),
            updatedAt: Date.now(),
            terminalPromise,
            resolveTerminal,
        };
        this.#tasks.set(taskId, task);
        return task;
    }

    /**
     * 任务入队并触发调度
     */
    #enqueue(task) {
        this.#queue.push(task);
        this.#pump();
    }

    /**
     * 调度：并发有空位时从队列取任务执行
     */
    #pump() {
        const maxConcurrent = this.#roleRegistry.getSessionConfig().maxConcurrent;
        const queueTimeoutMs = this.#roleRegistry.getSessionConfig().queueTimeoutMinutes * 60 * 1000;

        while (this.#runningCount < maxConcurrent && this.#queue.length > 0) {
            const task = this.#queue.shift();

            // 排队超时：直接失败，避免故障洪峰拖垮资源
            if (Date.now() - task.createdAt > queueTimeoutMs) {
                this.#finishTask(task, ApiTaskStatus.FAILED, '', '排队超时，请稍后重试');
                continue;
            }

            this.#runningCount++;
            task.status = ApiTaskStatus.RUNNING;
            task.updatedAt = Date.now();
            // 不 await：调度循环立即继续，任务完成由内部处理
            this.#runTask(task).finally(() => {
                this.#runningCount--;
                this.#pump();
            });
        }
    }

    /**
     * 执行任务：串行锁保护下发送 prompt，完成后提取文本回复
     */
    async #runTask(task) {
        try {
            const { agent, role } = this.#sessions.getAgent(task.callerSessionId);
            const result = await this.#sessions.withSessionLock(task.internalSessionId, () =>
                agent.sendMessage(task.internalSessionId, task.message, role.prompt || undefined),
            );
            const reply = extractTextResponse(result) || '（无文本回复）';
            this.#finishTask(task, ApiTaskStatus.DONE, reply);
        } catch (error) {
            console.error(`${LogPrefix.TASK} 任务执行失败: taskId=${task.taskId}, error=${error.message}`);
            this.#finishTask(task, ApiTaskStatus.FAILED, '', error.message);
        }
    }

    /**
     * 回答待答提问：question.reply 回传后原任务恢复执行
     */
    async #answerPendingQuestion(callerSessionId, binding, agent, message) {
        const pending = binding.pendingQuestion;
        const task = this.#tasks.get(pending.taskId);
        binding.pendingQuestion = null;

        // 按问题数量构建答案：回答恰好是某问题的选项 label 时按选项作答，否则用原文
        const answers = (pending.questions || []).map((q) => {
            const labels = (q.options || []).map((o) => o.label);
            return labels.includes(message.trim()) ? [message.trim()] : [message];
        });
        const ok = await agent.replyQuestion(pending.requestId, answers, binding.sessionId);
        if (!ok) {
            // 回答失败：保留待答状态，调用方可重试
            binding.pendingQuestion = pending;
            throw new Error('回答提交失败，请重试');
        }
        if (task && task.status === ApiTaskStatus.WAITING_INPUT) {
            task.status = ApiTaskStatus.RUNNING;
            task.question = null;
            task.updatedAt = Date.now();
        }
        console.log(`${LogPrefix.TASK} 已回传答案: credential=${callerSessionId}, 原任务=${pending.taskId}`);
        return { status: 'answered', taskId: pending.taskId };
    }

    // ==================== 任务状态维护 ====================

    /**
     * 任务进入终态并通知等待方
     */
    #finishTask(task, status, reply, error = '') {
        task.status = status;
        task.reply = reply;
        task.error = error;
        task.updatedAt = Date.now();
        task.resolveTerminal();
    }

    /**
     * 查找绑定上的活跃任务（running/waiting_input）
     */
    #findActiveTaskByBinding(binding) {
        for (const task of this.#tasks.values()) {
            if (task.internalSessionId !== binding.sessionId) continue;
            if (task.status === ApiTaskStatus.RUNNING || task.status === ApiTaskStatus.WAITING_INPUT) {
                return task;
            }
        }
        return null;
    }

    /**
     * 任务快照（对外暴露字段）
     */
    #snapshot(task) {
        const snap = {
            taskId: task.taskId,
            status: task.status,
            role: task.roleKey,
        };
        if (task.status === ApiTaskStatus.DONE) snap.reply = task.reply;
        if (task.status === ApiTaskStatus.WAITING_INPUT) {
            snap.question = task.question;
            snap.questionText = this.#formatQuestionText(task.question);
            snap.hint = '下游 agent 需要用户决策：①将 questionText 原样转达给最终用户并收集答复（用户可直接回答或选择选项）；②用同一 callerSessionId 调用 chat（message=用户答复），任务会自动继续执行；③不要将 waiting_input 当作任务结束，也不要继续轮询。超时 10 分钟未回应任务将自动失败';
        }
        if (task.status === ApiTaskStatus.FAILED) snap.error = task.error;
        if (task.status === ApiTaskStatus.PENDING) snap.hint = '任务排队中，请继续调用 get_result 轮询（建议由子 agent/后台任务执行，避免阻塞主会话）';
        if (task.status === ApiTaskStatus.RUNNING) snap.hint = '任务执行中，请继续调用 get_result 轮询（建议由子 agent/后台任务执行，避免阻塞主会话）';
        return snap;
    }

    /**
     * 格式化提问为可读文本（调用方拿到即可直接转述给最终用户）
     * @param {Array<{question:string, header:string, options?:Array<{label:string}>}>} questions
     * @returns {string}
     */
    #formatQuestionText(questions) {
        return (questions || []).map((q, i) => {
            const options = (q.options || []).map((o) => o.label).join(' / ');
            return `${i + 1}. ${q.question}（${q.header}）\n   选项：${options || '自由回答'}`;
        }).join('\n');
    }

    /**
     * 清理扫描：
     *  1. waiting_input 超时（10 分钟）的提问自动拒绝并转 failed，释放并发名额
     *  2. 已终结超过保留时长的任务移除
     */
    async #sweepTerminalTasks() {
        const now = Date.now();
        for (const [taskId, task] of this.#tasks.entries()) {
            // 场景1：提问等待超时 -> 自动拒绝，防止永久卡死
            if (task.status === ApiTaskStatus.WAITING_INPUT && now - task.updatedAt > QUESTION_WAIT_TTL) {
                await this.#timeoutPendingQuestion(task);
                continue;
            }

            // 场景2：终结任务过期清理
            const terminal = [ApiTaskStatus.DONE, ApiTaskStatus.FAILED].includes(task.status);
            if (!terminal) continue;
            if (now - task.updatedAt > TERMINAL_TASK_TTL) {
                this.#tasks.delete(taskId);
            }
        }
    }

    /**
     * 提问等待超时处理：question.reject 回传下游 + 清理会话绑定的待答状态 + 任务转 failed
     */
    async #timeoutPendingQuestion(task) {
        const binding = this.#sessions.findByInternalSessionId(task.internalSessionId);
        const pending = binding?.pendingQuestion;
        if (binding && pending?.requestId) {
            try {
                const { agent } = this.#sessions.getAgentByBinding(binding);
                const ok = await agent.rejectQuestion(pending.requestId);
                console.log(`${LogPrefix.TASK} 提问等待超时自动拒绝: taskId=${task.taskId}, request=${pending.requestId}, 结果=${ok}`);
            } catch (error) {
                console.warn(`${LogPrefix.TASK} 提问超时拒绝失败（继续任务失败流程）: ${error.message}`);
            }
            binding.pendingQuestion = null;
        }
        this.#finishTask(task, ApiTaskStatus.FAILED, '', '提问等待超时（10 分钟无回应），已自动拒绝；请重新发起任务');
    }
}
