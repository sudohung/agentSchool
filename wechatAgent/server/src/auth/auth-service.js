/**
 * 微信登录：code2session + dev 兜底
 *
 * 正式模式：小程序 wx.login 拿 code -> 服务端调 code2session 换 openid
 * dev 模式：未配置 AppID/AppSecret 时，用前端上报的 deviceId 派生稳定 openid，先把功能跑通
 */

import { createHash } from 'crypto';
import { AuthMode, ErrorCode } from '../constants.js';
import { httpError } from '../http/respond.js';

const CODE2SESSION_URL = 'https://api.weixin.qq.com/sns/jscode2session';

/**
 * 调微信 code2session
 * @param {{appId:string, appSecret:string, code:string}} input
 * @returns {Promise<{openid:string, unionid?:string}>}
 */
async function code2Session({ appId, appSecret, code }) {
    const url = new URL(CODE2SESSION_URL);
    url.searchParams.set('appid', appId);
    url.searchParams.set('secret', appSecret);
    url.searchParams.set('js_code', code);
    url.searchParams.set('grant_type', 'authorization_code');

    let payload;
    try {
        const res = await fetch(url, { signal: AbortSignal.timeout(10000) });
        payload = await res.json();
    } catch (error) {
        throw httpError(502, ErrorCode.ENGINE_ERROR, `微信登录接口不可用: ${error.message}`);
    }

    if (payload?.errcode) {
        throw httpError(401, ErrorCode.UNAUTHORIZED, `微信登录失败: ${payload.errmsg || payload.errcode}`, payload);
    }
    if (!payload?.openid) {
        throw httpError(401, ErrorCode.UNAUTHORIZED, '微信登录未返回 openid', payload);
    }
    return { openid: payload.openid, unionid: payload.unionid };
}

/**
 * 由设备标识派生稳定 openid（dev 模式）
 * @param {string} deviceId
 */
function deriveDevOpenid(deviceId) {
    const hash = createHash('sha256').update(String(deviceId)).digest('hex').slice(0, 24);
    return `dev_${hash}`;
}

/**
 * 登录服务
 */
export class AuthService {
    /** @type {import('../config.js').loadConfig extends Function ? any : any} */
    #config;
    /** @type {import('./token.js').TokenService} */
    #tokens;
    /** @type {import('../store/chat-store.js').ChatStore} */
    #store;

    constructor({ config, tokens, store }) {
        this.#config = config;
        this.#tokens = tokens;
        this.#store = store;
    }

    /** 当前登录模式 */
    get mode() {
        return this.#config.wechat.appId && this.#config.wechat.appSecret
            ? AuthMode.WECHAT
            : AuthMode.DEV;
    }

    /** 是否允许用 deviceId 走开发登录（有 AppID 时默认关闭） */
    get allowDevLogin() {
        return this.#config.wechat.allowDevLogin === true || this.mode === AuthMode.DEV;
    }

    /**
     * 登录：换取用户并签发 token
     * @param {{code?:string, deviceId?:string, nickname?:string, avatar?:string}} input
     */
    async login(input) {
        const mode = this.mode;
        let openid;
        let resolvedMode = mode;

        if (mode === AuthMode.WECHAT && input.code) {
            // 开发者工具游客模式下的 code 是伪造的，code2session 会返回 invalid code；
            // 开着 allowDevLogin 时降级为开发登录，避免“配置了真实 AppID 反而进不去模拟器”
            try {
                ({ openid } = await code2Session({
                    appId: this.#config.wechat.appId,
                    appSecret: this.#config.wechat.appSecret,
                    code: input.code,
                }));
            } catch (error) {
                if (!this.allowDevLogin) throw error;
                openid = deriveDevOpenid(input.deviceId || input.code);
                resolvedMode = AuthMode.DEV;
            }
        } else if (this.allowDevLogin && (input.deviceId || input.code)) {
            // 开发登录：没有 code（开发者工具未登录/未配置）时用设备标识派生稳定用户
            openid = deriveDevOpenid(input.deviceId || input.code);
            resolvedMode = AuthMode.DEV;
        } else if (mode === AuthMode.WECHAT) {
            throw httpError(400, ErrorCode.BAD_REQUEST, '缺少 wx.login 的 code');
        } else {
            throw httpError(400, ErrorCode.BAD_REQUEST, '缺少 deviceId（dev 登录标识）');
        }

        const user = this.#store.upsertUser(openid, {
            mode: resolvedMode,
            nickname: input.nickname,
            avatar: input.avatar,
        });

        return {
            mode: resolvedMode,
            token: this.#tokens.issue({ userId: user.id, openid }),
            user: {
                id: user.id,
                nickname: user.nickname,
                avatar: user.avatar,
            },
        };
    }

    /**
     * 从请求头解析登录态
     * @param {import('http').IncomingMessage} req
     * @returns {{userId:string, openid:string}|null}
     */
    authenticate(req) {
        const header = req.headers['authorization'] || '';
        const token = header.startsWith('Bearer ') ? header.slice(7) : '';
        return token ? this.#tokens.verify(token) : null;
    }
}