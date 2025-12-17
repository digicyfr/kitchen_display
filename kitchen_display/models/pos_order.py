from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    """Extend POS Order to automatically create Kitchen Display orders"""
    _inherit = 'pos.order'

    kitchen_order_id = fields.Many2one(
        'kitchen.order',
        string='Kitchen Order',
        readonly=True,
        help="Linked kitchen display order"
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically generate kitchen orders"""
        # Create POS orders first
        orders = super(PosOrder, self).create(vals_list)

        # Automatically create kitchen orders for all POS orders with lines
        for order in orders:
            if order.lines and not order.kitchen_order_id:
                try:
                    _logger.info(f"Attempting to create kitchen order for POS order {order.name}")
                    kitchen_order = self.env['kitchen.order'].create_from_pos_order(order)
                    if kitchen_order:
                        order.kitchen_order_id = kitchen_order.id
                        _logger.info(f"✓ Kitchen order {kitchen_order.name} created successfully for POS order {order.name}")
                    else:
                        _logger.warning(f"✗ Kitchen order creation returned None for POS order {order.name}")
                except Exception as e:
                    # Don't block POS order creation if kitchen order fails
                    _logger.error(f"✗ Failed to create kitchen order for POS order {order.name}: {e}", exc_info=True)

        return orders

    def action_pos_order_paid(self):
        """Override to update kitchen order when POS order is paid"""
        result = super(PosOrder, self).action_pos_order_paid()

        # Update kitchen order status when paid
        for order in self:
            if order.kitchen_order_id and order.kitchen_order_id.state == 'new':
                try:
                    # Automatically move to preparing when order is paid
                    order.kitchen_order_id.action_start_preparation()
                    _logger.info(f"Kitchen order {order.kitchen_order_id.name} moved to preparing after payment")
                except Exception as e:
                    _logger.warning(f"Could not update kitchen order status: {e}")

        return result
