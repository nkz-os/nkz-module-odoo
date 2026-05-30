#!/usr/bin/env python3
"""Patch energy_communities._generate_signup_values to respect Nekazari provider.

energy_communities overrides _generate_signup_values to set login=UUID (user_id),
which breaks Nekazari SSO (login must be email for OAuth compatibility).
This patch makes it use email when the OAuth provider name contains 'nekazari'.
"""
path = '/opt/odoo/custom-addons/energy_communities/models/res_users.py'
with open(path) as f:
    content = f.read()

old = '        values["login"] = validation["user_id"]'
new = '''        oauth_provider = self.env["auth.oauth.provider"].browse(provider)
        if oauth_provider.name and "nekazari" in oauth_provider.name.lower():
            return super(ResUsers, self)._generate_signup_values(provider, validation, params)
        values["login"] = validation["user_id"]'''

assert old in content, 'Could not find target line in energy_communities/res_users.py'
content = content.replace(old, new, 1)
with open(path, 'w') as f:
    f.write(content)
print('Patched energy_communities._generate_signup_values for Nekazari SSO')
