from odoo import models, fields, api, _
from odoo.exceptions import UserError


class KitchenDisplaySetupWizard(models.TransientModel):
    _name = 'kitchen.display.setup.wizard'
    _description = 'Kitchen Display Setup Wizard'

    # Basic Configuration
    display_name = fields.Char(
        string='Display Name',
        required=True,
        default='Main Kitchen Display',
        help="Name for your kitchen display"
    )
    
    location = fields.Char(
        string='Kitchen Location',
        help="Physical location of the display"
    )
    
    display_type = fields.Selection([
        ('all', 'All Orders Dashboard'),
        ('preparation', 'Preparation Station'),
        ('cooking', 'Cooking Station'),
        ('ready', 'Ready/Pickup Station'),
        ('custom', 'Custom Filter')
    ], string='Display Type', default='all', required=True)
    
    # POS Configuration
    pos_config_ids = fields.Many2many(
        'pos.config',
        string='POS Configurations',
        help="Select POS systems that will send orders to this display"
    )
    
    # Category Configuration
    category_ids = fields.Many2many(
        'product.category',
        string='Product Categories',
        help="Select product categories to display (leave empty for all)"
    )
    
    # Display Settings
    auto_refresh_interval = fields.Integer(
        string='Auto Refresh (seconds)',
        default=10,
        help="How often the display refreshes automatically"
    )
    
    max_orders_display = fields.Integer(
        string='Maximum Orders',
        default=20,
        help="Maximum number of orders to show at once"
    )
    
    # Appearance
    layout_type = fields.Selection([
        ('kanban', 'Kanban Board'),
        ('list', 'List View'),
        ('grid', 'Grid View')
    ], string='Layout', default='kanban')
    
    show_customer_name = fields.Boolean(
        string='Show Customer Names',
        default=True
    )
    
    show_table_number = fields.Boolean(
        string='Show Table Numbers',
        default=True
    )
    
    show_special_instructions = fields.Boolean(
        string='Show Special Instructions',
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
    
    # Setup Options
    create_demo_data = fields.Boolean(
        string='Create Demo Orders',
        default=True,
        help="Create sample orders for testing the display"
    )
    
    setup_pos_integration = fields.Boolean(
        string='Setup POS Integration',
        default=True,
        help="Automatically create kitchen orders from POS"
    )
    
    @api.constrains('auto_refresh_interval')
    def _check_refresh_interval(self):
        for wizard in self:
            if wizard.auto_refresh_interval < 5 or wizard.auto_refresh_interval > 300:
                raise UserError(_('Auto refresh interval must be between 5 and 300 seconds'))
    
    @api.constrains('max_orders_display')
    def _check_max_orders(self):
        for wizard in self:
            if wizard.max_orders_display < 1 or wizard.max_orders_display > 100:
                raise UserError(_('Maximum orders must be between 1 and 100'))
    
    def action_create_display(self):
        """Create kitchen display with configured settings"""
        self.ensure_one()
        
        # Create kitchen display
        display_vals = {
            'name': self.display_name,
            'location': self.location,
            'display_type': self.display_type,
            'pos_config_ids': [(6, 0, self.pos_config_ids.ids)],
            'category_ids': [(6, 0, self.category_ids.ids)],
            'auto_refresh_interval': self.auto_refresh_interval,
            'max_orders_display': self.max_orders_display,
            'layout_type': self.layout_type,
            'show_customer_name': self.show_customer_name,
            'show_table_number': self.show_table_number,
            'show_special_instructions': self.show_special_instructions,
            'sound_enabled': self.sound_enabled,
            'sound_new_order': self.sound_new_order,
            'is_active': True,
        }
        
        display = self.env['kitchen.display'].create(display_vals)
        
        # Create demo data if requested
        if self.create_demo_data:
            self._create_demo_orders(display)
        
        # Setup POS integration if requested
        if self.setup_pos_integration:
            self._setup_pos_integration()
        
        # Return action to view the created display
        return {
            'type': 'ir.actions.act_window',
            'name': _('Kitchen Display Created'),
            'res_model': 'kitchen.display',
            'res_id': display.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _create_demo_orders(self, display):
        """Create demo orders for testing"""
        
        # Get or create demo products
        demo_products = self._get_or_create_demo_products()
        
        # Create demo orders
        for i in range(3):
            order_vals = {
                'name': f'DEMO-{str(i+1).zfill(3)}',
                'customer_name': ['John Doe', 'Jane Smith', 'Bob Johnson'][i],
                'table_number': f'Table {i+1}',
                'state': ['new', 'preparing', 'ready'][i],
                'priority': 'normal',
                'estimated_time': 15,
                'special_instructions': 'Demo order for testing' if i == 0 else '',
                'delivery_platform': 'pos',
                'display_ids': [(6, 0, [display.id])],
            }
            
            order = self.env['kitchen.order'].create(order_vals)
            
            # Create order lines
            if demo_products:
                self.env['kitchen.order.line'].create({
                    'order_id': order.id,
                    'product_id': demo_products[i % len(demo_products)].id,
                    'quantity': 1,
                })
    
    def _get_or_create_demo_products(self):
        """Get existing or create demo products"""
        products = self.env['product.product'].search([
            ('available_in_pos', '=', True)
        ], limit=5)
        
        if not products:
            # Create basic demo products
            category = self.env['product.category'].search([
                ('name', '=', 'All')
            ], limit=1)
            
            if not category:
                category = self.env['product.category'].create({
                    'name': 'Demo Food Items'
                })
            
            product_data = [
                {'name': 'Demo Burger', 'list_price': 12.50},
                {'name': 'Demo Pizza', 'list_price': 15.00},
                {'name': 'Demo Salad', 'list_price': 8.50},
            ]
            
            products = self.env['product.product']
            for data in product_data:
                product = self.env['product.product'].create({
                    'name': data['name'],
                    'type': 'consu',
                    'list_price': data['list_price'],
                    'categ_id': category.id,
                    'available_in_pos': True,
                })
                products += product
        
        return products
    
    def _setup_pos_integration(self):
        """Setup automatic POS integration"""
        # This would typically involve configuring webhooks or 
        # event listeners for POS order creation
        # For now, we'll just ensure the POS configs are properly linked
        pass
    
    def action_skip_setup(self):
        """Skip wizard and go to kitchen display list"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Kitchen Displays'),
            'res_model': 'kitchen.display',
            'view_mode': 'tree,form',
            'target': 'current',
        }