// static/src/mrp_display_ext/js/mrp_display_auto_refresh.js

import { patch } from "@web/core/utils/patch";
import { MrpDisplay } from "@mrp_workorder/mrp_display/mrp_display";
import { onMounted, onWillUnmount, useState } from "@odoo/owl";

// 刷新间隔（毫秒）—— 默认 60 秒。可在控制面板的 BurgerMenu 切换开关。
const DEFAULT_REFRESH_INTERVAL = 60000;

patch(MrpDisplay.prototype, {
    setup() {
        super.setup(...arguments);

        // 自动刷新相关状态
        this.autoRefresh = useState({
            enabled: true,
            interval: DEFAULT_REFRESH_INTERVAL,
            remaining: DEFAULT_REFRESH_INTERVAL,
            lastRefreshAt: 0,
        });

        this._autoRefreshTimer = null;
        this._tickTimer = null;

        onMounted(() => {
            this._startAutoRefresh();
        });

        onWillUnmount(() => {
            this._stopAutoRefresh();
        });
    },

    // ------------------------------------------------------------------
    // 自动刷新控制
    // ------------------------------------------------------------------

    /**
     * 启动定时自动刷新 + 倒计时显示
     */
    _startAutoRefresh() {
        this._stopAutoRefresh();
        if (!this.autoRefresh.enabled) {
            return;
        }
        // 倒计时（每秒更新一次）
        this._tickTimer = setInterval(() => {
            this.autoRefresh.remaining = Math.max(
                0,
                this.autoRefresh.remaining - 1000
            );
        }, 1000);
        // 自动刷新
        this._autoRefreshTimer = setInterval(() => {
            this._doAutoRefresh();
        }, this.autoRefresh.interval);
    },

    /**
     * 停止所有定时器
     */
    _stopAutoRefresh() {
        if (this._autoRefreshTimer) {
            clearInterval(this._autoRefreshTimer);
            this._autoRefreshTimer = null;
        }
        if (this._tickTimer) {
            clearInterval(this._tickTimer);
            this._tickTimer = null;
        }
    },

    /**
     * 执行一次自动刷新
     */
    async _doAutoRefresh() {
        // 页面不可见时跳过刷新（节省资源）
        if (document.hidden) {
            this.autoRefresh.remaining = this.autoRefresh.interval;
            return;
        }
        // 用户正在输入或弹窗打开时跳过（避免打断操作）
        const hasOpenDialog = document.querySelector('.modal.show, .o_dialog');
        if (hasOpenDialog) {
            return;
        }
        // 重置倒计时
        this.autoRefresh.remaining = this.autoRefresh.interval;
        this.autoRefresh.lastRefreshAt = Date.now();
        // 调用原生刷新方法
        if (typeof this.onClickRefresh === 'function') {
            this.onClickRefresh();
        }
    },

    /**
     * 切换自动刷新开关（供顶部 BurgerMenu 调用）
     */
    toggleAutoRefresh() {
        this.autoRefresh.enabled = !this.autoRefresh.enabled;
        if (this.autoRefresh.enabled) {
            this.autoRefresh.remaining = this.autoRefresh.interval;
            this._startAutoRefresh();
        } else {
            this._stopAutoRefresh();
        }
    },

    /**
     * 立即刷新并重置倒计时
     */
    async refreshNow() {
        this.autoRefresh.remaining = this.autoRefresh.interval;
        this.autoRefresh.lastRefreshAt = Date.now();
        if (typeof this.onClickRefresh === 'function') {
            await this.onClickRefresh();
        }
        // 重新启动定时器以重置节奏
        if (this.autoRefresh.enabled) {
            this._startAutoRefresh();
        }
    },

    /**
     * 格式化倒计时为 mm:ss
     */
    get autoRefreshCountdown() {
        const sec = Math.ceil(this.autoRefresh.remaining / 1000);
        const m = Math.floor(sec / 60).toString().padStart(2, '0');
        const s = (sec % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    },

    /**
     * 是否显示倒计时（仅在启用了自动刷新时）
     */
    get showAutoRefreshCountdown() {
        return this.autoRefresh.enabled && !this.state.firstLoad;
    },
});
