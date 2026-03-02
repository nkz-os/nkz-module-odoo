{
    "name": "Nekazari Web Theme",
    "version": "16.0.1.0.0",
    "category": "Website/Theme",
    "summary": "Nekazari platform branding for Odoo",
    "description": "Replaces Odoo default branding with Nekazari identity: green colour scheme, logo on login page, custom favicon and browser tab title.",
    "author": "Robotika",
    "website": "https://nekazari.robotika.cloud",
    "license": "AGPL-3",
    "depends": ["web"],
    "data": [
        "views/webclient_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "nekazari_web_theme/static/src/css/nekazari_theme.css",
        ],
        "web.assets_frontend": [
            "nekazari_web_theme/static/src/css/nekazari_theme.css",
        ],
    },
    "auto_install": False,
    "installable": True,
    "application": False,
}
