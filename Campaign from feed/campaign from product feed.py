import pandas as pd
import json
import re
import requests
import xml.etree.ElementTree as ET

# ==========================================
# 1. KONFIGURÁCIA
# ==========================================

# URL tvojho XML feedu
FEED_URL = "https://www.domena.sk/feed.xml"

CAMPAIGN_NAME = "Search_Produkty_2026"
AD_LABEL = "ad_label_1"

# UPOZORNENIE: V Google Feede sa názov volá 'title' (nie 'name') a url sa volá 'link'.
# Všetky 'g:' prefixy ignorujeme, zadávaš to bez nich.
# Štruktúra umožňuje definovať 'position' pre uzamknutie pozície (pin) v responzívnej reklame.
AD_TEMPLATES_JSON = """
{
    "headlines": {
        "Headline 1": {
            "position": 1,
            "templates": [
                {"text": "Kúpte {{title}}", "max_len": 30},
                {"text": "Značkové {{product_type}}", "max_len": 30},
                {"text": "Kvalitné produkty v zľave", "max_len": 30}
            ]
        },
        "Headline 2": {
            "position": 2,
            "templates": [
                {"text": "{{title}}", "max_len": 30},
                {"text": "Značkové {{product_type}}", "max_len": 30},
                {"text": "Nevydalo", "max_len": 30}
            ]
        },
        "Headline 3": {
            "position": 3,
            "templates": [
                {"text": "Len za {{price}}", "max_len": 30},
                {"text": "Skvelé ceny v našom e-shope", "max_len": 30}
            ]
        },
        "Headline 4": {
            "templates": [
                {"text": "Skladom odosielame ihneď", "max_len": 30}
            ]
        }
    },
    "descriptions": {
        "Description 1": {
            "position": 1,
            "templates": [
                {"text": "Objednajte si {{title}} od značky {{brand}} ešte dnes. Super cena {{price}}.", "max_len": 90},
                {"text": "Objednajte si {{brand}} produkty ešte dnes. Najlepšie ceny na trhu.", "max_len": 90}
            ]
        },
        "Description 2": {
            "templates": [
                {"text": "Doprava zadarmo nad 50€. Bezpečný nákup a rýchle dodanie až k vám domov.", "max_len": 90}
            ]
        }
    }
}
"""
ad_templates = json.loads(AD_TEMPLATES_JSON)

# ==========================================
# 2. POMOCNÉ FUNKCIE (Logika textov a kľúč. slov)
# ==========================================

def get_valid_ad_text(row, template_list):
    for template in template_list:
        text = template['text']
        max_len = template['max_len']
        
        for col_name in row.index:
            placeholder = f"{{{{{col_name}}}}}"
            if placeholder in text:
                text = text.replace(placeholder, str(row[col_name]))
        
        if len(text) <= max_len:
            return text
            
    return "N/A"

def clean_text_for_keywords(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def generate_keywords(row):
    # Generujeme slová z 'title', keďže to je štandard v Google feede
    clean_name = clean_text_for_keywords(row['title'])
    words = clean_name.split()
    
    keywords = []
    if len(words) > 0:
        keywords.append({'Keyword': clean_name, 'Criterion Type': 'Exact'})
        if len(words) >= 3:
            keywords.append({'Keyword': " ".join(words[:3]), 'Criterion Type': 'Phrase'})
        if len(words) >= 2:
            keywords.append({'Keyword': " ".join(words[:2]), 'Criterion Type': 'Phrase'})
            
    return keywords

# ==========================================
# 3. NAČÍTANIE Z URL A PARSOVANIE GOOGLE FEEDU
# ==========================================

def fetch_and_parse_google_feed(url):
    print(f"Sťahujem feed z: {url}")
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"Chyba pri sťahovaní feedu. Status code: {response.status_code}")
        
    print("Súbor stiahnutý, parsujem XML...")
    root = ET.fromstring(response.content)
    
    items_data = []
    
    # Prechádzame všetky <item> tagy v RSS/XML
    for item in root.findall('.//item'):
        item_dict = {}
        for child in item:
            # Odstránenie menného priestoru (namespace), napr. {http://base.google.com/ns/1.0}price -> price
            tag_name = child.tag.split('}')[-1]
            item_dict[tag_name] = child.text if child.text else ""
            
        items_data.append(item_dict)
        
    df = pd.DataFrame(items_data)
    
    # Google Ads cena obsahuje menu (napr. "120.00 EUR"). 
    # Vytvoríme čistý číselný stĺpec 'price_numeric' pre matematické filtrovanie.
    # Očistíme aj samotný stĺpec 'price', aby sa v textových šablónach (napr. {{price}}) zobrazila len číselná hodnota bez meny.
    if 'price' in df.columns:
        df['price_numeric'] = df['price'].str.extract(r'([\d\.]+)').astype(float)
        df['price'] = df['price'].astype(str).str.replace(r'[^\d\.,]', '', regex=True)
    else:
        df['price_numeric'] = 0.0

    print(f"Úspešne načítaných {len(df)} produktov z feedu.")
    
    # TVOJ FILTER (Zmenené na štandardné Google hodnoty)
    # V Google je to 'in_stock', nie 'in stock'
    df_filtered = df[
        (df['availability'] == 'in_stock') & 
        #(df['price_numeric'] >= 20.0) &
        (df['product_type'].str.contains('ovocie', na=False))
    ].copy()
    
    print(f"Po aplikovaní filtra zostalo {len(df_filtered)} produktov na inzerciu.")
    return df_filtered

