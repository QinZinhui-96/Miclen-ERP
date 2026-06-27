/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

const TABS = [
    { key: "Core", label: _t("Kern") },
    { key: "Products", label: _t("Produkte") },
    { key: "Integrations", label: _t("Integrationen") },
    { key: "Platform", label: _t("Plattform") },
];

export class PraetorxAppStore extends Component {
    static template = "praetorx_base.AppStore";
    static props = {
        action: { type: Object, optional: true },
        actionId: { type: Number, optional: true },
        updateActionState: { type: Function, optional: true },
        globalState: { type: Object, optional: true },
        className: { type: String, optional: true },
        "*": true,
    };

    setup() {
        this.actionService = useService("action");

        this.state = useState({
            loading: true,
            modules: [],
            activeTab: "Core",
            error: null,
        });

        onWillStart(() => this.loadModules());
    }

    get tabs() {
        return TABS;
    }

    get filteredModules() {
        return this.state.modules.filter(
            (m) => m.category === this.state.activeTab
        );
    }

    get moduleCount() {
        const counts = {};
        for (const tab of TABS) {
            counts[tab.key] = this.state.modules.filter(
                (m) => m.category === tab.key
            ).length;
        }
        return counts;
    }

    async loadModules() {
        this.state.loading = true;
        this.state.error = null;
        try {
            const modules = await rpc("/praetorx/appstore/modules", {});
            this.state.modules = modules || [];
        } catch (error) {
            this.state.error =
                error.message || _t("Fehler beim Laden der Module");
        }
        this.state.loading = false;
    }

    onTabSwitch(tabKey) {
        this.state.activeTab = tabKey;
    }

    getStateBadgeClass(mod) {
        if (mod.state === "installed") return "badge bg-success";
        if (mod.state === "uninstalled") return "badge bg-secondary";
        return "badge bg-warning";
    }

    getStateBadgeLabel(mod) {
        if (mod.state === "installed") return _t("Installiert");
        if (mod.state === "uninstalled") return _t("Verfügbar");
        return _t("Abhängigkeiten fehlen");
    }
}

registry.category("actions").add("praetorx_appstore", PraetorxAppStore);
