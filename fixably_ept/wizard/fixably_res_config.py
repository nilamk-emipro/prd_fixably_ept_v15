# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json


class FixablyInstanceConfig(models.TransientModel):
    _name = "res.config.fixably.instance"
    _description = "Fixably Instance Configuration"

    name = fields.Char(help="Name to identify the Fixably")
    fixably_api_key = fields.Char("API Key", required=True, help="Fixably API Key.")
    fixably_url = fields.Char("URL", required=True,
                              help="Add your fixably store URL, for example, https://my-fixably.myfixably.com")
    fixably_company_id = fields.Many2one("res.company", string="Instance Company",
                                         help="Orders will be generated of this company.")

    def create_pricelist(self):
        """
        This method creates pricelist base on current currency .
        """
        pricelist_obj = self.env["product.pricelist"]
        currency_id = self.env.user.currency_id

        price_list_name = self.name + " " + "PriceList"
        pricelist = pricelist_obj.search([("name", "=", price_list_name),
                                          ("currency_id", "=", currency_id.id),
                                          ("company_id", "=", self.fixably_company_id.id)],
                                         limit=1)
        if not pricelist:
            pricelist = pricelist_obj.create({"name": price_list_name,
                                              "currency_id": currency_id.id,
                                              "company_id": self.fixably_company_id.id})

        return pricelist.id

    def prepare_val_for_instance_creation(self):
        """ This method is used to prepare a vals for instance creation.
            @return: vals
        """
        warehouse_obj = self.env['stock.warehouse']
        warehouse = warehouse_obj.search([('company_id', '=', self.fixably_company_id.id)], limit=1, order='id')
        pricelist_id = self.create_pricelist()

        vals = {
            "name": self.name,
            "fixably_api_key": self.fixably_api_key,
            "fixably_url": self.fixably_url,
            "fixably_warehouse_id": warehouse.id,
            "fixably_company_id": self.fixably_company_id.id,
            "fixably_pricelist_id": pricelist_id or False,
            "apply_tax": "create_fixably_tax",
        }
        return vals

    def get_store_value(self, vals):
        """
            this method use for getting store data from the api response
            return : response as store details
        """
        headers = {'Authorization': 'pk_LSw16e3iVQB928moz53tPtViyo1vfOv078yYvzGyhxPI9Cp',
                   'Content-Type': 'application/json'}
        response = requests.get(url=vals['href'], headers=headers)
        return response

    def create_store(self, vals):
        """
        this method use to create the store
        """
        store_obj = self.env['fixably.store.ept']
        for val in vals:
            store_obj.create(val)
        return True

    def prepare_val_store_creation(self, vals, instance):
        """
        this method use to prepare vals for store creation.
        """
        store_vals = []
        for val in vals['items']:
            res = self.get_store_value(val)
            if res.status_code == 200:
                details = json.loads(res.content.decode())
                store_vals.append({
                    "name": details['name'],
                    "fixably_instance_id": instance.id,
                    "fixably_store_id": details['id'],
                    "fixably_team_id": details['team_id'] if "team_id" in details else None,
                    "fixably_pos_store_id": details['pos_store_id'] if "pos_store_id" in details else None
                })
            else:
                raise UserError(_("Some Error in getting store Details please try again"))
        self.create_store(store_vals)
        return True

    def fixably_test_connection(self):
        """This method used to verify whether Odoo is capable of connecting with fixably or not.
            @return : Action of type reload.
        """
        instance_obj = self.env["fixably.instance.ept"]
        instance_id = instance_obj.with_context(active_test=False).search(
            ["|", ("fixably_api_key", "=", self.fixably_api_key),
             ("fixably_url", "=", self.fixably_url)], limit=1)
        if instance_id:
            raise UserError(_(
                "An instance already exists for the given details \nfixably API key : '%s' \nfixably URL : '%s'" % (
                    self.fixably_api_key, self.fixably_url)))

        vals = self.prepare_val_for_instance_creation()
        fixably_instance = instance_obj.create(vals)
        check_connection = instance_obj.test_connection()
        if check_connection.status_code != 200:
            raise UserError(_(
                "Some Error in Connection please try again"))
        else:
            self.prepare_val_store_creation(json.loads(check_connection.content.decode()), fixably_instance)

        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    fixably_instance_id = fields.Many2one("fixably.instance.ept", "Fixably Instance")
    fixably_company_id = fields.Many2one("res.company", string="Fixably Instance Company",
                                         help="Orders and Invoices will be generated of this company.")
    fixably_warehouse_id = fields.Many2one("stock.warehouse", string="Fixably Warehouse",
                                           domain="[('company_id', '=',fixably_company_id)]")
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
                           from fixably in Odoo, will create a new one if it fails in finding it.""")
    credit_tax_account_id = fields.Many2one('account.account', string='Credit Tax Account')
    debit_tax_account_id = fields.Many2one('account.account', string='Debit Tax Account')
    last_order_import_date = fields.Datetime(string="Last Date Of Order Import",
                                             help="Last date of sync orders from Fixably to Odoo")
    fixably_pricelist_id = fields.Many2one('product.pricelist', string='Pricelist',
                                           help="1.During product sync operation, prices will be Imported/Exported "
                                                "using this Pricelist.\n"
                                                "2.During order sync operation, this pricelist "
                                                "will be set in the order if the order currency from store and the "
                                                "currency from the pricelist set here, matches.")

    @api.onchange("fixably_instance_id")
    def onchange_fixably_instance_id(self):
        instance = self.fixably_instance_id or False
        if instance:
            self.fixably_company_id = instance.fixably_company_id and instance.fixably_company_id.id or False
            self.fixably_warehouse_id = instance.fixably_warehouse_id and instance.fixably_warehouse_id.id or False
            self.fixably_pricelist_id = instance.fixably_pricelist_id and instance.fixably_pricelist_id.id or False
            self.fixably_order_prefix = instance.fixably_order_prefix
            self.fixably_is_use_default_sequence = instance.fixably_is_use_default_sequence
            self.debit_tax_account_id = instance.debit_tax_account_id and \
                                        instance.debit_tax_account_id.id or False
            self.credit_tax_account_id = instance.credit_tax_account_id and \
                                         instance.credit_tax_account_id.id or False
            self.last_order_import_date = instance.last_order_import_date or False
            self.apply_tax = instance.apply_tax
