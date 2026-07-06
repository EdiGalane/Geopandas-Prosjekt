"""
Hånterer autorisering for barentswatch. 

For å kunne bruke APIen må vi ha en acces token, det er nemlig dette denne
filen og dens metoder gjør. Metodene tar for seg kunn innloggingsmetoden.

bruk:
    from src.data_ingestion.barentswatch_client import BarentsWatchClient
    client = BarentsWatchClient()      # leser nokler fra .env
    headers = client.auth_headers()    # klar til bruk i et API-kall
"""

import os
import time
import requests
from dotenv import load_dotenv
 

# Last inn variabler fra .env-filen i prosjektroten, 
# denne inneholder BARENTSWATCH_CLIENT_ID og BARENTSWATCH_CLIENT_SECRET.

load_dotenv()

TOKEN_URL = "https://id.barentswatch.no/connect/token" # dette er serveren til barentswatch der 
                                                       # nøkkelen må sendes for å få token
 
 
class BarentsWatchClient:
    # hånterer autorisering
    def __init__(self, client_id=None, client_secret=None):
        # Hent nokler fra argumenter hvis gitt
        self.client_id = client_id or os.getenv("BARENTSWATCH_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("BARENTSWATCH_CLIENT_SECRET")
 
        #Test hvis nøkler magnler. uten denne sjekken kan vi risikere en feil når vi henter token
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Mangler API-nokler. Sjekk at .env-filen finnes i prosjektroten "
                "og inneholder BARENTSWATCH_CLIENT_ID og BARENTSWATCH_CLIENT_SECRET."
            )
 
        # Vi lagrer tokenen og når den utløper, så vi slipper å hente ny for hvert eneste API-kall i samme kjøring.
        self._token = None
        self._token_expires_at = 0  # unix-tidspunkt for utlop


    def get_token(self):
        #returnerer gyldig access token
        if self._token and time.time() < (self._token_expires_at - 60):
            return self._token #gjenbruk dersom token er fortsatt fresh

        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials", #dette betyr at en maskin logger inn med id+secret, ikke menneske
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "ais",  
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )

        response.raise_for_status()
 
        data = response.json()
        self._token = data["access_token"]
        # expires_in er antall sekunder tokenen varer 
        self._token_expires_at = time.time() + data.get("expires_in", 3600)
        return self._token

    def auth_headers(self):
        #dette er hva andre deler av applikasjonen bruker. de ber ikke om
        #tokens eller noe, bare "headers" og får de ferdig utfylt med token
        return {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
        }