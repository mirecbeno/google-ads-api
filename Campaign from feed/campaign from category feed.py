import pandas as pd
import json
import re
import requests
import xml.etree.ElementTree as ET

# ==========================================
# 1. KONFIGURÁCIA
# ==========================================

FEED_URL = "https://www.domena.sk/category-feed.xml" # Zmeň na reálnu URL feedu
CAMPAIGN_NAME = "Search_Kategorie_2026"
AD_LABEL = "ad_label_kategorie"

# Placeholdery zodpovedajú tagom v kategorickom feede
AD_TEMPLATES_JSON = """
{
    "headlines": {
        "Headline 1": {
            "position": 1,
            "templates": [
                {"text": "Široký výber {{name}}", "max_len": 30},
                {"text": "Kvalitné {{name}}", "max_len": 30},
                {"text": "Nakúpte u nás", "max_len": 30}
            ]
        },
        "Headline 2": {
            "position": 2,
            "templates": [
                {"text": "{{name}}", "max_len": 30},
                {"text": "Všetko pre vaše zdravie", "max_len": 30},
                {"text": "Super ceny", "max_len": 30}
            ]
        },
        "Headline 3": {
            "position": 3,
            "templates": [
                {"text": "Z kategórie {{hierarchy}}", "max_len": 30},
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
                {"text": "Objavte našu ponuku v kategórii {{name}}. Vyberte si z množstva produktov ešte dnes.", "max_len": 90},
                {"text": "Nakupujte {{name}} za najlepšie ceny na trhu s rýchlym doručením.", "max_len": 90}
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
    # Kľúčové slová generujeme z tagu názvu kategórie
    clean_name = clean_text_for_keywords(row['name'])
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
# 3. NAČÍTANIE Z URL A PARSOVANIE KATEGORICKÉHO FEEDU
# ==========================================

def fetch_and_parse_category_feed(url):
    print(f"Sťahujem feed z: {url}")
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"Chyba pri sťahovaní feedu. Status code: {response.status_code}")
        
    print("Súbor stiahnutý, parsujem XML...")
    root = ET.fromstring(response.content)
    
    items_data = []
    
    # Hľadáme tag <category>
    for item in root.findall('.//category'):
        item_dict = {}
        for child in item:
            tag_name = child.tag.split('}')[-1]
            item_dict[tag_name] = child.text if child.text else ""
            
        items_data.append(item_dict)
        
    df = pd.DataFrame(items_data)
    print(f"Úspešne načítaných {len(df)} kategórií z feedu.")
    
    # Napríklad chceme len kategórie, ktoré majú v <hierarchy> slovo "Doplnky stravy"
    if 'hierarchy' in df.columns:
        df_filtered = df[df['hierarchy'].str.contains('Doplnky stravy', na=False, case=False)].copy()
    else:
        df_filtered = df.copy() # Ak tag neexistuje, pustí všetko
    
    print(f"Po aplikovaní filtra zostalo {len(df_filtered)} kategórií na inzerciu.")
    return df_filtered

# ==========================================
# 4. HLAVNÝ ENGINE
# ==========================================

def main():
    try:
        df_feed = fetch_and_parse_category_feed(FEED_URL)
    except Exception as e:
        print(f"Zlyhalo sťahovanie/parsovanie feedu: {e}")
        return
    
    if df_feed.empty:
        print("Filter neprepustil žiadne kategórie. Skontroluj pravidlá.")
        return

    ads_data = []
    keywords_data = []
    
    for index, row in df_feed.iterrows():
        
        # ZMENA: Namiesto id a title berieme identity a name
        ad_group_name = f"{row.get('identity', 'N/A')} - {row.get('name', 'Bez nazvu')}"
        
        ad_row = {
            'Campaign': CAMPAIGN_NAME,
            'Ad Group': ad_group_name,
            'Ad type': 'Responsive search ad',
            'Labels': AD_LABEL,
            'Final URL': row.get('url', ''), # tag pre url vo feede
            'Status': 'Paused'
        }
        
        # Generovanie textov pre Headlines
        for hl_key, hl_data in ad_templates['headlines'].items():
            ad_row[hl_key] = get_valid_ad_text(row, hl_data['templates'])
            
            pos_key = f"{hl_key} position"
            if 'position' in hl_data and hl_data['position']:
                ad_row[pos_key] = hl_data['position']
            else:
                ad_row[pos_key] = ' -'
                
        # Generovanie textov pre Descriptions
        for desc_key, desc_data in ad_templates['descriptions'].items():
            ad_row[desc_key] = get_valid_ad_text(row, desc_data['templates'])
            
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
    
    df_ads.to_csv('D:\\1_category_ads_import.csv', index=False, encoding='utf-8-sig')
    df_keywords.to_csv('D:\\2_category_keywords_import.csv', index=False, encoding='utf-8-sig')
    
    print("Hotovo! Súbory '1_category_ads_import.csv' a '2_category_keywords_import.csv' boli vytvorené.")

main()