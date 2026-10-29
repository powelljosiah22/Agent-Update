#!/usr/bin/env python3
"""
Automated Factor Library Sync Utility
Author: Financial Coach Agent
Purpose: Checks Dartmouth Kenneth French FTP for updated factor datasets,
         downloads, extracts, and updates CSV files in data/ directory.
"""

import os
import urllib.request
import zipfile
import io

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
BASE_URL = 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/'

TARGETS = {
    'F-F_Research_Data_5_Factors_2x3_CSV.zip': 'F-F_Research_Data_5_Factors_2x3.csv',
    'Developed_ex_US_5_Factors_CSV.zip': 'Developed_ex_US_5_Factors.csv',
    'Emerging_5_Factors_CSV.zip': 'Emerging_5_Factors.csv',
    'Developed_5_Factors_CSV.zip': 'Developed_5_Factors.csv'
}

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def sync_library():
    print(f"[*] Checking Dartmouth Kenneth French Factor Library...")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    updates = {}
    for zip_name, csv_name in TARGETS.items():
        url = BASE_URL + zip_name
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                z = zipfile.ZipFile(io.BytesIO(data))
                z.extract(csv_name, path=DATA_DIR)
                dest = os.path.join(DATA_DIR, csv_name)
                
                # Check latest date
                with open(dest, 'r', errors='ignore') as f:
                    lines = f.readlines()
                monthly = [l.strip()[:6] for l in lines if l and l[:6].isdigit()]
                latest_date = monthly[-1] if monthly else "Unknown"
                updates[csv_name] = latest_date
                print(f"  [+] {csv_name:<36} -> Synced (Latest Month: {latest_date})")
        except Exception as e:
            print(f"  [-] Failed to sync {zip_name}: {e}")
            
    return updates

if __name__ == '__main__':
    sync_library()
