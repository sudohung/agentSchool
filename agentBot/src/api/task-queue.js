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
import { CALLBACK_RETRY_INTERVAL } from './callback-store.js';

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
    /** @type {import('./callback-store.js').CallbackStore|null} 回调记录持久层（未注入时回调模式降级为纯内存） */
    #callbackStore;
    /** @type {import('./callback-client.js').CallbackClient|null} opencode 回调执行器 */
    #callbackClient;
    /** @type {Map<string, Object>} taskId -> 任务 */
    #tasks = new Map();
    /** @type {Array<Object>} 排队中的任务 */
    #queue = [];
    /** @type {number} 当前执行中的任务数 */
    #runningCount = 0;
    /** @type {NodeJS.Timeout|null} 清理定时器 */
    #sweeper = null;
    /** @type {NodeJS.Timeout|null} 回调重投定时器 */
    #callbackSweeper = null;

    /**
     * @param {import('./api-session-manager.js').ApiSessionManager} sessions
     * @param {import('../agent/instance-pool.js').InstancePool} pool
     * @param {import('../agent/role-registry.js').RoleRegistry} roleRegistry
     * @param {{callbackStore?:import('./callback-store.js').CallbackStore, callbackClient?:import('./callback-client.js').CallbackClient}} [deps]
     */
    constructor(sessions, pool, roleRegistry, deps = {}) {
        if (!sessions || !pool || !roleRegistry) {
            throw new Error('TaskQueue 初始化失败：缺少依赖');
        }
        this.#sessions = sessions;
        this.#pool = pool;
        this.#roleRegistry = roleRegistry;
        this.#callbackStore = deps.callbackStore || null;
        this.#callbackClient = deps.callbackClient || null;
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

    /** 启动回调重投扫描（sqlite 中未推送成功的终态记录周期性重投，重启后恢复） */
    startCallbackSweeper() {
        if (this.#callbackSweeper || !this.#callbackStore?.isAvailable()) return;
        this.#callbackSweeper = setInterval(() => {
            this.#redeliverPendingCallbacks().catch((error) => {
                console.error(`${LogPrefix.CALLBACK} 重投扫描异常: ${error.message}`);
            });
        }, CALLBACK_RETRY_INTERVAL);
        this.#callbackSweeper.unref?.();
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

        // 场景2：回调模式 -> 校验目标实例/会话并解析链路深度（失败直接报错，不静默降级）
        let callback = null;
        if (options.callback) {
            callback = await this.#prepareCallback(options.callback);
        }

        // 场景3：常规提问 -> 创建任务
        const task = this.#createTask(callerSessionId, binding, role, message, callback);
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
     * 回调模式任务不等待：结果由服务端主动推送，get_result 仅作即时状态查询/兜底
     */
    async #longPollSnapshot(task, longPollMs) {
        const terminal = [ApiTaskStatus.DONE, ApiTaskStatus.FAILED, ApiTaskStatus.WAITING_INPUT];
        if (terminal.includes(task.status) || task.callback) {
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
        // 回调模式：把提问文本推送到调用方会话（尽力而为），调用方用原凭证 chat 回答即可闭环
        this.#pushQuestionToCallback(task, this.#formatQuestionText(task.question));
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
    #createTask(callerSessionId, binding, role, message, callback = null) {
        const taskId = `task_${randomUUID().slice(0, 12)}`;
        let resolveTerminal;
        const terminalPromise = new Promise((resolve) => { resolveTerminal = resolve; });
        const task = {
            taskId,
            callerSessionId,
            internalSessionId: binding.sessionId,
            roleKey: role.key,
            message,
            callback,
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

    // ==================== 回调模式 ====================

    /**
     * 校验并准备回调目标
     * @param {{baseUrl:string, sessionId:string}} callback
     * @returns {Promise<{baseUrl:string, sessionId:string, depth:number}>}
     */
    async #prepareCallback(callback) {
        if (!this.#callbackClient) {
            throw new Error('回调模式不可用：回调执行器未装配，请去掉 callback 参数改用轮询模式');
        }
        const baseUrl = String(callback?.baseUrl || '').trim();
        const sessionId = String(callback?.sessionId || '').trim();
        await this.#callbackClient.verifyTarget(baseUrl, sessionId);

        const depth = this.#resolveCallbackDepth(sessionId);
        const maxDepth = this.#roleRegistry.getSessionConfig().maxCallbackDepth;
        if (depth > maxDepth) {
            throw new Error(`回调链路深度超限（${depth} > ${maxDepth}），已达多 agent 协作深度上限，请在更上层会话直接处理结果`);
        }
        return { baseUrl, sessionId, depth };
    }

    /**
     * 解析回调链深度（循环防护）：
     * 回调目标命中 agentBot 内部会话 -> 沿父任务递推（父深度 + 1）；
     * 外部会话（反查不到）为顶层调用，深度 1
     */
    #resolveCallbackDepth(callerSessionId) {
        let parentDepth = 0;
        for (const task of this.#tasks.values()) {
            if (task.internalSessionId === callerSessionId) {
                parentDepth = Math.max(parentDepth, task.callback?.depth || 1);
            }
        }
        return parentDepth + 1;
    }

    /**
     * 任务终态后向调用方会话推送结果（fire-and-forget，不阻塞调度）
     * 流程：落库（重启可重投）-> 推送（重试）-> 成功删记录 / 失败保留待扫描重投
     */
    async #dispatchCallback(task) {
        if (!task.callback) return;
        const { baseUrl, sessionId, depth } = task.callback;

        let payload = '';
        if (task.status === ApiTaskStatus.DONE) {
            payload = `[agentBot 回调] 角色「${task.roleKey}」任务 ${task.taskId} 已完成：\n${task.reply}`;
        } else if (task.status === ApiTaskStatus.FAILED) {
            payload = `[agentBot 回调] 角色「${task.roleKey}」任务 ${task.taskId} 已失败：${task.error}`;
        } else {
            return; // waiting_input 的提问推送在 onQuestionAsked 中处理
        }

        this.#callbackStore?.upsert({
            taskId: task.taskId,
            role: task.roleKey,
            callerBaseUrl: baseUrl,
            callerSessionId: sessionId,
            internalSessionId: task.internalSessionId,
            depth,
            payload,
        });
        if (!this.#callbackClient) return;

        const ok = await this.#callbackClient.pushWithRetry(baseUrl, sessionId, payload);
        if (ok) {
            this.#callbackStore?.remove(task.taskId);
            console.log(`${LogPrefix.CALLBACK} 结果已推送: taskId=${task.taskId}, 目标会话=${sessionId}`);
        } else {
            this.#callbackStore?.bumpRetries(task.taskId);
            console.warn(`${LogPrefix.CALLBACK} 结果推送失败（保留记录待重投）: taskId=${task.taskId}, 目标会话=${sessionId}`);
        }
    }

    /**
     * 推送反问文本到回调目标（尽力而为，不落库：
     * 若推送失败，任务会在提问超时后转 failed，终态推送仍会落库兜底）
     */
    #pushQuestionToCallback(task, questionText) {
        if (!task.callback || !this.#callbackClient) return;
        const { baseUrl, sessionId } = task.callback;
        const payload = `[agentBot 回调] 角色「${task.roleKey}」任务 ${task.taskId} 等待补充输入（10 分钟内有效，请用原 callerSessionId 调用 chat 传回答复）：\n${questionText}`;
        this.#callbackClient.pushWithRetry(baseUrl, sessionId, payload)
            .then((ok) => {
                if (ok) console.log(`${LogPrefix.CALLBACK} 反问已推送: taskId=${task.taskId}, 目标会话=${sessionId}`);
                else console.warn(`${LogPrefix.CALLBACK} 反问推送失败（任务超时后仍会推送终态）: taskId=${task.taskId}`);
            })
            .catch(() => { /* 尽力而为 */ });
    }

    /**
     * 重投 sqlite 中未推送成功的终态记录（服务重启后恢复 + 失败重试）
     */
    async #redeliverPendingCallbacks() {
        if (!this.#callbackStore?.isAvailable() || !this.#callbackClient) return;
        const pending = this.#callbackStore.listPending();
        for (const record of pending) {
            const ok = await this.#callbackClient.pushWithRetry(
                record.caller_base_url, record.caller_session_id, record.payload,
            );
            if (ok) {
                this.#callbackStore.remove(record.task_id);
                console.log(`${LogPrefix.CALLBACK} 重投成功: taskId=${record.task_id}, 目标会话=${record.caller_session_id}`);
            } else {
                this.#callbackStore.bumpRetries(record.task_id);
            }
        }
    }

    // ==================== 任务状态维护 ====================

    /**
     * 任务进入终态并通知等待方，随后触发回调推送
     */
    #finishTask(task, status, reply, error = '') {
        task.status = status;
        task.reply = reply;
        task.error = error;
        task.updatedAt = Date.now();
        task.resolveTerminal();
        // 回调推送不 await：异常已在内部消化，不影响任务状态维护
        this.#dispatchCallback(task).catch((e) => {
            console.warn(`${LogPrefix.CALLBACK} 回调推送流程异常: taskId=${task.taskId}, ${e.message}`);
        });
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
            notify: task.callback ? 'callback' : 'poll',
        };
        if (task.status === ApiTaskStatus.DONE) snap.reply = task.reply;
        if (task.status === ApiTaskStatus.WAITING_INPUT) {
            snap.question = task.question;
            snap.questionText = this.#formatQuestionText(task.question);
            snap.hint = '下游 agent 需要用户决策：①将 questionText 原样转达给最终用户并收集答复（用户可直接回答或选择选项）；②用同一 callerSessionId 调用 chat（message=用户答复），任务会自动继续执行；③不要将 waiting_input 当作任务结束，也不要继续轮询。超时 10 分钟未回应任务将自动失败';
        }
        if (task.status === ApiTaskStatus.FAILED) snap.error = task.error;
        if (task.status === ApiTaskStatus.PENDING) {
            snap.hint = task.callback
                ? '任务已受理，完成后结果将主动推送到你的回调会话，无需轮询'
                : '任务排队中，请继续调用 get_result 轮询（建议由子 agent/后台任务执行，避免阻塞主会话）';
        }
        if (task.status === ApiTaskStatus.RUNNING) {
            snap.hint = task.callback
                ? '任务执行中，完成后结果将主动推送到你的回调会话，无需轮询'
                : '任务执行中，请继续调用 get_result 轮询（建议由子 agent/后台任务执行，避免阻塞主会话）';
        }
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
