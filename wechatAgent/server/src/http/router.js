/**
 * 极简路由表
 * 支持 `/api/sessions/:id/messages` 形式的路径参数
 */

/**
 * 把路径模板编译为匹配器
 * @param {string} pattern
 */
function compile(pattern) {
    const keys = [];
    const regexSource = pattern
        .split('/')
        .map((segment) => {
            if (!segment.startsWith(':')) {
                return segment.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            }
            keys.push(segment.slice(1));
            return '([^/]+)';
        })
        .join('/');
    return { regex: new RegExp(`^${regexSource}/?$`), keys };
}

export class Router {
    /** @type {Array<{method:string, regex:RegExp, keys:string[], handler:Function}>} */
    #routes = [];

    /**
     * 注册路由
     * @param {string} method
     * @param {string} pattern
     * @param {Function} handler
     */
    add(method, pattern, handler) {
        const { regex, keys } = compile(pattern);
        this.#routes.push({ method: method.toUpperCase(), regex, keys, handler });
        return this;
    }

    get(pattern, handler) {
        return this.add('GET', pattern, handler);
    }

    post(pattern, handler) {
        return this.add('POST', pattern, handler);
    }

    patch(pattern, handler) {
        return this.add('PATCH', pattern, handler);
    }

    delete(pattern, handler) {
        return this.add('DELETE', pattern, handler);
    }

    /**
     * 匹配路由
     * @param {string} method
     * @param {string} pathname
     * @returns {{handler:Function, params:Object}|null}
     */
    match(method, pathname) {
        for (const route of this.#routes) {
            if (route.method !== method.toUpperCase()) continue;
            const matched = route.regex.exec(pathname);
            if (!matched) continue;
            const params = {};
            route.keys.forEach((key, index) => {
                params[key] = decodeURIComponent(matched[index + 1]);
            });
            return { handler: route.handler, params };
        }
        return null;
    }
}