# ==========================================
# 4. HLAVNÝ ENGINE
# ==========================================

def main():
    try:
        df_feed = fetch_and_parse_google_feed(FEED_URL)
    except Exception as e:
        print(f"Zlyhalo sťahovanie/parsovanie feedu: {e}")
        return
    
    if df_feed.empty:
        print("Filter neprepustil žiadne produkty. Skontroluj pravidlá.")
        return

    ads_data = []
    keywords_data = []
    
    for index, row in df_feed.iterrows():
        
        # ID a Názov tvoria reklamnú skupinu
        ad_group_name = f"{row.get('id', 'N/A')} - {row.get('title', 'Bez nazvu')}"
        
        # Reklamy (v Google feede je to link, nie url)
        # Definovanie statických parametrov podľa požiadaviek Google Ads Editora
        ad_row = {
            'Campaign': CAMPAIGN_NAME,
            'Ad Group': ad_group_name,
            'Ad type': 'Responsive search ad',
            'Labels': AD_LABEL,
            'Final URL': row.get('link', ''),
            'Status': 'Paused'
        }
        
        # Generovanie textov pre Headlines a nastavenie ich pinu (pozície)
        for hl_key, hl_data in ad_templates['headlines'].items():
            ad_row[hl_key] = get_valid_ad_text(row, hl_data['templates'])
            
            # G. Ads Editor vyžaduje ' -' ak pozícia nie je explicitne uzamknutá
            pos_key = f"{hl_key} position"
            if 'position' in hl_data and hl_data['position']:
                ad_row[pos_key] = hl_data['position']
            else:
                ad_row[pos_key] = ' -'
                
        # Generovanie textov pre Descriptions a nastavenie ich pinu (pozície)
        for desc_key, desc_data in ad_templates['descriptions'].items():
            ad_row[desc_key] = get_valid_ad_text(row, desc_data['templates'])
            
            # G. Ads Editor vyžaduje ' -' ak pozícia nie je explicitne uzamknutá
            pos_key = f"{desc_key} position"
            if 'position' in desc_data and desc_data['position']:
                ad_row[pos_key] = desc_data['position']
            else:
                ad_row[pos_key] = ' -'
            
        ads_data.append(ad_row)
        
        # Kľúčové slová
        kws = generate_keywords(row)
        for kw in kws:
            keywords_data.append({
                'Campaign': CAMPAIGN_NAME,
                'Ad Group': ad_group_name,
                'Keyword': kw['Keyword'],
                'Criterion Type': kw['Criterion Type'],
                'Status': 'Paused'
            })

    df_ads = pd.DataFrame(ads_data)
    df_keywords = pd.DataFrame(keywords_data)
    
    df_ads.to_csv('D:\\1_ads_import2.csv', index=False, encoding='utf-8-sig')
    df_keywords.to_csv('D:\\2_keywords_import2.csv', index=False, encoding='utf-8-sig')
    
    print("Hotovo! Súbory '1_ads_import2.csv' a '2_keywords_import2.csv' boli vytvorené.")


main()