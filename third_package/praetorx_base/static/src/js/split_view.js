/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

/**
 * Split View Component - Master-Detail Pattern
 *
 * Provides a reusable OWL component for split view layouts with a master list
 * on the left and detail view on the right. Commonly used in:
 * - Email clients (message list + message detail)
 * - Settings panels (category list + settings form)
 * - Document browsers (file list + preview)
 *
 * Usage in XML:
 * <SplitView
 *     masterItems="state.items"
 *     selectedId="state.selectedId"
 *     onSelect.bind="onItemSelect"
 *     masterWidth="'30%'"
 * >
 *     <t t-set-slot="master" t-slot-scope="item">
 *         <div t-esc="item.name"/>
 *     </t>
 *     <t t-set-slot="detail" t-slot-scope="selected">
 *         <div t-esc="selected.description"/>
 *     </t>
 * </SplitView>
 */
export class SplitView extends Component {
    static template = "praetorx_base.SplitView";
    static props = {
        masterItems: { type: Array, optional: true },
        selectedId: { type: [Number, String, Boolean], optional: true },
        onSelect: { type: Function, optional: true },
        masterWidth: { type: String, optional: true },
        detailWidth: { type: String, optional: true },
        showBorder: { type: Boolean, optional: true },
        slots: { type: Object, optional: true },
    };

    static defaultProps = {
        masterItems: [],
        selectedId: false,
        masterWidth: "35%",
        detailWidth: "65%",
        showBorder: true,
    };

    setup() {
        this.state = useState({
            selectedId: this.props.selectedId || false,
        });
    }

    /**
     * Get the currently selected item from masterItems
     */
    get selectedItem() {
        if (!this.state.selectedId || !this.props.masterItems) {
            return null;
        }
        return this.props.masterItems.find(
            item => item.id === this.state.selectedId
        );
    }

    /**
     * Handle item selection
     */
    onItemClick(item) {
        this.state.selectedId = item.id;
        if (this.props.onSelect) {
            this.props.onSelect(item);
        }
    }

    /**
     * Check if item is selected
     */
    isSelected(item) {
        return item.id === this.state.selectedId;
    }

    /**
     * Get master panel style
     */
    get masterStyle() {
        return `width: ${this.props.masterWidth}; min-width: 200px;`;
    }

    /**
     * Get detail panel style
     */
    get detailStyle() {
        return `width: ${this.props.detailWidth};`;
    }

    /**
     * Get border class
     */
    get borderClass() {
        return this.props.showBorder ? 'border-end' : '';
    }
}

registry.category("components").add("SplitView", SplitView);
