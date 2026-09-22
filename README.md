# Kitchen Display for Odoo 17

An Odoo 17 module prototype for configuring kitchen display stations and moving restaurant orders through `new`, `preparing`, `ready`, `served`, and `cancelled` states.

This repository is separate from any Android or WooCommerce application. It does not currently demonstrate compatibility with WooCommerce, external delivery platforms, or standalone Android devices.

## Current scope

The repository contains:

- Odoo models for kitchen displays, kitchen orders, order lines, priorities, timing, and station assignment;
- authenticated JSON routes for reading display data, creating kitchen orders, and updating order status;
- Odoo views, access-control definitions, demo data, and a full-screen display template;
- configurable display types, POS configurations, product-category filters, refresh intervals, warning thresholds, colours, sounds, and layouts;
- basic order-count and preparation-time calculations.

The browser-side JavaScript is still a scaffold: it installs event listeners and a refresh timer, but its RPC calls are not implemented. Treat the repository as source for technical review and further development, not as evidence of a completed production deployment.

## Requirements

- Odoo 17
- Point of Sale (`point_of_sale`)
- Restaurant POS (`pos_restaurant`)
- the additional Odoo modules listed in [`__manifest__.py`](./__manifest__.py)

## Installation for development

1. Clone or copy this repository into an Odoo addons directory named `kitchen_display`.
2. Add that directory to the Odoo addons path.
3. Restart Odoo and update the Apps list.
4. Install **Kitchen Display System Pro** from Apps.
5. Review access groups and test the module in a non-production database before using real operational data.

The module declares pre-installation, post-installation, and uninstall hooks. Review those hooks and your Odoo logs during installation.

## Main routes

All routes require an authenticated Odoo user:

| Route | Purpose |
| --- | --- |
| `POST /kitchen_display/orders` | Read orders for a configured display |
| `POST /kitchen_display/update_order_status` | Move an order through an allowed status action |
| `POST /kitchen_display/create_order` | Create a kitchen-order record from validated input |
| `GET /kitchen_display/display/<display_id>` | Render one configured display |
| `GET /kitchen_display/fullscreen` | Render the first active display or a newly created default |

## Verification status

No public compatibility matrix, automated test suite, performance benchmark, customer-volume claim, or production-support SLA is included in this repository. Validate the module against the exact Odoo edition, installed modules, POS configuration, browser, hardware, and operational workflow you intend to use.

## Security and data

The routes use `auth='user'` and invoke Odoo access-right checks. A production review should also verify record rules, multi-company boundaries, CSRF behaviour, input validation, logging, and whether customer or order information should be visible on each station.

Do not commit database credentials, API keys, production exports, or customer data.

## License

The repository is licensed under the [Odoo Proprietary License v1.0](./LICENSE). It is source-available under those license terms; it is not an open-source GPL project.

## Maintainer

CYFR Sp. z o.o., operating under the Digicyfr brand

[www.digicyfr.com](https://www.digicyfr.com) · [info@digicyfr.com](mailto:info@digicyfr.com)

For implementation enquiries, describe your Odoo version, edition, installed POS modules, number of locations and stations, and the order sources that must be supported.
