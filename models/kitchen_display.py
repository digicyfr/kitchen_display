from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging

_logger = logging.getLogger(__name__)


class KitchenDisplay(models.Model):
    _name = 'kitchen.display'
    _description = 'Professional Kitchen Display Configuration'
    _order = 'sequence, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _check_company_auto = True

    # Basic Information
    name = fields.Char(
        string='Display Name', 
        required=True, 
        tracking=True,
        help="Name of the kitchen display station"
    )
    sequence = fields.Integer(
        string='Sequence', 
        default=10,
        help="Defines the order in which displays are shown"
    )
    
    # Company and Location
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        required=True,
        default=lambda self: self.env.company
    )
    location = fields.Char(
        string='Kitchen Location',
        tracking=True,
        help="Physical location of the display in the kitchen"
    )
    
    # Display Configuration
    is_active = fields.Boolean(
        string='Active', 
        default=True,
        tracking=True
    )
    display_type = fields.Selection([
        ('preparation', 'Preparation Station'),
        ('cooking', 'Cooking Station'),
        ('ready', 'Ready/Pickup Station'),
        ('all', 'All Orders Dashboard'),
        ('custom', 'Custom Filter')
    ], string='Display Type', default='all', required=True, tracking=True)
    
    # POS Integration
    pos_config_ids = fields.Many2many(
        'pos.config',
        'kitchen_display_pos_config_rel',
        'display_id',
        'pos_config_id',
        string='POS Configurations',
        help="POS systems that send orders to this display"
    )
    
    # Category Filtering
    category_ids = fields.Many2many(
        'product.category',
        'kitchen_display_category_rel',
        'display_id',
        'category_id',
        string='Product Categories',
        help="Product categories to display on this screen"
    )
    
    # Timing Configuration
    auto_refresh_interval = fields.Integer(
        string='Auto Refresh (seconds)', 
        default=10,
        help="How often the display refreshes automatically"
    )
    max_orders_display = fields.Integer(
        string='Max Orders to Display', 
        default=50,
        help="Maximum number of orders to show at once"
    )
    order_timeout_warning = fields.Integer(
        string='Order Timeout Warning (minutes)',
        default=15,
        help="Minutes after which orders are highlighted as overdue"
    )
    order_timeout_critical = fields.Integer(
        string='Order Timeout Critical (minutes)',
        default=30,
        help="Minutes after which orders are marked as critically overdue"
    )
    
    # Appearance Settings
    background_color = fields.Char(
        string='Background Color', 
        default='#f8f9fa',
        help="Background color for the display"
    )
    text_color = fields.Char(
        string='Text Color', 
        default='#212529',
        help="Text color for the display"
    )
    font_size = fields.Selection([
        ('small', 'Small (12px)'),
        ('medium', 'Medium (14px)'),
        ('large', 'Large (16px)'),
        ('extra_large', 'Extra Large (18px)')
    ], string='Font Size', default='medium')
    
    # Display Options
    show_customer_name = fields.Boolean(
        string='Show Customer Name', 
        default=True
    )
    show_order_time = fields.Boolean(
        string='Show Order Time', 
        default=True
    )
    show_special_instructions = fields.Boolean(
        string='Show Special Instructions', 
        default=True
    )
    show_table_number = fields.Boolean(
        string='Show Table Number', 
        default=True
    )
    show_order_total = fields.Boolean(
        string='Show Order Total', 
        default=False
    )
    show_preparation_time = fields.Boolean(
        string='Show Preparation Time', 
        default=True
    )
    
    # Sound Settings
    sound_enabled = fields.Boolean(
        string='Enable Sound Notifications', 
        default=True
    )
    sound_new_order = fields.Selection([
        ('beep', 'Beep'),
        ('chime', 'Chime'),
        ('bell', 'Bell'),
        ('none', 'None')
    ], string='New Order Sound', default='chime')
    
    # Layout Settings
    layout_type = fields.Selection([
        ('kanban', 'Kanban Board'),
        ('list', 'List View'),
        ('grid', 'Grid View')
    ], string='Layout Type', default='kanban')
    
    columns_count = fields.Integer(
        string='Columns Count',
        default=4,
        help="Number of columns for grid/kanban layout"
    )
    
    # Advanced Settings
    custom_css = fields.Text(
        string='Custom CSS',
        help="Custom CSS for advanced styling"
    )
    
    # Statistics
    order_count_today = fields.Integer(
        string='Orders Today',
        compute='_compute_order_statistics',
        store=False
    )
    avg_preparation_time = fields.Float(
        string='Avg Preparation Time (min)',
        compute='_compute_order_statistics',
        store=False
    )
    
    # Constraints
    @api.constrains('auto_refresh_interval')
    def _check_refresh_interval(self):
        for record in self:
            if record.auto_refresh_interval < 5:
                raise ValidationError(_('Auto refresh interval must be at least 5 seconds'))
    
    @api.constrains('max_orders_display')
    def _check_max_orders(self):
        for record in self:
            if record.max_orders_display < 1 or record.max_orders_display > 100:
                raise ValidationError(_('Max orders display must be between 1 and 100'))
    
    @api.depends('pos_config_ids')
    def _compute_order_statistics(self):
        for record in self:
            today = fields.Date.today()
            domain = [
                ('display_ids', 'in', record.id),
                ('date_order', '>=', today),
                ('date_order', '<', today + fields.timedelta(days=1))
            ]
            
            orders = self.env['kitchen.order'].search(domain)
            record.order_count_today = len(orders)
            
            if orders:
                total_prep_time = sum(order.actual_preparation_time for order in orders if order.actual_preparation_time)
                record.avg_preparation_time = total_prep_time / len(orders) if orders else 0
            else:
                record.avg_preparation_time = 0
    
    def get_display_data(self, filters=None):
        """Get orders for kitchen display with advanced filtering"""
        self.ensure_one()
        
        # Base domain
        domain = [
            ('company_id', '=', self.company_id.id),
            ('state', 'in', ['new', 'preparing', 'ready'])
        ]
        
        # Add POS config filter
        if self.pos_config_ids:
            domain.append(('pos_config_id', 'in', self.pos_config_ids.ids))
        
        # Add category filter
        if self.category_ids:
            domain.append(('order_line_ids.product_id.categ_id', 'in', self.category_ids.ids))
        
        # Add display type filter
        if self.display_type != 'all':
            if self.display_type == 'preparation':
                domain.append(('state', '=', 'new'))
            elif self.display_type == 'cooking':
                domain.append(('state', '=', 'preparing'))
            elif self.display_type == 'ready':
                domain.append(('state', '=', 'ready'))
        
        # Add custom filters
        if filters:
            for key, value in filters.items():
                if key == 'priority' and value:
                    domain.append(('priority', '=', value))
                elif key == 'table_number' and value:
                    domain.append(('table_number', '=', value))
        
        # Search orders
        orders = self.env['kitchen.order'].search(domain, limit=self.max_orders_display)
        
        # Format data for display
        result = []
        for order in orders:
            result.append({
                'id': order.id,
                'name': order.name,
                'customer_name': order.customer_name,
                'table_number': order.table_number,
                'status': order.status,
                'priority': order.priority,
                'order_time': order.order_time,
                'elapsed_time': order.elapsed_time,
                'estimated_time': order.estimated_time,
                'special_instructions': order.special_instructions,
                'display_color': order.display_color,
                'order_lines': [{
                    'product_name': line.product_name,
                    'quantity': line.quantity,
                    'special_instructions': line.special_instructions,
                } for line in order.order_lines]
            })
        
        return result
    
    def action_refresh_display(self):
        """Manual refresh action for display"""
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }