from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError
import json
import logging

_logger = logging.getLogger(__name__)


class KitchenDisplayController(http.Controller):
    """Professional Kitchen Display Controller for Restaurant Operations"""

    @http.route('/kitchen_display/orders', type='json', auth='user', methods=['POST'])
    def get_kitchen_orders(self, display_id=None, filters=None):
        """Get orders for kitchen display with optional filtering"""
        try:
            if not display_id:
                return {'success': False, 'error': _('Display ID is required')}
            
            display = request.env['kitchen.display'].browse(int(display_id))
            if not display.exists():
                return {'success': False, 'error': _('Kitchen display not found')}
            
            # Check access rights
            display.check_access_rights('read')
            
            data = display.get_display_data(filters or {})
            return {
                'success': True, 
                'data': data,
                'display_info': {
                    'name': display.name,
                    'location': display.location,
                    'auto_refresh_interval': display.auto_refresh_interval,
                }
            }
        except AccessError as e:
            _logger.warning(f"Access denied for kitchen display {display_id}: {e}")
            return {'success': False, 'error': _('Access denied')}
        except Exception as e:
            _logger.error(f"Error getting kitchen orders: {e}")
            return {'success': False, 'error': _('An error occurred while fetching orders')}

    @http.route('/kitchen_display/update_order_status', type='json', auth='user', methods=['POST'])
    def update_order_status(self, order_id, action):
        """Update order status with proper validation and logging"""
        try:
            if not order_id or not action:
                return {'success': False, 'error': _('Order ID and action are required')}
            
            order = request.env['kitchen.order'].browse(int(order_id))
            if not order.exists():
                return {'success': False, 'error': _('Order not found')}
            
            # Check access rights
            order.check_access_rights('write')
            
            # Map actions to methods
            action_methods = {
                'start_preparation': 'action_start_preparation',
                'preparing': 'action_start_preparation',
                'ready': 'action_mark_ready',
                'served': 'action_mark_served',
                'cancel': 'action_cancel_order',
            }
            
            if action not in action_methods:
                return {'success': False, 'error': _('Invalid action: %s') % action}
            
            # Execute the action
            method = getattr(order, action_methods[action])
            result = method()
            
            _logger.info(f"Order {order.name} status updated to {action} by user {request.env.user.name}")
            
            return {
                'success': True, 
                'message': _('Order status updated successfully'),
                'order_state': order.state,
                'order_name': order.name
            }
            
        except AccessError as e:
            _logger.warning(f"Access denied for order {order_id}: {e}")
            return {'success': False, 'error': _('Access denied')}
        except ValidationError as e:
            _logger.warning(f"Validation error for order {order_id}: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Error updating order status: {e}")
            return {'success': False, 'error': _('An error occurred while updating order status')}

    @http.route('/kitchen_display/create_order', type='json', auth='user', methods=['POST'])
    def create_kitchen_order(self, order_data):
        """Create a new kitchen order with validation"""
        try:
            if not order_data:
                return {'success': False, 'error': _('Order data is required')}
            
            # Validate required fields
            required_fields = ['customer_name']
            for field in required_fields:
                if field not in order_data:
                    return {'success': False, 'error': _('Missing required field: %s') % field}
            
            # Check access rights
            request.env['kitchen.order'].check_access_rights('create')
            
            order = request.env['kitchen.order'].create(order_data)
            
            _logger.info(f"Kitchen order {order.name} created by user {request.env.user.name}")
            
            return {
                'success': True, 
                'order_id': order.id, 
                'order_name': order.name,
                'message': _('Order created successfully')
            }
            
        except AccessError as e:
            _logger.warning(f"Access denied for order creation: {e}")
            return {'success': False, 'error': _('Access denied')}
        except ValidationError as e:
            _logger.warning(f"Validation error for order creation: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Error creating kitchen order: {e}")
            return {'success': False, 'error': _('An error occurred while creating the order')}

    @http.route('/kitchen_display/display/<int:display_id>', type='http', auth='user')
    def kitchen_display_view(self, display_id):
        """Kitchen display view"""
        display = request.env['kitchen.display'].browse(display_id)
        if not display.exists():
            return request.not_found()
        
        return request.render('kitchen_display.kitchen_display_fullscreen', {
            'display': display,
            'display_id': display_id
        })
    
    @http.route('/kitchen_display/fullscreen', type='http', auth='user')
    def kitchen_display_fullscreen(self, display_id=None):
        """Full-screen kitchen display"""
        display = None
        if display_id:
            display = request.env['kitchen.display'].browse(int(display_id))
            if not display.exists():
                display = None
        
        if not display:
            # Get the first active display or create a default one
            display = request.env['kitchen.display'].search([('is_active', '=', True)], limit=1)
            if not display:
                display = request.env['kitchen.display'].create({
                    'name': 'Default Kitchen Display',
                    'location': 'Main Kitchen',
                    'display_type': 'all',
                    'is_active': True
                })
        
        return request.render('kitchen_display.kitchen_display_fullscreen', {
            'display': display,
            'display_id': display.id
        })