/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * Kitchen Board Real-time Component
 * Listens to bus.bus for real-time order updates
 */
export class KitchenBoard extends Component {
    setup() {
        this.orm = useService("orm");
        this.busService = useService("bus_service");
        this.notification = useService("notification");
        this.action = useService("action");

        this.state = useState({
            displayId: null,
            companyId: null,
            orders: [],
            lastUpdate: null,
        });

        onWillStart(async () => {
            await this.loadInitialData();
            this.subscribeToNotifications();
        });

        onMounted(() => {
            console.log("Kitchen Board Component Mounted");
            // Start periodic refresh as fallback
            this.startPeriodicRefresh();
        });

        onWillUnmount(() => {
            console.log("Kitchen Board Component Unmounted");
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
        });
    }

    async loadInitialData() {
        // Get display configuration from context
        const context = this.env.context || {};
        this.state.displayId = context.active_display_id;
        this.state.companyId = context.allowed_company_ids ? context.allowed_company_ids[0] : null;

        console.log(`Kitchen Board initialized for display: ${this.state.displayId}, company: ${this.state.companyId}`);
    }

    subscribeToNotifications() {
        // Subscribe to display-specific channel
        if (this.state.displayId) {
            const displayChannel = `kitchen_display_${this.state.displayId}`;
            this.busService.addEventListener('notification', ({ detail }) => {
                this.handleBusNotification(detail);
            });
            this.busService.addChannel(displayChannel);
            console.log(`Subscribed to channel: ${displayChannel}`);
        }

        // Subscribe to general company channel
        if (this.state.companyId) {
            const companyChannel = `kitchen_display_all_${this.state.companyId}`;
            this.busService.addChannel(companyChannel);
            console.log(`Subscribed to channel: ${companyChannel}`);
        }
    }

    handleBusNotification(notifications) {
        for (const notification of notifications) {
            const [channel, message] = notification;

            if (message.type === 'kitchen.order.update') {
                this.handleOrderUpdate(message.payload);
            }
        }
    }

    handleOrderUpdate(orderData) {
        console.log('Kitchen Order Update:', orderData);

        // Show notification for new orders
        if (orderData.event === 'new_order') {
            this.notification.add(
                `New Order: ${orderData.order_name} - Table ${orderData.table_number || 'N/A'}`,
                {
                    type: 'info',
                    sticky: false,
                    className: 'kitchen_new_order_notification',
                }
            );

            // Play sound if configured
            this.playNotificationSound('new_order');
        } else if (orderData.event === 'state_change') {
            // Update UI without full page refresh
            this.refreshKanbanView();
        }

        this.state.lastUpdate = new Date();
    }

    playNotificationSound(soundType) {
        try {
            // Sound will be played via browser audio API
            // You can add audio files to static/src/sounds/ directory
            const audio = new Audio(`/kitchen_display/static/src/sounds/${soundType}.mp3`);
            audio.volume = 0.5;
            audio.play().catch(err => {
                console.warn('Could not play notification sound:', err);
            });
        } catch (error) {
            console.warn('Sound playback not available:', error);
        }
    }

    refreshKanbanView() {
        // Trigger kanban view refresh
        this.action.doAction('kitchen_display.kitchen_order_action_kanban', {
            clearBreadcrumbs: false,
        });
    }

    startPeriodicRefresh() {
        // Fallback refresh every 30 seconds in case bus notifications fail
        this.refreshInterval = setInterval(() => {
            const now = new Date();
            const timeSinceLastUpdate = this.state.lastUpdate
                ? (now - this.state.lastUpdate) / 1000
                : 999;

            // Only refresh if no bus updates received in last 30 seconds
            if (timeSinceLastUpdate > 30) {
                console.log('Fallback refresh triggered');
                this.refreshKanbanView();
            }
        }, 30000); // 30 seconds
    }
}

KitchenBoard.template = "kitchen_display.KitchenBoardComponent";

// Register the component
registry.category("actions").add("kitchen_display.kitchen_board", KitchenBoard);
