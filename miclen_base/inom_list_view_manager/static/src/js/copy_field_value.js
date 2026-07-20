/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

patch(ListRenderer.prototype, {

    setup() {
        super.setup(...arguments);
    },

    // ─────────────────────────────────────────────────────────────────────────
    // CHANGED BEHAVIOUR
    //   • SINGLE click on a data cell  -> open the form view (Odoo default).
    //   • The copy-to-clipboard feature is removed from click to avoid
    //     intercepting the single-click-to-open behaviour.
    //
    // The original module hijacked single clicks to copy cell values, which
    // prevented single-click from opening the form view. Now we simply let
    // the original onCellClicked run unmodified.
    // ─────────────────────────────────────────────────────────────────────────
    async onCellClicked(record, column, ev, newWindow) {
        // Always defer to Odoo's default behaviour:
        //   - non-editable list → openRecord (form view)
        //   - editable list → enter edit mode
        //   - selection mode → toggle selection
        return super.onCellClicked(record, column, ev, newWindow);
    },
});
