from . import models
from . import controllers
from . import wizard

import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """Pre-initialization hook for Kitchen Display System Pro"""
    _logger.info("Kitchen Display System Pro: Starting pre-initialization...")
    # Add any pre-installation checks here
    return True


def post_init_hook(env):
    """Post-initialization hook for Kitchen Display System Pro"""
    _logger.info("Kitchen Display System Pro by Azad Karipody Hamza (Digicyfr Polska): Starting post-initialization...")

    # Create default kitchen display if none exists
    existing_displays = env['kitchen.display'].search([])
    if not existing_displays:
        default_display = env['kitchen.display'].create({
            'name': 'Main Kitchen Display',
            'display_type': 'all',
            'is_active': True,
            'location': 'Main Kitchen',
            'auto_refresh_interval': 10,
            'max_orders_display': 50,
            'show_customer_name': True,
            'show_order_time': True,
            'show_special_instructions': True,
            'show_table_number': True,
            'sound_enabled': True,
            'sound_new_order': 'chime',
        })
        _logger.info(f"Created default kitchen display: {default_display.name}")

    _logger.info("Kitchen Display System Pro: Post-initialization completed successfully")
    return True


def uninstall_hook(env):
    """Uninstallation hook for Kitchen Display System Pro"""
    _logger.info("Kitchen Display System Pro: Starting uninstallation cleanup...")
    
    # Clean up any external resources if needed
    # Note: Odoo automatically handles database cleanup
    
    _logger.info("Kitchen Display System Pro: Uninstallation completed successfully")
    return True