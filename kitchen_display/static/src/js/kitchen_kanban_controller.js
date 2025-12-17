/** @odoo-module **/

import { KanbanController } from "@web/views/kanban/kanban_controller";
import { patch } from "@web/core/utils/patch";

/**
 * Kitchen Display Kanban Controller with Auto-Refresh
 * Automatically refreshes the view every few seconds for real-time updates
 */
patch(KanbanController.prototype, {
    setup() {
        super.setup(...arguments);

        // Check if this is the kitchen board view
        const context = this.props.context || {};
        if (context.kitchen_board) {
            console.log("Kitchen Board Auto-Refresh Enabled");
            this.startKitchenAutoRefresh();
        }
    },

    /**
     * Start auto-refresh for kitchen board
     */
    startKitchenAutoRefresh() {
        // Get refresh interval from context or use default (10 seconds)
        const context = this.props.context || {};
        const refreshInterval = (context.auto_refresh_interval || 10) * 1000; // Convert to ms

        console.log(`Kitchen Board: Auto-refresh every ${refreshInterval/1000} seconds`);

        // Clear any existing interval
        if (this.kitchenRefreshInterval) {
            clearInterval(this.kitchenRefreshInterval);
        }

        // Set up periodic refresh
        this.kitchenRefreshInterval = setInterval(() => {
            console.log("Kitchen Board: Auto-refreshing view...");
            this.model.root.load();
        }, refreshInterval);
    },

    /**
     * Clean up interval on component unmount
     */
    onWillUnmount() {
        if (this.kitchenRefreshInterval) {
            clearInterval(this.kitchenRefreshInterval);
            console.log("Kitchen Board: Auto-refresh stopped");
        }
        super.onWillUnmount(...arguments);
    },
});

console.log("Kitchen Kanban Controller with Auto-Refresh loaded");
