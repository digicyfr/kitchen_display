# Kitchen Display System Pro - Complete Workflow

## Table of Contents
1. [System Overview](#system-overview)
2. [Order Lifecycle](#order-lifecycle)
3. [Automatic Intelligence Features](#automatic-intelligence-features)
4. [User Workflows](#user-workflows)
5. [Technical Architecture](#technical-architecture)
6. [Configuration Guide](#configuration-guide)

---

## System Overview

The Kitchen Display System Pro automatically transforms POS orders into visual kitchen orders with intelligent time estimation and priority management.

### Key Components
- **POS Integration**: Automatic order creation from Point of Sale
- **Smart Estimation**: Calculates prep time based on order contents
- **Priority Management**: Auto-assigns and escalates order priorities
- **Real-time Display**: Kanban board for kitchen staff
- **Order Tracking**: Complete audit trail and analytics

---

## Order Lifecycle

### 1. Order Creation (Automatic)

```
POS Order Created
      ↓
Kitchen Order Auto-Generated
      ↓
[Calculate Estimated Time]
      ↓
[Assign Smart Priority]
      ↓
Display in Kitchen Board
```

**What Happens:**
- Customer places order through POS
- System automatically creates kitchen order
- Estimated time calculated based on items
- Priority assigned based on order characteristics
- Order appears on kitchen displays

**Technical Details:**
- Trigger: `pos.order` create method
- Handler: `kitchen.order.create_from_pos_order()`
- Location: `models/pos_order.py` (lines 18-39)

---

### 2. Order States Flow

```
┌─────────┐
│   NEW   │ ← Order just created
└────┬────┘
     ↓
┌─────────┐
│PREPARING│ ← Kitchen starts cooking
└────┬────┘
     ↓
┌─────────┐
│  READY  │ ← Food ready for pickup
└────┬────┘
     ↓
┌─────────┐
│ SERVED  │ ← Delivered to customer
└─────────┘
```

**State Transitions:**
- **NEW → PREPARING**: Staff clicks "Start Preparation" or order is auto-started
- **PREPARING → READY**: Staff clicks "Mark Ready" button
- **READY → SERVED**: Staff clicks "Served" button
- **Any → CANCELLED**: Manager cancels order

---

## Automatic Intelligence Features

### 1. Smart Estimated Time Calculation

**Formula:**
```
Estimated Time = Base Time (5 min) + Sum of Item Times

Item Time = {
    Product Prep Time × Quantity Factor     (if set on product)
    OR
    3 minutes × Quantity Factor             (default)
}

Quantity Factor = 1 + (Quantity - 1) × 0.5  (diminishing returns)
```

**Examples:**

| Order Contents | Calculation | Estimated Time |
|---------------|-------------|----------------|
| 1 Pizza | 5 + (3 × 1) | **8 minutes** |
| 3 Pizzas | 5 + (3 × 2) | **11 minutes** |
| 2 Pizzas, 1 Salad | 5 + (3 × 1.5) + (3 × 1) | **13 minutes** |
| 10 Burgers | 5 + (3 × 5.5) | **22 minutes** |

**Code Location:** `models/kitchen_order.py` (lines 248-273)

---

### 2. Smart Priority Assignment

**Priority Rules:**

| Priority | Conditions |
|----------|-----------|
| **URGENT** | • Auto-escalated (see below)<br>• Manually set by manager |
| **HIGH** | • Special instructions > 10 characters<br>• Large orders (>10 items)<br>• Delivery platform orders |
| **NORMAL** | • Standard POS orders<br>• Simple requirements<br>• 1-10 items |
| **LOW** | • Manually set by manager<br>• Test/training orders |

**Code Location:** `models/kitchen_order.py` (lines 275-297)

---

### 3. Automatic Priority Escalation

**Escalation Rules:**

```
Time Elapsed vs Estimated Time
      ↓
< 90% of estimated
      → Priority stays same

90-149% of estimated
      → Normal → HIGH

≥ 150% of estimated
      → HIGH → URGENT
```

**Example:**
- Order estimated: 20 minutes
- At 18 minutes (90%): Normal → **HIGH**
- At 30 minutes (150%): High → **URGENT**

**Frequency:** Runs every 2 minutes automatically

**Code Location:**
- Method: `models/kitchen_order.py` (lines 299-312)
- Cron: `data/kitchen_display_data.xml` (lines 65-76)

---

## User Workflows

### Kitchen Staff Workflow

#### A. Viewing Orders (Kitchen Board)

**Navigation:** Kitchen Display → Kitchen Board

**Display:**
```
┌──────────────┬──────────────┬──────────────┐
│     NEW      │  PREPARING   │    READY     │
├──────────────┼──────────────┼──────────────┤
│ • KO0001     │ • KO0002     │ • KO0003     │
│   Table 5    │   Table 3    │   Table 1    │
│   8 min      │   15 min     │   Ready!     │
│   2x Pizza   │   3x Burger  │   1x Salad   │
│   [READY]    │   [READY]    │   [SERVED]   │
└──────────────┴──────────────┴──────────────┘
```

**Actions:**
1. View incoming orders in **NEW** column
2. Click **READY** button when food is prepared
3. Move to **READY** column, waiter sees it
4. Waiter clicks **SERVED** after delivery

---

#### B. Managing Orders (Order List)

**Navigation:** Kitchen Display → Operations → Order List

**Features:**
- **Inline Editing**: Click any field to edit directly
- **Bulk Actions**: Select multiple orders
- **Filtering**: Filter by state, priority, table
- **Sorting**: Click column headers to sort

**Editable Fields:**
- Customer Name
- Table Number
- Priority (dropdown)
- Estimated Time (minutes)
- Special Instructions

**Read-only Fields:**
- Order Number
- State (use buttons)
- Elapsed Time (auto-calculated)
- Order Time (system timestamp)

---

### Manager Workflow

#### A. Monitor Performance

**View:** Kitchen Display → Analytics (if available)

**Metrics:**
- Average preparation time
- Orders completed per hour
- Priority escalation frequency
- Kitchen efficiency score

---

#### B. Manual Override

**When to Override:**
- VIP customer arrives
- Delivery driver waiting
- Kitchen capacity issues
- Special circumstances

**How to Override:**
1. Go to Order List
2. Click Priority field
3. Change to HIGH or URGENT
4. Click Estimated Time if adjustment needed

---

#### C. Configure Displays

**Navigation:** Kitchen Display → Configuration → Display Settings

**Settings:**
- Display Type (All/Station-specific)
- Auto-refresh interval
- Visual/sound alerts
- Product categories to show
- Associated POS systems

---

## Technical Architecture

### Database Schema

#### Kitchen Order Model
```python
kitchen.order
├── name (Char) - Order number (KO####)
├── state (Selection) - new/preparing/ready/served/cancelled
├── priority (Selection) - low/normal/high/urgent
├── customer_name (Char)
├── table_number (Char)
├── order_time (Datetime) - When order created
├── estimated_time (Integer) - Calculated prep time
├── elapsed_time (Integer) - Computed from order_time
├── pos_order_id (Many2one) → pos.order
└── order_lines (One2many) → kitchen.order.line
```

#### Kitchen Order Line Model
```python
kitchen.order.line
├── order_id (Many2one) → kitchen.order
├── product_id (Many2one) → product.product
├── product_name (Char) - Stored for reference
├── quantity (Float)
├── preparation_time (Integer) - Minutes per item
├── state (Selection) - new/preparing/ready/served
└── special_instructions (Text)
```

---

### Integration Points

#### 1. POS Integration
**File:** `models/pos_order.py`

```python
class PosOrder(models.Model):
    _inherit = 'pos.order'

    def create(self, vals_list):
        # Create POS orders
        orders = super().create(vals_list)

        # Auto-create kitchen orders
        for order in orders:
            if order.lines:
                kitchen_order = self.env['kitchen.order'].create_from_pos_order(order)

        return orders
```

**Trigger:** When POS order is validated/paid

---

#### 2. Scheduled Actions

**Auto-escalate Priorities:**
- **Frequency:** Every 2 minutes
- **Code:** `model.search([('state', 'in', ['new', 'preparing'])])._auto_escalate_priority()`
- **Purpose:** Check elapsed time and escalate priorities

---

### View Architecture

```
Kitchen Display Module
│
├── Kitchen Board (Kanban View)
│   └── Grouped by: state
│       ├── Color-coded by priority
│       ├── Shows: elapsed time, items, buttons
│       └── Real-time updates
│
├── Order List (Tree View - Editable)
│   └── Inline editing enabled
│       ├── Editable: priority, estimated_time, customer, table
│       ├── Action buttons: Mark Ready, Served
│       └── Colored rows by state
│
└── Order Form (Detail View)
    └── Full order details
        ├── Header: Status bar, action buttons
        ├── Order Info: customer, table, timing
        ├── Special Instructions
        └── Order Lines (editable tree)
```

---

## Configuration Guide

### Initial Setup

#### 1. Install Module
```bash
# Update apps list
# Navigate to Apps → Update Apps List
# Search "Kitchen Display System Pro"
# Click Install
```

#### 2. Configure First Display
1. Go to: Kitchen Display → Configuration → Display Settings
2. Click: New
3. Set:
   - Name: "Main Kitchen"
   - Location: "Main Kitchen"
   - Display Type: "All Orders Dashboard"
   - Auto-refresh: 10 seconds
   - Sound alerts: Enabled

#### 3. Assign Security Groups
Navigate to: Settings → Users & Companies → Users

**Kitchen Staff:**
- Group: Kitchen Display / Kitchen Staff
- Can: View orders, change states

**Kitchen Manager:**
- Group: Kitchen Display / Kitchen Manager
- Can: Configure displays, override priorities

---

### Product Configuration (Optional)

**Set Preparation Times on Products:**

1. Go to: Inventory → Products → Products
2. Open any product
3. Go to: Sales tab (or create custom field)
4. Set: Preparation Time (minutes)

**Example:**
- Pizza: 12 minutes
- Salad: 5 minutes
- Steak: 20 minutes
- Coffee: 3 minutes

**Result:** Orders automatically calculate accurate estimated times

---

### Advanced Configuration

#### Custom Priority Rules

Edit: `models/kitchen_order.py` → `_calculate_smart_priority()`

```python
def _calculate_smart_priority(self):
    priority = 'normal'

    # Add custom rules
    if self.customer_name and 'VIP' in self.customer_name.upper():
        priority = 'urgent'

    if self.table_number and int(self.table_number) > 20:
        priority = 'high'  # Outdoor tables

    return priority
```

#### Adjust Escalation Timing

Edit: `data/kitchen_display_data.xml` → cron interval

```xml
<field name="interval_number">5</field>  <!-- Change from 2 to 5 minutes -->
<field name="interval_type">minutes</field>
```

#### Modify Time Calculation

Edit: `models/kitchen_order.py` → `_calculate_estimated_time()`

```python
# Change base time
base_time = 10  # Increased from 5 minutes

# Change default item time
item_time = 5 * (1 + (line.quantity - 1) * 0.5)  # Increased from 3
```

---

## Troubleshooting

### Orders Not Appearing

**Check:**
1. POS order has lines (products)
2. Kitchen display is active
3. User has Kitchen Staff access
4. Browser cache cleared

**Solution:**
```python
# Manually create kitchen order
kitchen_order = self.env['kitchen.order'].create_from_pos_order(pos_order)
```

---

### Priority Not Escalating

**Check:**
1. Cron job is active: Settings → Technical → Scheduled Actions
2. Search: "Auto-escalate Order Priorities"
3. Verify: Next Execution Date is set

**Manual Escalation:**
```python
# Run manually
self.env['kitchen.order'].search([('state', 'in', ['new', 'preparing'])])._auto_escalate_priority()
```

---

### Estimated Time Inaccurate

**Solutions:**
1. Set preparation times on products
2. Adjust calculation formula (see Advanced Configuration)
3. Monitor actual times and tune base_time

**Track Actual Times:**
- Check: `actual_preparation_time` field on completed orders
- Compare with `estimated_time`
- Adjust formula accordingly

---

## Performance Optimization

### For Large Restaurants (>100 orders/day)

#### 1. Index Database Fields
```sql
CREATE INDEX idx_kitchen_order_state ON kitchen_order(state);
CREATE INDEX idx_kitchen_order_priority ON kitchen_order(priority);
CREATE INDEX idx_kitchen_order_time ON kitchen_order(order_time);
```

#### 2. Archive Old Orders
```python
# Archive orders older than 7 days
old_orders = self.env['kitchen.order'].search([
    ('state', 'in', ['served', 'cancelled']),
    ('order_time', '<', fields.Datetime.now() - timedelta(days=7))
])
old_orders.write({'active': False})
```

#### 3. Adjust Cron Frequency
- High volume: 1 minute
- Medium volume: 2 minutes (default)
- Low volume: 5 minutes

---

## API Reference

### Create Kitchen Order Programmatically

```python
kitchen_order = self.env['kitchen.order'].create({
    'customer_name': 'John Doe',
    'table_number': '5',
    'special_instructions': 'No onions',
    'priority': 'normal',
})

# Add order lines
self.env['kitchen.order.line'].create({
    'order_id': kitchen_order.id,
    'product_id': product.id,
    'quantity': 2,
})

# Calculate estimated time
estimated = kitchen_order._calculate_estimated_time()
kitchen_order.estimated_time = estimated
```

---

### Change Order State

```python
# Start preparation
order.action_start_preparation()

# Mark ready
order.action_mark_ready()

# Mark served
order.action_mark_served()

# Cancel order
order.action_cancel_order()

# Undo actions
order.action_undo_ready()
order.action_undo_served()
```

---

### Query Orders

```python
# Get all active orders
active_orders = self.env['kitchen.order'].search([
    ('state', 'in', ['new', 'preparing', 'ready'])
])

# Get urgent orders
urgent_orders = self.env['kitchen.order'].search([
    ('priority', '=', 'urgent'),
    ('state', '!=', 'served')
])

# Get overdue orders
overdue = self.env['kitchen.order'].search([
    ('elapsed_time', '>', 'estimated_time'),
    ('state', 'in', ['new', 'preparing'])
])
```

---

## Support & Customization

**Developer:** Azad Karipody Hamza
**Company:** Digicyfr Polska
**Email:** info@digicyfr.com
**Phone:** +48 695 021 633
**Website:** https://www.digicyfr.com

**For Custom Features:**
- Advanced analytics and reporting
- Integration with delivery platforms
- Custom display layouts
- Multi-kitchen coordination
- Customer-facing displays

---

## Changelog

### Version 1.0 (Current)
- ✅ Automatic POS integration
- ✅ Smart estimated time calculation
- ✅ Intelligent priority assignment
- ✅ Automatic priority escalation
- ✅ Editable order list
- ✅ Real-time kanban board
- ✅ Complete order lifecycle management

### Planned Features
- 📊 Advanced analytics dashboard
- 🔔 Mobile app notifications
- 📱 Customer status tracking
- 🌐 Multi-language interface
- 🎯 Kitchen capacity management
- 📈 Performance benchmarking

---

**Last Updated:** December 2025
**Module Version:** 1.0
**Odoo Version:** 17.0
