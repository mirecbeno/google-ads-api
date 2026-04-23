# --- 1. IMPORTY ---
from google.ads.googleads.client import GoogleAdsClient
from google.api_core import protobuf_helpers
from google.ads.googleads.errors import GoogleAdsException

# --- 2. DEFINÍCIA FUNKCIE ---
def update_seasonality_adjustment(client, customer_id, adjustment_id, start_datetime, end_datetime, modifier):
    bidding_seasonality_adjustment_service = client.get_service("BiddingSeasonalityAdjustmentService")
    operation = client.get_type("BiddingSeasonalityAdjustmentOperation")
    
    adjustment = operation.update

    # Vytvorenie Resource Name
    adjustment.resource_name = bidding_seasonality_adjustment_service.bidding_seasonality_adjustment_path(
        customer_id, adjustment_id
    )

    # 1. Zmena dátumov
    adjustment.start_date_time = start_datetime
    adjustment.end_date_time = end_datetime
    
    # 2. ZMENA KONVERZNÉHO POMERU (NÁSOBITEĽ)
    adjustment.conversion_rate_modifier = modifier

    # Vytvorenie masky (vďaka ._pb to zoberie všetky zmeny automaticky)
    client.copy_from(
        operation.update_mask,
        protobuf_helpers.field_mask(None, adjustment._pb)
    )

    try:
        response = bidding_seasonality_adjustment_service.mutate_bidding_seasonality_adjustments(
            customer_id=customer_id, operations=[operation]
        )
        print(f"✅ Úspešne aktualizované (účet: {customer_id}, adjustment_id: {adjustment_id})")
        print(f"   Resource Name: {response.results[0].resource_name}")
        return True

    except GoogleAdsException as ex:
        print(f"❌ Chyba pri volaní API pre účet {customer_id} (adjustment_id: {adjustment_id}):")
        for error in ex.failure.errors:
            print(f"  - Detail chyby: {error.message}")
        return False


# --- 3. NASTAVENIE PREMENNÝCH ---

# Zoznam úloh: Doplňte ID účtov a ich príslušné Adjustment ID

# Dátumy ako premenná pre viaceré účty
NEW_START_DATE = "2026-04-24 18:00:00"
NEW_END_DATE = "2026-04-25 23:00:00"
#NEW_MODIFIER = 0.85  # Zníženie o 20%

TASKS = [
    # SK
    {"customer_id": "1234", "adjustment_id": "1234", "new_modifier": 0.85, "new_start_date": NEW_START_DATE, "new_end_date": NEW_END_DATE},
    # CZ
    {"customer_id": "1234", "adjustment_id": "1234", "new_modifier": 0.85, "new_start_date": NEW_START_DATE, "new_end_date": NEW_END_DATE},
    # HU
    {"customer_id": "1234", "adjustment_id": "1234", "new_modifier": 0.85, "new_start_date": NEW_START_DATE, "new_end_date": NEW_END_DATE},
    # PL
    {"customer_id": "1234", "adjustment_id": "1234", "new_modifier": 0.85, "new_start_date": NEW_START_DATE, "new_end_date": NEW_END_DATE},
    # RO
    {"customer_id": "1234", "adjustment_id": "1234", "new_modifier": 0.85, "new_start_date": NEW_START_DATE, "new_end_date": NEW_END_DATE},
    # AT
    {"customer_id": "1234", "adjustment_id": "1234", "new_modifier": 0.85, "new_start_date": NEW_START_DATE, "new_end_date": NEW_END_DATE},
    # DE
    {"customer_id": "1234", "adjustment_id": "1234", "new_modifier": 0.85, "new_start_date": NEW_START_DATE, "new_end_date": NEW_END_DATE},
    # Sem môžeš pridávať ďalšie účty...
]

YAML_PATH = "...path\\google-ads.yaml" 

# --- 4. SPUSTENIE ---
try:
    # Načítanie klienta (stačí načítať raz pre všetky účty)
    googleads_client = GoogleAdsClient.load_from_storage(YAML_PATH)
    
    print(f"Spúšťam aktualizáciu pre {len(TASKS)} položiek...\n")
    print("-" * 40)

    # Prechod cez všetky definované účty
    for task in TASKS:
        current_customer_id = task["customer_id"]
        current_adjustment_id = task["adjustment_id"]
        new_modifier = task["new_modifier"]
        new_start_date = task["new_start_date"]
        new_end_date = task["new_end_date"]
        
        update_seasonality_adjustment(
            client=googleads_client, 
            customer_id=current_customer_id, 
            adjustment_id=current_adjustment_id, 
            start_datetime=new_start_date, 
            end_datetime=new_end_date,
            modifier=new_modifier
        )
        print("-" * 40)
        
    print("\n✅ Všetky úlohy boli spracované.")
    
except FileNotFoundError:
    print("❌ Súbor 'google-ads.yaml' sa nenašiel na zadanej ceste.")
except Exception as e:
    print(f"❌ Nastala neočakávaná kritická chyba: {e}")
