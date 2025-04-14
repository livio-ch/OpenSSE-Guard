import requests
import logging
import cache
import os
from .threat_api import ThreatIntelAPI

class OTXAPI(ThreatIntelAPI):
    def __init__(self):
        self.api_key = os.getenv('OTX_API_KEY')
        self.url_domain = 'https://otx.alienvault.com/api/v1/indicators/domain/{}/general'
        self.url_hash = 'https://otx.alienvault.com/api/v1/indicators/file/{}/analysis'

    def check_domain(self, domain):
        myurl = self.url_domain.format(domain)
        response = cache.get_cache(myurl)
        if not response:
            headers = {'X-OTX-API-KEY': self.api_key}
            res = requests.get(myurl, headers=headers)
            if res.status_code != 200:
                logging.error(f"OTX API failed: {res.status_code}")
                return None
            response = res.json()
            cache.set_cache(myurl, response)
            logging.error(f"SET CACHE DONE")
        logging.info(f"response data json transform")
        data = response

        # Check if pulse_info count is 0
        pulse_info = data.get('pulse_info', {})
        pulse_count = pulse_info.get('count', 0)
        logging.info(f"Do pulse count")

        if pulse_count == 0:
            logging.info(f"Domain {domain} has pulse count 0, not blocking.")
            return None  # No pulses, so don't block

        # Extract the validation list that contains information about whitelist
        validations = data.get('validation', [])

        # Check if any of the validation sources are "whitelist"
        for validation in validations:
            if validation.get('source') == 'whitelist':
                logging.info(f"Domain {domain} is whitelisted. Not blocking.")
                return None  # Domain is whitelisted, so we don't block it

    # If it's not whitelisted, check for other IOC information (verdict)
        facts = data.get('facts', {})
        verdict = facts.get('verdict', 'Unknown')

    # Extract other relevant details from 'facts'
        ip_addresses = facts.get('current_ip_addresses', [])
        current_asns = facts.get('current_asns', [])
        current_nameservers = facts.get('current_nameservers', [])
        ssl_certificates = facts.get('ssl_certificates', [])

    # Logging the extracted information in a readable format
        logging.info(f"OTX Verdict for {domain}: {verdict}")
        logging.info(f"OTX IP Addresses for {domain}: {json.dumps(ip_addresses, indent=4)}")
        logging.info(f"OTX Current ASNs for {domain}: {json.dumps(current_asns, indent=4)}")
        logging.info(f"OTX Current Nameservers for {domain}: {json.dumps(current_nameservers, indent=4)}")
        logging.info(f"OTX SSL Certificates for {domain}: {json.dumps(ssl_certificates, indent=4)}")

    # Return the IOC info (but only if it's not whitelisted)
        return {
            'verdict': verdict,
            'ip_addresses': ip_addresses,
            'current_asns': current_asns,
            'current_nameservers': current_nameservers,
            'ssl_certificates': ssl_certificates
        }

    def check_hash(self, file_hash):
        myurl = self.url_hash.format(file_hash)
        response = cache.get_cache(myurl)
        if not response:
            headers = {'X-OTX-API-KEY': self.api_key}
            res = requests.get(myurl, headers=headers)
            if res.status_code != 200:
                return None
            response = res.json()
            cache.set_cache(myurl, response)
        try:
            data = response
            # Ensure 'pulse_info' exists in the response
            pulse_info = data.get("pulse_info", {})
            if not pulse_info or pulse_info.get("count", 0) == 0:
                logging.info(f"Hash {file_hash} is not found in OTX (no pulses).")
                return None  # No threats found
                # Extract threat details
            return {
                "verdict": "Malicious",
                "pulses": pulse_info.get("pulses", [])
            }

        except json.JSONDecodeError:
            logging.error(f"OTX API returned invalid JSON for hash {file_hash}")
            return None
