/**
 * 回调任务持久层（sqlite）
 * 职责：
 *  1. 终态（done/failed）待推送记录的持久化：调用方实例/会话、内部会话、结果文本
 *  2. 推送成功即删除；失败保留并累计重试次数
 *  3. 服务重启后扫描未推送记录继续重投（payload 随记录落库，不依赖内存任务）
 * 依赖 Node 22.13+ 内置 node:sqlite（零新增 npm 依赖）
 */

import { DatabaseSync } from 'node:sqlite';
import { mkdirSync } from 'fs';
import { dirname } from 'path';
import { LogPrefix } from '../constants.js';

/** 重投扫描间隔（毫秒） */
export const CALLBACK_RETRY_INTERVAL = 5 * 60 * 1000;

/**
 * 回调任务存储类
 */
export class CallbackStore {
    /** @type {DatabaseSync} */
    #db;

    /**
     * @param {string} dbPath - sqlite 数据库文件路径（如 config/callback-tasks.db）
     */
    constructor(dbPath) {
        try {
            mkdirSync(dirname(dbPath), { recursive: true });
            this.#db = new DatabaseSync(dbPath);
            this.#db.exec('PRAGMA journal_mode = WAL');
            this.#db.exec(`
                CREATE TABLE IF NOT EXISTS callback_tasks (
                    task_id             TEXT PRIMARY KEY,
                    role                TEXT NOT NULL,
                    caller_base_url     TEXT NOT NULL,
                    caller_session_id   TEXT NOT NULL,
                    internal_session_id TEXT NOT NULL,
                    depth               INTEGER NOT NULL DEFAULT 1,
                    payload             TEXT NOT NULL,
                    retries             INTEGER NOT NULL DEFAULT 0,
                    created_at          INTEGER NOT NULL
                )
            `);
            const count = this.#db.prepare('SELECT COUNT(*) AS n FROM callback_tasks').get()?.n || 0;
            console.log(`${LogPrefix.CALLBACK} 存储已初始化: ${dbPath}（待推送记录 ${count} 条）`);
        } catch (error) {
            // sqlite 初始化失败只降级（回调不可持久化），不拖垮主流程
            console.error(`${LogPrefix.CALLBACK} 存储初始化失败，回调推送将不落库: ${error.message}`);
            this.#db = null;
        }
    }

    /** 是否可用（初始化失败时为 false，上层跳过落库逻辑） */
    isAvailable() {
        return !!this.#db;
    }

    /**
     * 写入/覆盖待推送记录（幂等：同一任务重复触发时覆盖）
     * @param {{taskId:string, role:string, callerBaseUrl:string, callerSessionId:string, internalSessionId:string, depth:number, payload:string}} record
     */
    upsert(record) {
        if (!this.#db) return;
        try {
            this.#db.prepare(`
                INSERT INTO callback_tasks
                    (task_id, role, caller_base_url, caller_session_id, internal_session_id, depth, payload, retries, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    payload = excluded.payload, retries = 0
            `).run(
                record.taskId, record.role, record.callerBaseUrl, record.callerSessionId,
                record.internalSessionId, record.depth, record.payload, Date.now(),
            );
        } catch (error) {
            console.error(`${LogPrefix.CALLBACK} 记录写入失败: taskId=${record.taskId}, ${error.message}`);
        }
    }

    /** 推送成功后删除记录 */
    remove(taskId) {
        if (!this.#db) return;
        try {
            this.#db.prepare('DELETE FROM callback_tasks WHERE task_id = ?').run(taskId);
        } catch (error) {
            console.error(`${LogPrefix.CALLBACK} 记录删除失败: taskId=${taskId}, ${error.message}`);
        }
    }

    /** 累计重试次数（推送失败时调用） */
    bumpRetries(taskId) {
        if (!this.#db) return;
        try {
            this.#db.prepare('UPDATE callback_tasks SET retries = retries + 1 WHERE task_id = ?').run(taskId);
        } catch (error) {
            console.error(`${LogPrefix.CALLBACK} 重试计数更新失败: taskId=${taskId}, ${error.message}`);
        }
    }

    /**
     * 列出全部待推送记录（重投扫描用）
     * @returns {Array<Object>}
     */
    listPending() {
        if (!this.#db) return [];
        try {
            return this.#db.prepare('SELECT * FROM callback_tasks ORDER BY created_at ASC').all();
        } catch (error) {
            console.error(`${LogPrefix.CALLBACK} 待推送记录查询失败: ${error.message}`);
            return [];
        }
    }

    /** 关闭数据库连接（进程退出前调用） */
    close() {
        try {
            this.#db?.close();
        } catch { /* 忽略关闭异常 */ }
    }
}
