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
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # PricesHub HTML სტრუქტურა ინახავს ფასებს სპეციფიკურ div-ებში.
        # cont.js ფაილის მიხედვით, HTML ველები ასეთია:
        # outputDiv1 - outputDiv7 : Socar (სხვადასხვა ტიპი)
        # goutputDiv1 - goutputDiv7 : Gulf
        # woutputDiv1 - woutputDiv7 : Wissol
        # routputDiv1 - routputDiv5 : Rompetrol
        # woutputDiv9 - woutputDiv12 : Lukoil
        
        def safe_float(div_class):
            elem = soup.find('div', class_=div_class)
            if elem and elem.text.strip():
                try:
                    return float(elem.text.strip())
                except ValueError:
                    return None
            return None

        # მონაცემების ლექსიკონი, companies -> fuel types -> prices
        companies = {
            "Socar": {
                "Superi": None, # აკლია ძირითადად
                "Premiumi": safe_float('outputDiv2'), # premiumid 
                "Regulari": safe_float('outputDiv3'), # regularid
                "Euro_Dizeli": safe_float('outputDiv5'),
                "Dizeli": safe_float('outputDiv4')
            },
            "Gulf": {
                "Superi": safe_float('goutputDiv1'), 
                "Premiumi": safe_float('goutputDiv2'), 
                "Regulari": safe_float('goutputDiv4'), # regulari
                "Euro_Dizeli": safe_float('goutputDiv6'),
                "Dizeli": safe_float('goutputDiv5')
            },
            "Wissol": {
                "Superi": safe_float('woutputDiv1'), 
                "Premiumi": safe_float('woutputDiv2'), 
                "Regulari": safe_float('woutputDiv3'),
                "Euro_Dizeli": safe_float('woutputDiv4'),
                "Dizeli": safe_float('woutputDiv5')
            },
            "Rompetrol": {
                "Superi": safe_float('routputDiv1'), 
                "Premiumi": safe_float('routputDiv2'), 
                "Regulari": safe_float('routputDiv3'),
                "Euro_Dizeli": safe_float('routputDiv5'),
                "Dizeli": safe_float('routputDiv4')
            },
            "Lukoil": {
                "Superi": safe_float('woutputDiv9'), 
                "Premiumi": safe_float('woutputDiv10'), 
                "Regulari": safe_float('woutputDiv11'),
                "Euro_Dizeli": safe_float('woutputDiv12'),
                "Dizeli": None # აკლია
            },
            "Portal": {
                "Superi": safe_float('woutputDiv13'), 
                "Premiumi": safe_float('woutputDiv14'), 
                "Regulari": safe_float('woutputDiv15'),
                "Euro_Dizeli": safe_float('woutputDiv16'),
                "Dizeli": safe_float('woutputDiv17')
            },
            "Connect": {
                "Superi": None, 
                "Premiumi": safe_float('coutputDiv1'), 
                "Regulari": safe_float('coutputDiv2'),
                "Euro_Dizeli": safe_float('coutputDiv3'),
                "Dizeli": None 
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
