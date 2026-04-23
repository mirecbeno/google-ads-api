import pandas as pd
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

CUSTOMER_ID = "1234"   # konkrétny ads účet (bez pomlčiek)
YAML_PATH = "...\\path\\google-ads.yaml"              # cesta k yaml súboru

client = GoogleAdsClient.load_from_storage(YAML_PATH)
ga_service = client.get_service("GoogleAdsService")


query = """
    SELECT
        bidding_seasonality_adjustment.seasonality_adjustment_id,
        bidding_seasonality_adjustment.name
    FROM bidding_seasonality_adjustment
"""

try:
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query)

    rows = []
    for row in response:
        rows.append({
            "ID":        row.bidding_seasonality_adjustment.seasonality_adjustment_id,
            "Názov":     row.bidding_seasonality_adjustment.name,
        })

    df = pd.DataFrame(rows)
    print(f"✅ Načítaných adjustments: {len(df)}")

except GoogleAdsException as ex:
    print(f"❌ Chyba: {ex.failure.errors[0].message}")
    raise

df
