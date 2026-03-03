# Copyright 2026 Robotika
# License AGPL-3.0

from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _generate_signup_values(self, provider, validation, params):
        """Use email as login for Nekazari Keycloak provider.

        energy_communities overrides this to use user_id (sub/UUID) as login,
        which breaks signup with its constraints (vat=login, country=ES).
        For the Nekazari provider we restore standard behavior: login=email.
        """
        oauth_provider = self.env["auth.oauth.provider"].browse(provider)
        if oauth_provider.name and "nekazari" in oauth_provider.name.lower():
            # Standard behavior: login = email
            oauth_uid = validation["user_id"]
            email = validation.get(
                "email", "provider_%s_user_%s" % (provider, oauth_uid)
            )
            name = validation.get("name", email)
            return {
                "name": name,
                "login": email,
                "email": email,
                "oauth_provider_id": provider,
                "oauth_uid": oauth_uid,
                "oauth_access_token": params["access_token"],
                "active": True,
            }
        return super()._generate_signup_values(provider, validation, params)
