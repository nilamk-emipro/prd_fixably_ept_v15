{
    # App information
    'name': 'Fixably Odoo Connector',
    'version': '15.0.4.0.1',
    'category': 'Sales',
    'summary': 'Fixably Odoo Connector helps you in integrating and managing your data with odoo',
    'license': 'OPL-1',

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com/',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    # Dependencies
    'depends': ['common_connector_library'],

    # Views
    'init_xml': [],
    'data': [
        'security/ir.model.access.csv',
        'wizard/instance_config_wizard_view.xml',
        'wizard/fixably_res_config_view.xml',
        'view/instance_view.xml',
        'view/store_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 379.00,
    'currency': 'EUR',
}
