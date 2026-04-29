import pandas as pd
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import configparser

def ads_id(zoznam_domen):
    config = configparser.ConfigParser()
    config.read('D:\\accounts-config.ini')
    
    vysledne_id =[]
    ads_sekcia = config['ADS_ACCOUNTS']

    for domena in zoznam_domen:
        ad_id = ads_sekcia.get(domena)
        if ad_id:
            vysledne_id.append(ad_id.replace("-", ""))
        else:
            print(f"Varovanie: Doména {domena} sa nenašla v config.ini")
            
    return vysledne_id

# --- 1. INICIALIZÁCIA ---
CUSTOMER_ID = ads_id(["domain.sk"])[0]
YAML_PATH   = "D:\\google-ads.yaml"              

client = GoogleAdsClient.load_from_storage(YAML_PATH)
ga_service = client.get_service("GoogleAdsService")

try:
    # --- 2. KROK: ZÍSKANIE AKTÍVNYCH PMAX KAMPANÍ ---
    print("⏳ Získavam zoznam aktívnych PMax kampaní...")
    campaigns_query = """
        SELECT
            campaign.id,
            campaign.name
        FROM campaign
        WHERE
            campaign.status = 'ENABLED'
            AND campaign.advertising_channel_type = 'PERFORMANCE_MAX'
    """
    
    campaigns_response = ga_service.search(customer_id=CUSTOMER_ID, query=campaigns_query)
    
    # Uložíme do slovníka: {id_kampane: "Názov kampane"}
    active_pmax_campaigns = {}
    for row in campaigns_response:
        active_pmax_campaigns[row.campaign.id] = row.campaign.name
        
    pocet_kampani = len(active_pmax_campaigns)
    print(f"✅ Nájdených aktívnych PMax kampaní: {pocet_kampani}\n")

    if pocet_kampani == 0:
        print("Boli nájdené 0 PMax kampaní. Končím skript.")
    else:
        # --- 3. KROK: ITERÁCIA A SŤAHOVANIE PLACEMENTOV ---
        all_rows =[]
        counter = 1
        
        for camp_id, camp_name in active_pmax_campaigns.items():
            print(f"Spracovávam kampaň {counter}/{pocet_kampani}: {camp_name} (ID: {camp_id})")
            
            # Dynamický dopyt - vkladáme camp_id priamo do query pomocou f-stringu
            placement_query = f"""
                SELECT
                    performance_max_placement_view.display_name,
                    performance_max_placement_view.placement,
                    performance_max_placement_view.placement_type,
                    performance_max_placement_view.target_url,
                    metrics.impressions,
                    campaign.id
                FROM performance_max_placement_view
                WHERE
                    campaign.id = {camp_id}
                    AND segments.date DURING LAST_30_DAYS
                ORDER BY metrics.impressions DESC
            """
            
            placement_response = ga_service.search(customer_id=CUSTOMER_ID, query=placement_query)
            
            for row in placement_response:
                all_rows.append({
                    "Campaign ID":      camp_id,
                    "Campaign Name":    camp_name,
                    "Display name":     row.performance_max_placement_view.display_name,
                    "Placement":        row.performance_max_placement_view.placement,
                    "Placement type":   row.performance_max_placement_view.placement_type.name,
                    "Target url":       row.performance_max_placement_view.target_url,
                    "Impressions":      row.metrics.impressions,
                })
            
            counter += 1

        # --- 4. KROK: VYTVORENIE DATAFRAME ---
        df = pd.DataFrame(all_rows)
        print(f"\n🎉 Hotovo! Celkovo stiahnutých riadkov: {len(df)}")

except GoogleAdsException as ex:
    print(f"❌ Chyba API: {ex.failure.errors[0].message}")
    raise

# Zobrazenie výsledku
#df

# Export do excelu
#df.to_excel("D:\\vystup1223.xlsx", index=False)

# Tvoj zoznam textov, ktoré chceš hľadať v URL (uprav si podľa potreby)
hladane_texty = ["weather", "pocasie", "game", "sudok", "sport", "calcula", 
                 "kalkula", "radio", "radia", "kurzy", "wiki", "pedia", 
                 "futbal", "footba", "mahjong", "card"]

# 1. Filter: Ponechať iba riadky, kde 'Placement type' je presne 'WEBSITE'
df_website = df[df["Placement type"] == "WEBSITE"]

# 2. Filter: 'Target url' musí obsahovať niektorý z textov v tvojom zozname
# Spojíme zoznam pomocou '|', čo v regexe znamená "ALEBO" (vznikne "bazos|topky|sme|cas")
vzor = '|'.join(hladane_texty)

# Použijeme str.contains. 
# case=False znamená, že nebude rozlišovať veľké a malé písmená.
# na=False zabráni errorom, ak by v stĺpci boli prázdne (NaN) hodnoty.
df_filtered = df_website[df_website["Target url"].str.contains(vzor, case=False, na=False)]

# 3. Získanie zoznamu iba unikátnych 'Target url'
unikatne_urls = df_filtered["Target url"].unique().tolist()

# Vypísanie výsledku
print(f"Nájdených unikátnych URL: {len(unikatne_urls)}")
#print(unikatne_urls)


# odoslanie do vylučujúceho zoznamu domén
def add_domains_to_existing_list(client, customer_id, shared_set_id, domains):
    shared_criterion_service = client.get_service("SharedCriterionService")
    
    # Vytvorenie resource_name pre zoznam
    shared_set_resource_name = client.get_service("SharedSetService").shared_set_path(
        customer_id, shared_set_id
    )
    
    operations = []
    for domain in domains:
        operation = client.get_type("SharedCriterionOperation")
        criterion = operation.create
        
        # Prepojenie s existujúcim zoznamom
        criterion.shared_set = shared_set_resource_name
        # Zadanie domény
        criterion.placement.url = domain
        
        operations.append(operation)

    try:
        response = shared_criterion_service.mutate_shared_criteria(
            customer_id=customer_id,
            operations=operations
        )
        print(f"Úspešne pridaných {len(response.results)} domén do zoznamu ID: {shared_set_id}")
        
    except GoogleAdsException as ex:
        print(f"Chyba: {ex}")

# --- Spustenie ---
googleads_client = GoogleAdsClient.load_from_storage(YAML_PATH)

SHARED_SET_ID = "12345" # ID zoznamu, z url sharedSetId=123456...

add_domains_to_existing_list(
    googleads_client, 
    CUSTOMER_ID, 
    SHARED_SET_ID, 
    unikatne_urls
)