/**
 * OpenCode Agent ����ʵ��
 * ��װ @opencode-ai/sdk �ĻỰ����Ϣ����
 */

import { BotConfig } from '../config/bot-config.js';
import { LogPrefix } from '../constants.js';

/**
 * ��������û��� system Լ��ָ�����������ע�� prompt��
 */
const FEISHU_SYSTEM_RULES = [
    '��Ļظ�������������û������ն˿����߽��棩�����ϸ����أ�',
    '1. ��ֹ�ڻظ�������������ļ�·����Ŀ¼�ṹ������ IP�����������˿ڵȻ�����ʩ��Ϣ��',
    '2. ��ֹ���������������Կ��token�����Ӵ����κ�ƾ֤���ݣ���ʹ��Ƭ�Σ�',
    '3. ��ֹ���ϵͳ����ԭ�ļ���ԭʼִ�н�������������ۣ���չʾԭ�ģ���',
    '4. ֻ�������û�������ص�ҵ����������ۡ�',
].join('\n');

/**
 * OpenCode Agent ��
 */
export class OpencodeAgent {
    /**
     * @param {Object} client - OpenCode SDK �ͻ���
     * @param {{provider:string, model:string}} model - ģ�Ͷ���
     * @param {string} [baseUrl] - ���� OpenCode ʵ����ַ��question ��ԭ�� HTTP �ӿ��ã�ȱʡȫ�����ã�
     */
    constructor(client, model, baseUrl) {
        if (!client) throw new Error('OpencodeAgent ��ʼ��ʧ�ܣ�client Ϊ��');
        if (!model?.provider || !model?.model) throw new Error('OpencodeAgent ��ʼ��ʧ�ܣ�ģ�Ͷ��岻����');
        this.client = client;
        this.model = { providerID: model.provider, modelID: model.model };
        this.baseUrl = baseUrl || BotConfig.getOpencodeBaseUrl();
        this.callbacks = {};
    }

    setCallbacks(callbacks) {
        this.callbacks = callbacks || {};
    }

