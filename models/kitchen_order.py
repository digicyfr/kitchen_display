from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class KitchenOrder(models.Model):
    _name = 'kitchen.order'
    _description = 'Professional Kitchen Order Management'
    _order = 'priority desc, create_date asc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _check_company_auto = True
    _rec_name = 'display_name'

    # Basic Information
    name = fields.Char(
        string='Order Number', 
        required=True, 
        default=lambda self: self.env['ir.sequence'].next_by_code('kitchen.order') or 'New',
        copy=False,
        tracking=True
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    # POS Integration
    pos_order_id = fields.Many2one(
        'pos.order', 
        string='POS Order', 
        ondelete='cascade',
        index=True
    )
    pos_config_id = fields.Many2one(
        'pos.config',
        string='POS Configuration',
        related='pos_order_id.config_id',
        store=True,
        index=True
    )
    
    # Customer Information
    customer_name = fields.Char(
        string='Customer Name',
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='pos_order_id.partner_id',
        store=True
    )
    
    # Company and Multi-company support
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        required=True,
        default=lambda self: self.env.company,
        index=True
    )
    
    # Order Status and Workflow
    state = fields.Selection([
        ('new', 'New Order'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('served', 'Served'),
        ('cancelled', 'Cancelled')
    ], string='State', default='new', required=True, tracking=True, index=True)
    
    # Legacy field for backward compatibility
    status = fields.Selection([
        ('to_cook', 'To Cook'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', compute='_compute_status', store=False)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal', required=True)
    
    order_time = fields.Datetime(string='Order Time', default=fields.Datetime.now)
    cooking_time = fields.Datetime(string='Cooking Started')
    ready_time = fields.Datetime(string='Ready Time')
    completed_time = fields.Datetime(string='Completed Time')
    
    estimated_time = fields.Integer(string='Estimated Time (minutes)', default=15)
    elapsed_time = fields.Integer(string='Elapsed Time (minutes)', compute='_compute_elapsed_time', store=True)
    
    special_instructions = fields.Text(string='Special Instructions')
    table_number = fields.Char(string='Table Number')
    
    # Timing Information
    actual_preparation_time = fields.Float(
        string='Actual Preparation Time (min)',
        compute='_compute_actual_preparation_time',
        store=True,
        help="Actual time taken to prepare the order"
    )
    
    # Kitchen Display Assignment
    display_ids = fields.Many2many(
        'kitchen.display',
        'kitchen_order_display_rel',
        'order_id',
        'display_id',
        string='Kitchen Displays',
        help="Kitchen displays that should show this order"
    )
    
    # Order Lines
    order_lines = fields.One2many(
        'kitchen.order.line', 
        'order_id', 
        string='Order Lines',
        copy=True
    )
    order_line_count = fields.Integer(
        string='Line Count',
        compute='_compute_order_line_count',
        store=True
    )
    
    # Display and UI fields
    display_color = fields.Char(
        string='Display Color', 
        compute='_compute_display_color',
        help="Color indicator based on priority and timing"
    )
    status_display = fields.Char(
        string='Status Display', 
        compute='_compute_status_display', 
        store=False
    )
    
    # Integration fields
    external_order_id = fields.Char(
        string='External Order ID',
        help="Order ID from external delivery platforms"
    )
    delivery_platform = fields.Selection([
        ('pos', 'Point of Sale'),
        ('glovo', 'Glovo'),
        ('uber_eats', 'Uber Eats'),
        ('deliveroo', 'Deliveroo'),
        ('just_eat', 'Just Eat'),
        ('bolt_food', 'Bolt Food'),
        ('wolt', 'Wolt'),
        ('other', 'Other')
    ], string='Platform', default='pos')
    
    # Currency and totals
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        store=True
    )
    total_amount = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        related='pos_order_id.amount_total',
        store=True
    )
    
    @api.depends('name', 'customer_name', 'table_number')
    def _compute_display_name(self):
        """Compute display name for the order"""
        for order in self:
            parts = [order.name]
            if order.table_number:
                parts.append(f"Table {order.table_number}")
            if order.customer_name:
                parts.append(f"({order.customer_name})")
            order.display_name = " - ".join(parts)
    
    @api.depends('state')
    def _compute_status(self):
        """Compute legacy status field for backward compatibility"""
        for order in self:
            if order.state == 'new':
                order.status = 'to_cook'
            elif order.state == 'preparing':
                order.status = 'to_cook'
            elif order.state == 'ready':
                order.status = 'ready'
            elif order.state == 'served':
                order.status = 'completed'
            elif order.state == 'cancelled':
                order.status = 'cancelled'
            else:
                order.status = 'to_cook'

    @api.depends('order_time', 'state')
    def _compute_elapsed_time(self):
        """Compute elapsed time since order was placed"""
        for order in self:
            if order.order_time and order.state not in ['served', 'cancelled']:
                now = fields.Datetime.now()
                elapsed = now - order.order_time
                order.elapsed_time = int(elapsed.total_seconds() / 60)
            else:
                order.elapsed_time = 0
    
    @api.depends('elapsed_time', 'estimated_time', 'priority', 'state')
    def _compute_actual_preparation_time(self):
        """Compute actual preparation time when order is completed"""
        for order in self:
            if order.state == 'served' and order.order_time and order.completed_time:
                time_diff = order.completed_time - order.order_time
                order.actual_preparation_time = time_diff.total_seconds() / 60.0
            else:
                order.actual_preparation_time = 0.0
    
    @api.depends('order_lines')
    def _compute_order_line_count(self):
        """Compute number of order lines"""
        for order in self:
            order.order_line_count = len(order.order_lines)
    
    @api.depends('elapsed_time', 'estimated_time', 'priority', 'state')
    def _compute_display_color(self):
        for order in self:
            if order.priority == 'urgent':
                order.display_color = '#ff0000'  # Red
            elif order.elapsed_time > order.estimated_time:
                order.display_color = '#ffa500'  # Orange
            elif order.elapsed_time > order.estimated_time * 0.8:
                order.display_color = '#ffff00'  # Yellow
            else:
                order.display_color = '#00ff00'  # Green
    
    @api.depends('status')
    def _compute_status_display(self):
        """Compute display status for kanban grouping"""
        for order in self:
            if order.status == 'to_cook':
                order.status_display = "2_to_cook"
            elif order.status == 'ready':
                order.status_display = "3_ready"
            elif order.status == 'completed':
                order.status_display = "4_completed"
            else:
                order.status_display = "5_other"
    
    # Computed field for All section grouping
    kanban_group = fields.Selection([
        ('1_all', 'All'),
        ('2_to_cook', 'To Cook'),
        ('3_ready', 'Ready'),
        ('4_completed', 'Completed')
    ], string='Kanban Group', compute='_compute_kanban_group', store=False)
    
    @api.depends('status')
    def _compute_kanban_group(self):
        """Compute kanban group for display with All section"""
        for order in self:
            if order.status in ['to_cook', 'ready']:
                # Orders appear in both All and their specific status column
                order.kanban_group = '1_all'
            elif order.status == 'completed':
                order.kanban_group = '4_completed'
            else:
                order.kanban_group = '5_other'
    
    @api.model
    def get_kitchen_board_data(self):
        """Get all orders organized for kitchen board display"""
        # Get active orders (to_cook, ready, completed)
        orders = self.search([
            ('status', 'in', ['to_cook', 'ready', 'completed'])
        ], order='priority desc, create_date asc')
        
        result = []
        for order in orders:
            # Add order to All section if it's to_cook or ready
            if order.status in ['to_cook', 'ready']:
                all_order = order.copy_data()[0]
                all_order.update({
                    'id': f"all_{order.id}",
                    'display_section': 'all',
                    'sort_key': f"1_all_{order.id}"
                })
                result.append(all_order)
            
            # Add order to its specific status section
            status_order = order.copy_data()[0]
            status_order.update({
                'id': order.id,
                'display_section': order.status,
                'sort_key': f"{order.status}_{order.id}"
            })
            result.append(status_order)
        
        return result
    
    # Validation and Constraints
    @api.constrains('estimated_time')
    def _check_estimated_time(self):
        """Validate estimated preparation time"""
        for order in self:
            if order.estimated_time <= 0:
                raise ValidationError(_('Estimated preparation time must be greater than 0 minutes.'))
            if order.estimated_time > 480:  # 8 hours
                raise ValidationError(_('Estimated preparation time cannot exceed 8 hours.'))
    
    @api.constrains('priority')
    def _check_priority_logic(self):
        """Validate priority assignment logic"""
        for order in self:
            if order.priority == 'urgent' and not order.special_instructions:
                _logger.warning(f"Order {order.name} marked as urgent without special instructions")
    
    # Business Logic Methods
    def action_start_preparation(self):
        """Start order preparation"""
        self.ensure_one()
        if self.state != 'new':
            raise UserError(_('Only new orders can be started for preparation.'))
        
        self.write({
            'state': 'preparing',
            'cooking_time': fields.Datetime.now()
        })
        self._log_state_change('preparing')
        return True
    
    def action_mark_ready(self):
        """Mark order as ready for pickup"""
        self.ensure_one()
        if self.state not in ['new', 'preparing']:
            raise UserError(_('Only new or preparing orders can be marked as ready.'))
        
        self.write({
            'state': 'ready',
            'ready_time': fields.Datetime.now()
        })
        self._log_state_change('ready')
        return True
    
    def action_mark_served(self):
        """Mark order as served/completed"""
        self.ensure_one()
        if self.state != 'ready':
            raise UserError(_('Only ready orders can be marked as served.'))
        
        self.write({
            'state': 'served',
            'completed_time': fields.Datetime.now()
        })
        self._log_state_change('served')
        return True
    
    def action_cancel_order(self):
        """Cancel order"""
        self.ensure_one()
        if self.state in ['served', 'cancelled']:
            raise UserError(_('Cannot cancel served or already cancelled orders.'))
        
        self.write({
            'state': 'cancelled',
            'completed_time': fields.Datetime.now()
        })
        self._log_state_change('cancelled')
        return True

    def _log_state_change(self, new_state):
        """Log state changes for auditing"""
        self.ensure_one()
        state_names = dict(self._fields['state'].selection)
        message = _("Order state changed to: %s") % state_names.get(new_state, new_state)
        self.message_post(body=message, subtype_xmlid='mail.mt_note')
        _logger.info(f"Order {self.name} state changed to {new_state}")
    
    def auto_assign_displays(self):
        """Automatically assign order to appropriate displays"""
        self.ensure_one()
        
        # Find displays that should show this order
        domain = [
            ('is_active', '=', True),
            ('company_id', '=', self.company_id.id),
        ]
        
        # Filter by POS config if available
        if self.pos_config_id:
            domain.append(
                '|',
                ('pos_config_ids', '=', False),
                ('pos_config_ids', 'in', self.pos_config_id.ids)
            )
        
        # Filter by product categories
        product_categories = self.order_lines.mapped('product_id.categ_id')
        if product_categories:
            domain.append(
                '|',
                ('category_ids', '=', False),
                ('category_ids', 'in', product_categories.ids)
            )
        
        displays = self.env['kitchen.display'].search(domain)
        self.display_ids = [(6, 0, displays.ids)]
        
        return displays
    
    @api.model
    def create_from_pos_order(self, pos_order):
        """Create kitchen order from POS order"""
        if not pos_order:
            return False
        
        # Check if kitchen order already exists
        existing = self.search([('pos_order_id', '=', pos_order.id)])
        if existing:
            return existing
        
        # Prepare order data
        order_data = {
            'pos_order_id': pos_order.id,
            'customer_name': pos_order.partner_id.name if pos_order.partner_id else pos_order.name or 'Walk-in Customer',
            'table_number': getattr(pos_order, 'table_id', None) and pos_order.table_id.name or '',
            'special_instructions': getattr(pos_order, 'note', '') or '',
            'state': 'new',
            'priority': 'normal',
            'delivery_platform': 'pos',
        }
        
        # Create kitchen order
        kitchen_order = self.create(order_data)
        
        # Create order lines
        for pos_line in pos_order.lines:
            self.env['kitchen.order.line'].create({
                'order_id': kitchen_order.id,
                'product_id': pos_line.product_id.id,
                'quantity': pos_line.qty,
                'special_instructions': getattr(pos_line, 'note', '') or '',
            })
        
        # Auto-assign to displays
        kitchen_order.auto_assign_displays()
        
        return kitchen_order
    
    # Undo Actions for Kitchen Board
    def action_undo_preparation(self):
        """Undo preparation - move back to new status"""
        self.ensure_one()
        if self.state != 'preparing':
            raise UserError(_('Only preparing orders can be reset to new.'))
        
        self.write({
            'state': 'new',
            'cooking_time': False
        })
        self._log_state_change('new')
        return True
    
    def action_undo_ready(self):
        """Undo ready - move back to preparing status"""
        self.ensure_one()
        if self.state != 'ready':
            raise UserError(_('Only ready orders can be reset to preparing.'))
        
        self.write({
            'state': 'preparing',
            'ready_time': False
        })
        self._log_state_change('preparing')
        return True
    
    def action_undo_served(self):
        """Undo served - move back to ready status"""
        self.ensure_one()
        if self.state != 'served':
            raise UserError(_('Only served orders can be reset to ready.'))
        
        self.write({
            'state': 'ready',
            'completed_time': False
        })
        self._log_state_change('ready')
        return True


class KitchenOrderLine(models.Model):
    _name = 'kitchen.order.line'
    _description = 'Professional Kitchen Order Line Management'
    _order = 'sequence, id'
    _check_company_auto = True

    # Basic Information
    order_id = fields.Many2one(
        'kitchen.order', 
        string='Kitchen Order', 
        required=True, 
        ondelete='cascade',
        index=True
    )
    sequence = fields.Integer(
        string='Sequence', 
        default=10,
        help="Sequence for ordering lines"
    )
    
    # Product Information
    product_id = fields.Many2one(
        'product.product', 
        string='Product', 
        required=True,
        index=True
    )
    product_name = fields.Char(
        string='Product Name', 
        related='product_id.name', 
        store=True,
        readonly=True
    )
    product_code = fields.Char(
        string='Product Code',
        related='product_id.default_code',
        store=True,
        readonly=True
    )
    
    # Quantity and Pricing
    quantity = fields.Float(
        string='Quantity', 
        default=1.0,
        digits='Product Unit of Measure',
        required=True
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        related='product_id.uom_id',
        store=True,
        readonly=True
    )
    
    # Instructions and Notes
    special_instructions = fields.Text(
        string='Special Instructions',
        help="Special preparation instructions for this item"
    )
    internal_notes = fields.Text(
        string='Internal Notes',
        help="Internal notes for kitchen staff"
    )
    
    # Status and Workflow
    state = fields.Selection([
        ('new', 'New'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served')
    ], string='State', default='new', tracking=True)
    
    # Timing Information
    preparation_time = fields.Integer(
        string='Estimated Prep Time (minutes)',
        help="Estimated preparation time for this item"
    )
    actual_prep_time = fields.Float(
        string='Actual Prep Time (minutes)',
        readonly=True,
        help="Actual time taken to prepare this item"
    )
    
    # Category and Classification
    category_id = fields.Many2one(
        'product.category', 
        string='Category', 
        related='product_id.categ_id',
        store=True,
        readonly=True
    )
    
    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='order_id.company_id',
        store=True,
        readonly=True
    )
    
    # Constraints
    @api.constrains('quantity')
    def _check_quantity(self):
        """Validate quantity is positive"""
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_('Quantity must be greater than 0'))
    
    # Business Logic Methods
    def action_start_preparation(self):
        """Start preparation of this order line"""
        self.ensure_one()
        if self.state != 'new':
            raise UserError(_('Only new items can be started for preparation.'))
        
        self.write({'state': 'preparing'})
        return True
    
    def action_mark_ready(self):
        """Mark order line as ready"""
        self.ensure_one()
        if self.state not in ['new', 'preparing']:
            raise UserError(_('Only new or preparing items can be marked as ready.'))
        
        self.write({'state': 'ready'})
        return True
    
    def action_mark_served(self):
        """Mark order line as served"""
        self.ensure_one()
        if self.state != 'ready':
            raise UserError(_('Only ready items can be marked as served.'))
        
        self.write({'state': 'served'})
        return True
    
    @api.model
    def get_preparation_summary(self, category_id=None):
        """Get preparation summary for kitchen displays"""
        domain = [('state', 'in', ['new', 'preparing'])]
        if category_id:
            domain.append(('category_id', '=', category_id))
        
        lines = self.search(domain)
        
        summary = {}
        for line in lines:
            key = f"{line.product_name}"
            if key not in summary:
                summary[key] = {
                    'product_name': line.product_name,
                    'quantity': 0,
                    'special_instructions': [],
                    'preparation_time': line.preparation_time or 0,
                }
            
            summary[key]['quantity'] += line.quantity
            if line.special_instructions and line.special_instructions not in summary[key]['special_instructions']:
                summary[key]['special_instructions'].append(line.special_instructions)
        
        return list(summary.values())