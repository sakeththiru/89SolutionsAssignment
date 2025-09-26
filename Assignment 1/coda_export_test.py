#!/usr/bin/env python3
#test via py script

import requests
import time

# config - your API credentials and page details
API_TOKEN = "f059083a-79d8-413a-a135-3cb4a7f1ce46"
DOCUMENT_ID = "I3kdM_WJkT"
PAGE_ID = "canvas-E5zOEJWlHW"

# Headers for API authentication
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def main():
    print("Coda.io API Export")
    print("=" * 30)
    
    # export process
    print("Starting export")
    export_data = {"outputFormat": "html"}
    response = requests.post(f"https://coda.io/apis/v1/docs/{DOCUMENT_ID}/pages/{PAGE_ID}/export", 
                           headers=headers, json=export_data)
    
    # export request success check
    if response.status_code not in [200, 202]:
        print(f"Export failed: {response.text}")
        return
    
    # req id for export 
    request_id = response.json()['id']
    print(f"Export started with ID: {request_id}")
    
    # Main: export
    print("Waiting for export to complete")
    while True:
        # export status 
        status_response = requests.get(f"https://coda.io/apis/v1/docs/{DOCUMENT_ID}/pages/{PAGE_ID}/export/{request_id}", 
                                    headers=headers)
        
        # case was id expired
        if status_response.status_code == 404:
            print("Request expired, starting new export")
            return main()
        
        # Check for other errors
        if status_response.status_code != 200:
            print(f"Status check failed: {status_response.text}")
            time.sleep(2)
            continue
        
        # status checks be safe
        status_data = status_response.json()
        print(f"Status: {status_data['status']}")
        
        if status_data['status'] == 'complete':
            print("Export completed!")
            break
        
        if status_data['status'] == 'failed':
            print(f"Export failed: {status_data}")
            return
        
        time.sleep(2)
    
    # Step 3: Download the HTML content
    print("Downloading HTML content")
    download_response = requests.get(status_data['downloadLink'])
    
    # html save
    if download_response.status_code == 200:
        with open('exported_page.html', 'w', encoding='utf-8') as f:
            f.write(download_response.text)
        print("HTML saved to: exported_page.html")
    else:
        print(f"Download failed: {download_response.text}")

if __name__ == "__main__":
    main()