    #trigger(name, ...args) {
        try {
            this.callbacks[name]?.(...args);
        } catch (error) {
            console.error(`${LogPrefix.AGENT_MGR} �ص�ִ��ʧ�� [${name}]: ${error.message}`);
        }
    }

    /** @returns {string} agent չʾ�� */
    getName() {
        return `${this.model.providerID}/${this.model.modelID}`;
    }

    /**
     * �����»Ự
     * @param {string} title
     * @returns {Promise<string>} �Ự ID
     */
    async createSession(title) {
        const session = await this.client.session.create({ body: { title } });
        const sessionId = session?.id || session?.data?.id;
        if (!sessionId) {
            throw new Error(`�����Ự�ɹ���δ���� ID: ${JSON.stringify(session)}`);
        }
        this.#trigger('onSessionCreated', sessionId, title);
        return sessionId;
    }

    /**
     * ������Ϣ������ʽ prompt��
     * @param {string} sessionId
     * @param {string} message
     * @param {string} [systemPrompt] - �Զ��� system ָ�API ְ�ܳ���ע��ְ����ʾ�ʣ�ȱʡ����������ע�����Լ����
     */
    async sendMessage(sessionId, message, systemPrompt) {
        if (!sessionId || !message) throw new Error('������Ϣʧ�ܣ�sessionId/message Ϊ��');
        this.#trigger('onMessageReceived', sessionId, message);
        try {
            const body = {
                model: this.model,
                parts: [{ type: 'text', text: message }],
            };
            // system ָ����÷���ʽָ�����ȣ�ְ����ʾ�ʣ���������������ʱע�������ΪԼ����Դͷ����������Ϣ������B ����ߣ�
            const system = systemPrompt || (BotConfig.isMaskSensitiveEnabled() ? FEISHU_SYSTEM_RULES : '');
            if (system) {
                body.system = system;
            }
            const result = await this.client.session.prompt({
                path: { id: sessionId },
                body,
            });
            this.#trigger('onMessageSent', sessionId, message, result);
            return result;
        } catch (error) {
            // undici 的 fetch failed 会把真实原因藏在 cause（HeadersTimeoutError/连接错误等）
            const cause = error?.cause?.message || error?.cause?.code || error?.cause;
            console.error(`${LogPrefix.AGENT_MGR} prompt 调用失败: session=${sessionId}, error=${error.message}${cause ? ` | cause: ${cause}` : ''}`);
            this.#trigger('onError', sessionId, error);
            throw error;
        }
    }

    /** �жϻỰ */
    async abort(sessionId) {
        try {
            await this.client.session.abort({ path: { id: sessionId } });
        } catch (error) {
            this.#trigger('onError', sessionId, error);
            throw error;
        }
    }

    /** �г����лỰ */
    async listSessions() {
        const res = await this.client.session.list();
        return res?.data || res || [];
    }

    /** ��ȡ�Ự��Ϣ�б� */
    async getSessionMessages(sessionId) {
        const res = await this.client.session.messages({ path: { id: sessionId } });
        return res?.data || res || [];
    }

    /**
     * �ش𹤾����ʣ�question.reply �ջ���
     * ע�⣺SDK 1.18.x δ���� question �ӿڣ��˴�ֱ�ӵ��÷���� HTTP API
     * @param {string} requestId - question ���� ID��que_xxx��
     * @param {string[][]} answers - ���б���ÿ�������Ӧһ��ѡ�� label ����
     * @param {string} [sessionId] - �����Ự ID������ 404 ʱ���Ự�ض�λ��ʵ requestId
     * @returns {Promise<boolean>} �Ƿ�ɹ�
     */
    async replyQuestion(requestId, answers, sessionId) {
        try {
            console.log(`${LogPrefix.AGENT_MGR} question.reply ����: requestId=${requestId}, sessionId=${sessionId || '��'}, answers=${JSON.stringify(answers)}`);
            let res = await this.#postQuestionReply(requestId, answers);

            // 404 ��������ť/�����е� requestId �����˴������ⲻƥ�䣨���ڡ���ʵ����λ�ȣ�
            // ���Ự ID ���¶�λ��ǰ����� requestId ������һ��
            if (res.status === 404 && sessionId) {
                const realId = await this.#findPendingQuestionId(sessionId);
                if (realId && realId !== requestId) {
                    console.warn(`${LogPrefix.AGENT_MGR} question.reply 404��requestId ��ƥ�䣬�ض�λ: ${requestId} -> ${realId}`);
                    res = await this.#postQuestionReply(realId, answers);
                } else {
                    // ��ӡ����˵�ǰ�����б���Э����λ ID ��λԭ��
                    await this.#logPendingQuestions();
                }
            }

            if (!res.ok) {
                console.error(`${LogPrefix.AGENT_MGR} question.reply HTTP ${res.status}`);
                return false;
            }
            return true;
        } catch (error) {
            console.error(`${LogPrefix.AGENT_MGR} question.reply ʧ��: ${error.message}`);
            return false;
        }
    }

    /**
     * ���� question.reply HTTP �ӿ�
     */
    async #postQuestionReply(requestId, answers) {
        const url = `${this.baseUrl}/question/${encodeURIComponent(requestId)}/reply`;
        return await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answers }),
        });
    }

    /**
     * ���Ự ID ��ѯ��ǰ�������ʵ���ʵ requestId
     * @returns {Promise<string|null>}
     */
    async #findPendingQuestionId(sessionId) {
        try {
            const res = await fetch(`${this.baseUrl}/question`);
            if (!res.ok) return null;
            const list = await res.json();
            const hit = (Array.isArray(list) ? list : []).find((q) => q?.sessionID === sessionId);
            return hit?.id || null;
        } catch (error) {
            console.error(`${LogPrefix.AGENT_MGR} ��ѯ��������ʧ��: ${error.message}`);
            return null;
        }
    }

    /**
     * ��ӡ����˵�ǰ���������б������ requestId ��λ��
     */
    async #logPendingQuestions() {
        try {
            const res = await fetch(`${this.baseUrl}/question`);
            if (!res.ok) return;
            const list = await res.json();
            const brief = (Array.isArray(list) ? list : []).map((q) => ({
                id: q.id,
                sessionID: q.sessionID,
            }));
            console.warn(`${LogPrefix.AGENT_MGR} ����˵�ǰ��������: ${JSON.stringify(brief) || '[]'}`);
        } catch (error) {
            console.error(`${LogPrefix.AGENT_MGR} ��ѯ���������б�ʧ��: ${error.message}`);
        }
    }

    /**
     * �ܾ��������ʣ�question.reject �ջ���
     * ���ڽ�����ʱ���ף��ܾ��� OpenCode �Ự�������ù���
     * @param {string} requestId - question ���� ID��que_xxx��
     * @returns {Promise<boolean>} �Ƿ�ɹ�
     */
    async rejectQuestion(requestId) {
        try {
            const url = `${this.baseUrl}/question/${encodeURIComponent(requestId)}/reject`;
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
            if (!res.ok) {
                console.error(`${LogPrefix.AGENT_MGR} question.reject HTTP ${res.status}`);
                return false;
            }
            return true;
        } catch (error) {
            console.error(`${LogPrefix.AGENT_MGR} question.reject ʧ��: ${error.message}`);
            return false;
        }
    }

    /**
     * ��ӦȨ������
     * @param {string} sessionId
     * @param {string} permissionId
     * @param {'once'|'always'|'reject'} response
     */
    async respondPermission(sessionId, permissionId, response) {
        try {
            const body = { response };
            const path = { id: sessionId, permissionID: permissionId };
            // ����ʹ���°� SDK �� session.permissions.respond���������ɰ涥�㷽��
            const respond = this.client.session?.permissions?.respond;
            if (typeof respond === 'function') {
                await respond.call(this.client.session.permissions, { path, body });
            } else if (typeof this.client.postSessionIdPermissionsPermissionId === 'function') {
                await this.client.postSessionIdPermissionsPermissionId({ path, body });
            } else {
                throw new Error('SDK ��֧��Ȩ����Ӧ�ӿ�');
            }
            return true;
        } catch (error) {
            console.error(`${LogPrefix.AGENT_MGR} Ȩ����Ӧʧ��: ${error.message}`);
            return false;
        }
    }
}
