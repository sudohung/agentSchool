/**
 * 登录令牌：HMAC-SHA256 签名的自包含 token（无需服务端存 session）
 * 格式：base64url(payload).base64url(signature)
 */

import { createHmac, timingSafeEqual, randomBytes } from 'crypto';
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';

/** token 有效期 30 天 */
const TOKEN_TTL_MS = 30 * 24 * 60 * 60 * 1000;

/**
 * 读取或生成签名密钥（持久化到数据目录，重启不失效）
 * @param {string} dataDir
 * @returns {string}
 */
function loadSecret(dataDir) {
    if (process.env.AUTH_SECRET) return process.env.AUTH_SECRET;
    const file = join(dataDir, 'auth-secret.txt');
    mkdirSync(dirname(file), { recursive: true });
    if (existsSync(file)) {
        const saved = readFileSync(file, 'utf-8').trim();
        if (saved) return saved;
    }
    const secret = randomBytes(32).toString('hex');
    writeFileSync(file, secret, { mode: 0o600 });
    return secret;
}

/** base64url 编码 */
function encode(input) {
    return Buffer.from(input).toString('base64url');
}

/**
 * 签发 token
 * @param {{userId:string, openid:string}} claims
 * @param {string} secret
 */
export function signToken(claims, secret) {
    const payload = { ...claims, exp: Date.now() + TOKEN_TTL_MS };
    const body = encode(JSON.stringify(payload));
    const signature = createHmac('sha256', secret).update(body).digest('base64url');
    return `${body}.${signature}`;
}

/**
 * 校验 token
 * @param {string} token
 * @param {string} secret
 * @returns {{userId:string, openid:string}|null}
 */
export function verifyToken(token, secret) {
    if (typeof token !== 'string') return null;
    const [body, signature] = token.split('.');
    if (!body || !signature) return null;
    const expected = createHmac('sha256', secret).update(body).digest('base64url');
    const givenBuf = Buffer.from(signature);
    const expectedBuf = Buffer.from(expected);
    if (givenBuf.length !== expectedBuf.length) return null;
    if (!timingSafeEqual(givenBuf, expectedBuf)) return null;
    try {
        const payload = JSON.parse(Buffer.from(body, 'base64url').toString('utf-8'));
        if (!payload?.exp || payload.exp < Date.now()) return null;
        if (!payload.userId || !payload.openid) return null;
        return { userId: payload.userId, openid: payload.openid };
    } catch {
        return null;
    }
}

/**
 * 令牌服务
 */
export class TokenService {
    /** @type {string} */
    #secret;

    /** @param {string} dataDir */
    constructor(dataDir) {
        this.#secret = loadSecret(dataDir);
    }

    /**
     * @param {{userId:string, openid:string}} claims
     */
    issue(claims) {
        return signToken(claims, this.#secret);
    }

    /**
     * @param {string} token
     */
    verify(token) {
        return verifyToken(token, this.#secret);
    }
}