/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";

const SCROLL_THRESHOLD = 300;

const SCROLL_SELECTOR = ".o_content, .o_list_renderer, .o_form_sheet_bg, .settings";

export class BackToTopButton extends Component {
    static template = "inom_list_view_manager.BackToTopButton";
    static props = {};

    setup() {
        this.state = useState({ visible: false });
        this.scrollEl = null;
        this._onScroll = this._onScroll.bind(this);

        onMounted(() => {
            document.addEventListener("scroll", this._onScroll, true);
        });
        onWillUnmount(() => {
            document.removeEventListener("scroll", this._onScroll, true);
        });
    }

    get label() {
        return "回到顶部";
    }

    _onScroll(ev) {
        const target = ev.target;
        if (!target || target.nodeType !== 1 || typeof target.matches !== "function") {
            return;
        }
        if (!target.matches(SCROLL_SELECTOR)) {
            return;
        }
        this.scrollEl = target;
        this.state.visible = target.scrollTop > SCROLL_THRESHOLD;
    }

    onClick() {
        if (this.scrollEl) {
            this.scrollEl.scrollTo({ top: 0, behavior: "smooth" });
        }
        this.state.visible = false;
    }
}

registry.category("main_components").add("inom_list_view_manager.BackToTopButton", {
    Component: BackToTopButton,
});
