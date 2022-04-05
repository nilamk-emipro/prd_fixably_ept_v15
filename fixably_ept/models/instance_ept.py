# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import requests
import json

class FixablyInstanceEpt(models.Model):
    _name = "fixably.instance.ept"
    _description = 'Fixably Instance'

    @api.model
    def _get_default_warehouse(self):
        """
        This method is used to set the default warehouse in an instance.
        """
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.fixably_company_id.id)], limit=1)
        return warehouse.id if warehouse else False

    name = fields.Char(size=120, required=True)
    fixably_warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', default=_get_default_warehouse,
                                           domain="[('company_id', '=',fixably_company_id)]",
                                           help="Selected Warehouse will be set in your orders", required=True)
    fixably_company_id = fields.Many2one('res.company', string='Company', required=True,
                                         default=lambda self: self.env.company)
    fixably_auto_create_product_if_not_found = fields.Boolean(string="Auto Create Product",
                                                              help='if checked than it auto create the product when'
                                                                   ' product is not found')
    fixably_is_use_default_sequence = fields.Boolean("Use Odoo Default Sequence?",
                                                     help="If checked,Then use default sequence of odoo while create pos "
                                                          "order.")
    fixably_order_prefix = fields.Char(size=10, string='Order Prefix',
                                       help="Enter your order prefix")
    apply_tax = fields.Selection(
        [("odoo_tax", "Odoo Default Tax Behaviour"), ("create_fixably_tax",
                                                      "Create new tax If Not Found")],
        copy=False, help=""" For Fixably Orders :- \n
                       1) Odoo Default Tax Behaviour - The Taxes will be set based on Odoo's
                                    default functional behaviour i.e. based on Odoo's Tax and Fiscal Position configurations. \n
                       2) Create New Tax If Not Found - System will search the tax data received 
                       from Fixably in Odoo, will create a new one if it fails in finding it.""")
    credit_tax_account_id = fields.Many2one('account.account', string='Credit Tax Account')
    debit_tax_account_id = fields.Many2one('account.account', string='Debit Tax Account')
    last_order_import_date = fields.Datetime(string="Last Date Of Order Import",
                                             help="Last date of sync orders from Fixably to Odoo")
    fixably_pricelist_id = fields.Many2one('product.pricelist', string='Pricelist',
                                           help="During order sync, prices will be Imported/Exported using this Pricelist.")
    fixably_api_key = fields.Char("API Key", required=True)
    fixably_url = fields.Char("URL", required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [('unique_url', 'unique(fixably_url)',
                         "Instance already exists for given url. URL must be Unique for the instance!"),
                        ('unique_api_key', 'unique(fixably_api_key)',
                         "Instance already exists for given Api Key. Api Key must be Unique for the instance!")]

    def test_connection(self):
        url = "https://albion.fixably.com"
        api_url = "/api/v3/stores"
        headers = {'Authorization': 'pk_LSw16e3iVQB928moz53tPtViyo1vfOv078yYvzGyhxPI9Cp',
                   'Content-Type': 'application/json'}
        response = requests.get(url=url + api_url, headers=headers)
        return response