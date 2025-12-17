# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    """Extend Product to add kitchen preparation time"""
    _inherit = 'product.product'

    kitchen_preparation_time = fields.Integer(
        string='Kitchen Prep Time (min)',
        default=0,
        help="Estimated time in minutes to prepare this item in the kitchen. "
             "Used for automatic order time estimation. 0 means use default estimation."
    )
    is_kitchen_item = fields.Boolean(
        string='Kitchen Item',
        default=False,
        help="Check this if the product needs kitchen preparation"
    )
    kitchen_category = fields.Selection([
        ('appetizer', 'Appetizer'),
        ('main', 'Main Course'),
        ('side', 'Side Dish'),
        ('dessert', 'Dessert'),
        ('beverage', 'Beverage'),
        ('other', 'Other')
    ], string='Kitchen Category', help="Category for kitchen organization")

    kitchen_station = fields.Selection([
        ('grill', 'Grill Station'),
        ('fryer', 'Fryer Station'),
        ('salad', 'Salad Station'),
        ('dessert', 'Dessert Station'),
        ('drinks', 'Drinks Station'),
        ('main', 'Main Kitchen'),
        ('other', 'Other')
    ], string='Kitchen Station', help="Which kitchen station prepares this item")


class ProductTemplate(models.Model):
    """Extend Product Template to add kitchen preparation time"""
    _inherit = 'product.template'

    kitchen_preparation_time = fields.Integer(
        string='Kitchen Prep Time (min)',
        default=0,
        help="Estimated time in minutes to prepare this item in the kitchen. "
             "Used for automatic order time estimation. 0 means use default estimation."
    )
    is_kitchen_item = fields.Boolean(
        string='Kitchen Item',
        default=False,
        help="Check this if the product needs kitchen preparation"
    )
    kitchen_category = fields.Selection([
        ('appetizer', 'Appetizer'),
        ('main', 'Main Course'),
        ('side', 'Side Dish'),
        ('dessert', 'Dessert'),
        ('beverage', 'Beverage'),
        ('other', 'Other')
    ], string='Kitchen Category', help="Category for kitchen organization")

    kitchen_station = fields.Selection([
        ('grill', 'Grill Station'),
        ('fryer', 'Fryer Station'),
        ('salad', 'Salad Station'),
        ('dessert', 'Dessert Station'),
        ('drinks', 'Drinks Station'),
        ('main', 'Main Kitchen'),
        ('other', 'Other')
    ], string='Kitchen Station', help="Which kitchen station prepares this item")
