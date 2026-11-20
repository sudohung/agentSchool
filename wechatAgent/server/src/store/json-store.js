/**
 * 轻量 JSON 文件存储
 * 单进程使用；写入采用「临时文件 + rename」保证原子性，避免断电/崩溃产生半截文件
 */

import { readFileSync, writeFileSync, renameSync, existsSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { LogPrefix } from '../constants.js';

/**
 * 一个 JSON 文件承载一份数据
 */
export class JsonStore {
    /** @type {string} */
    #filePath;
    /** @type {any} */
    #data;
    /** @type {boolean} */
    #dirty = false;

    /**
     * @param {string} filePath
     * @param {any} initial 文件不存在时的初始值
     */
    constructor(filePath, initial) {
        this.#filePath = filePath;
        mkdirSync(dirname(filePath), { recursive: true });
        if (existsSync(filePath)) {
            try {
                this.#data = JSON.parse(readFileSync(filePath, 'utf-8'));
            } catch (error) {
                // 损坏时保留现场，避免数据被静默覆盖
                const broken = `${filePath}.broken-${Date.now()}`;
                renameSync(filePath, broken);
                console.error(`${LogPrefix.STORE} 数据文件损坏，已备份到 ${broken}: ${error.message}`);
                this.#data = structuredClone(initial);
            }
        } else {
            this.#data = structuredClone(initial);
        }
    }

    /** 读取数据（返回引用，调用方修改后需 save） */
    get() {
        return this.#data;
    }

    /** 覆盖数据 */
    set(data) {
        this.#data = data;
        this.#dirty = true;
    }

    /** 持久化到磁盘 */
    save() {
        const tmp = `${this.#filePath}.tmp`;
        writeFileSync(tmp, JSON.stringify(this.#data, null, 2), 'utf-8');
        renameSync(tmp, this.#filePath);
        this.#dirty = false;
    }

    /** 是否有未落盘修改 */
    get dirty() {
        return this.#dirty;
    }

    /** 数据文件路径 */
    get path() {
        return this.#filePath;
    }
}

/**
 * 把数据目录下的文件名转为绝对路径
 * @param {string} dataDir
 * @param {string} name
 */
export function dataFile(dataDir, name) {
    return join(dataDir, name);
}