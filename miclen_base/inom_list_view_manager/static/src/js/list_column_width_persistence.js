/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";
import { ListRenderer } from "@web/views/list/list_renderer";
import { session } from "@web/session";
import { onMounted, onPatched, useExternalListener } from "@odoo/owl";

/**
 * Column width persistence — ported from atliis_list_column_width_saver.
 *
 * Hooks into Odoo 19's native columnWidths mechanism: when the user drags
 * a column resize handle, the new widths are saved to localStorage keyed
 * per database + user + view. On mount / patch the saved widths are
 * restored automatically.
 *
 * Storage key:  inom.list_column_widths.{db}.{uid}.{viewKey}
 */

const STORAGE_PREFIX = "inom.list_column_widths";
const STORAGE_VERSION = 1;

patch(ListRenderer.prototype, {
    setup() {
        super.setup(...arguments);

        this._inomColWidthStorageKey = this._inomColWidthGetStorageKey();
        this._inomColResizeInProgress = false;

        // ── Hook into Odoo's native columnWidths ──────────────────────
        const originalStartResize = this.columnWidths.onStartResize.bind(this.columnWidths);
        this.columnWidths.onStartResize = (ev) => {
            this._inomColResizeInProgress = true;
            originalStartResize(ev);
        };

        const originalResetWidths = this.columnWidths.resetWidths.bind(this.columnWidths);
        this.columnWidths.resetWidths = () => {
            this._inomColWidthClearStored();
            originalResetWidths();
        };

        // ── Save widths after resize ends (pointerup / keydown) ───────
        const saveAfterResizeStop = (ev) => {
            if (!this._inomColResizeInProgress) {
                return;
            }
            // Ignore the initial left-click pointerdown that started resize.
            if (ev.type === "pointerdown" && ev.button === 0) {
                return;
            }
            browser.setTimeout(() => {
                this._inomColResizeInProgress = false;
                this._inomColWidthStore();
            });
        };

        useExternalListener(window, "pointerup", saveAfterResizeStop);
        useExternalListener(window, "pointerdown", saveAfterResizeStop);
        useExternalListener(window, "keydown", saveAfterResizeStop);

        // ── Restore saved widths on mount / patch ─────────────────────
        const restoreStoredWidths = () => {
            if (this._inomColResizeInProgress) {
                return;
            }
            this._inomColWidthRestore();
        };

        onMounted(() => {
            browser.setTimeout(restoreStoredWidths);
        });
        onPatched(() => browser.setTimeout(restoreStoredWidths));
    },

    // ───────────────────────────────────────────────────────────────────
    //  Storage key:  inom.list_column_widths.{db}.{uid}.{viewKey}
    // ───────────────────────────────────────────────────────────────────
    _inomColWidthGetStorageKey() {
        const dbName = session.db || "default_db";
        return `${STORAGE_PREFIX}.${dbName}.${user.userId}.${this.createViewKey()}`;
    },

    /**
     * Build a hash from column ids + header count so we don't restore
     * widths on a view whose columns have changed.
     */
    _inomColWidthBuildHash(headersLength) {
        return `${this.columns.map((column) => column.id).join("/")}/${headersLength}`;
    },

    _inomColWidthGetHeaders() {
        const table = this.tableRef?.el;
        if (!table) {
            return null;
        }
        const headers = [...table.querySelectorAll("thead th")];
        if (!headers.length) {
            return null;
        }
        return headers;
    },

    // ── Save ──────────────────────────────────────────────────────────
    _inomColWidthStore() {
        const headers = this._inomColWidthGetHeaders();
        if (!headers) {
            return;
        }
        const table = this.tableRef.el;
        const payload = {
            version: STORAGE_VERSION,
            hash: this._inomColWidthBuildHash(headers.length),
            widths: headers.map((th) => Math.floor(th.getBoundingClientRect().width)),
            tableWidth: table.style.width || null,
        };
        try {
            browser.localStorage.setItem(this._inomColWidthStorageKey, JSON.stringify(payload));
        } catch {
            // Ignore storage quota / access errors.
        }
    },

    // ── Read ──────────────────────────────────────────────────────────
    _inomColWidthReadStored() {
        try {
            const rawValue = browser.localStorage.getItem(this._inomColWidthStorageKey);
            if (!rawValue) {
                return null;
            }
            const payload = JSON.parse(rawValue);
            if (
                !payload ||
                payload.version !== STORAGE_VERSION ||
                !Array.isArray(payload.widths) ||
                !payload.widths.length ||
                payload.widths.some((value) => !Number.isFinite(value) || value <= 0)
            ) {
                return null;
            }
            return payload;
        } catch {
            return null;
        }
    },

    // ── Restore ───────────────────────────────────────────────────────
    _inomColWidthRestore() {
        const headers = this._inomColWidthGetHeaders();
        if (!headers) {
            return false;
        }
        const payload = this._inomColWidthReadStored();
        if (!payload) {
            return false;
        }
        // Column count changed — don't restore stale widths.
        if (payload.widths.length !== headers.length) {
            return false;
        }
        // Column set changed — don't restore stale widths.
        if (payload.hash !== this._inomColWidthBuildHash(headers.length)) {
            return false;
        }

        const table = this.tableRef.el;
        table.style.tableLayout = "fixed";
        headers.forEach((th, index) => {
            th.style.width = `${Math.floor(payload.widths[index])}px`;
        });
        if (payload.tableWidth) {
            table.style.width = payload.tableWidth;
        }
        return true;
    },

    // ── Clear (called when user resets widths) ────────────────────────
    _inomColWidthClearStored() {
        try {
            browser.localStorage.removeItem(this._inomColWidthStorageKey);
        } catch {
            // Ignore storage access errors.
        }
    },
});
