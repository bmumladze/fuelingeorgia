import re
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

def scrape_data():
    url = "https://priceshub.ge/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    
    try:
        response = requests.get("https://priceshub.ge/conti/result.php", headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        def get_text(elements, index):
            if len(elements) > index:
                try: 
                    return float(elements[index].text.strip())
                except: 
                    return None
            return None

        socar_spans = soup.select('b + span')
        gulf_prices = soup.select('.price_entry .product_price')
        wissol_prices = soup.select('.wissol-prices li')
        romp_prices = soup.select('.table-responsive tbody td:nth-of-type(2)')
        lukoil_prices = soup.select('.luk-prices p')
        portal_prices = soup.select('.old_fuel_price')
        connect_prices = soup.select('.connect li')

        # მონაცემების ლექსიკონი, companies -> fuel types -> prices
        companies = {
            "Socar": {
                "Superi": get_text(socar_spans, 0),
                "Premiumi": get_text(socar_spans, 1),
                "Regulari": get_text(socar_spans, 2),
                "Euro_Dizeli": get_text(socar_spans, 3),
                "Dizeli": get_text(socar_spans, 4)
            },
            "Gulf": {
                "Superi": get_text(gulf_prices, 0), 
                "Premiumi": get_text(gulf_prices, 1), 
                "Regulari": get_text(gulf_prices, 3), 
                "Euro_Dizeli": get_text(gulf_prices, 4),
                "Dizeli": get_text(gulf_prices, 5)
            },
            "Wissol": {
                "Superi": get_text(wissol_prices, 1), 
                "Premiumi": get_text(wissol_prices, 3), 
                "Regulari": get_text(wissol_prices, 9),
                "Euro_Dizeli": get_text(wissol_prices, 5),
                "Dizeli": get_text(wissol_prices, 7)
            },
            "Rompetrol": {
                "Superi": get_text(romp_prices, 0), 
                "Premiumi": get_text(romp_prices, 1), 
                "Regulari": get_text(romp_prices, 2),
                "Euro_Dizeli": get_text(romp_prices, 3),
                "Dizeli": get_text(romp_prices, 4)
            },
            "Lukoil": {
                "Superi": get_text(lukoil_prices, 1), 
                "Premiumi": get_text(lukoil_prices, 2), 
                "Regulari": get_text(lukoil_prices, 3),
                "Euro_Dizeli": get_text(lukoil_prices, 4),
                "Dizeli": None # აკლია
            },
            "Portal": {
                "Superi": get_text(portal_prices, 0), 
                "Premiumi": get_text(portal_prices, 1), 
                "Regulari": get_text(portal_prices, 2),
                "Euro_Dizeli": get_text(portal_prices, 3),
                "Dizeli": get_text(portal_prices, 4)
            },
            "Connect": {
                "Superi": get_text(connect_prices, 0), 
                "Premiumi": get_text(connect_prices, 1), 
                "Regulari": get_text(connect_prices, 2),
                "Euro_Dizeli": get_text(connect_prices, 3),
                "Dizeli": get_text(connect_prices, 4)
            }
        }
        
        # თბილისის დროის დაფიქსირება
        tz = pytz.timezone('Asia/Tbilisi')
        current_time = datetime.now(tz)
        date_str = current_time.strftime("%Y-%m-%d")
        record_id = current_time.strftime("%Y-%m-%d %H") # 1 საათიანი უნიკალურობისთვის

        new_entry = {
            "id": record_id,
            "date": date_str,
            "timestamp": current_time.isoformat(),
            "prices": companies
        }
        
        history_file = os.path.join(os.path.dirname(__file__), 'history.json')
        
        # წაკითხვა თუ არსებობს ფაილი
        history = []
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    history = []
                    
        # შემოწმება უკვე გვაქვს თუ არა ამ საათის ჩანაწერი
        if history and history[-1].get('id') == record_id:
            print("Today's current hour data already exists. Updating...")
            history[-1] = new_entry
        else:
            history.append(new_entry)
            
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
            
        print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] Data scraped successfully!")
        
    except Exception as e:
        print(f"Error while scraping: {e}")

if __name__ == "__main__":
    scrape_data()
