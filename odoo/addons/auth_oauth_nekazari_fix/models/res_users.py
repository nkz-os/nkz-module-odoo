# Copyright 2026 Robotika
# License AGPL-3.0

import logging

from odoo import models
from odoo.exceptions import AccessDenied, UserError

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.auth_signup.models.res_users import SignupError
except ImportError:
    SignupError = Exception


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

    def constrains_user_login(self):
        """Skip energy_communities vat/country write for OAuth users (no Spanish VAT)."""
        for record in self:
            if record.oauth_uid:
                return  # OAuth users: skip partner vat/country_id write
        return super().constrains_user_login()

    def _auth_oauth_signin(self, provider, validation, params):
        """Log real exception when OAuth signup fails for Nekazari."""
        try:
            return super()._auth_oauth_signin(provider, validation, params)
        except (AccessDenied, SignupError, UserError) as e:
            oauth_provider = self.env["auth.oauth.provider"].browse(provider)
            if oauth_provider.name and "nekazari" in oauth_provider.name.lower():
                _logger.exception(
                    "[Nekazari OAuth] signup/signin failed: %s (provider=%s user_id=%s)",
                    e,
                    provider,
                    validation.get("user_id"),
                )
            raise
