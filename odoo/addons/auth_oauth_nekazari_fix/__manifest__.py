{
    "name": "Auth OAuth Nekazari Fix",
    "version": "16.0.1.0.0",
    "category": "Technical",
    "summary": "Fix OAuth signup for Nekazari Keycloak provider",
    "description": """
Restores email-as-login for Nekazari Keycloak OAuth provider.
energy_communities overrides _generate_signup_values to use user_id (UUID) as login,
which can break signup with its constraints. This module ensures Nekazari provider
uses email for login, matching standard OAuth behavior.
""",
    "author": "Robotika",
    "license": "AGPL-3",
    "depends": ["auth_oauth", "energy_communities"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
