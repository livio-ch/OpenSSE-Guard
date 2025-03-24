import json
import logging
from urllib.request import urlopen
from authlib.oauth2.rfc7523 import JWTBearerTokenValidator
from authlib.jose.rfc7517.jwk import JsonWebKey

class Auth0JWTBearerTokenValidator(JWTBearerTokenValidator):
    def __init__(self, domain, audience):
        issuer = f"https://{domain}/"
        try:
            logging.error(f"{issuer}.well-known/jwks.json")
            jsonurl = urlopen(f"{issuer}.well-known/jwks.json")
            logging.error(f"JSON URL: {jsonurl}")
            public_key = JsonWebKey.import_key_set(
                json.loads(jsonurl.read())
            )
            super(Auth0JWTBearerTokenValidator, self).__init__(public_key)
            self.claims_options = {
                "exp": {"essential": True},
                "aud": {"essential": True, "value": audience},
                "iss": {"essential": True, "value": issuer},
            }
        except Exception as e:
            logging.error(f"Error in token validation: {str(e)}")
            raise
