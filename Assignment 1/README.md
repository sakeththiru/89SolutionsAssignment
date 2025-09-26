
# Coda API Export Flow Chart

syntax : python coda_export_test.py

Expected Output:
Coda.io API Export
==============================
Starting export
Export started with ID: 4ccb8e2b-ee52-42b1-8edf-b291c9d626e2
Waiting for export to complete
Status: inProgress
Status: complete
Export completed!
Downloading HTML content
HTML saved to: exported_page.html


Result:
O/P is `exported_page.html` 

Context:
Page selected : Engineering team hub
________________________________________________________________________________________________________________________

┌─────────────────────────────────────────────────────────────────┐
│                    CODA API EXPORT PROCESS                      |  
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│   START SCRIPT  │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ 1. START EXPORT │
│                 │
│ POST /export    │
│ Body: {         │
│  "outputFormat":│
│   "html"        │
│ }               │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ 2. GET REQUEST  │
│      ID         │
│                 │
│ Response: {     │
│   "id": "abc123"│
│   "status":     │
│   "inProgress"  │
│ }               │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ 3. CHECK STATUS │
│                 │
│ GET /export/    │
│ {request_id}    │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ 4. STATUS = ?   │
│                 │
│ • inProgress    │
│ • complete      │
│ • failed        │
│ • 404 (expired) │
└─────────┬───────┘
          │
          ▼
    ┌─────────┐
    │ STATUS  │
    │ CHECK   │
    └────┬────┘
         │
    ┌────▼────┐
    │inProgress│
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │ WAIT 2  │
    │ SECONDS │
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │ GO BACK │
    │ TO STEP │
    │    3    │
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │complete │
    └────┬────┘
         │
         ▼
┌─────────────────┐
│ 5. DOWNLOAD     │
│    HTML         │
│                 │
│ GET {downloadLink}│
│ (S3 URL)        │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ 6. SAVE FILE    │
│                 │
│ Write to:       │
│ exported_page.html│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   SUCCESS!      │
│                 │
│ HTML file       │
│ created         │
└─────────────────┘

┌─────────────────┐
│    ERROR CASES  │
└─────────────────┘

┌─────────┐
│ 404     │
│ (expired)│
└────┬────┘
     │
     ▼
┌─────────┐
│ RESTART │
│ PROCESS │
│ (go to  │
│ step 1) │
└─────────┘

┌─────────┐
│ failed  │
└────┬────┘
     │
     ▼
┌─────────┐
│ EXIT    │
│ SCRIPT  │
└─────────┘

┌─────────┐
│ Other   │
│ Errors  │
└────┬────┘
     │
     ▼
┌─────────┐
│ WAIT &  │
│ RETRY   │
└─────────┘
______________________________________________________________________________


Tokens
- API_TOKEN: Your Coda API token
- DOCUMENT_ID: The document you want to export from
- PAGE_ID: The specific page to export

API endpoints used:
1. **POST** `/docs/{docId}/pages/{pageId}/export` - Start export
2. **GET** `/docs/{docId}/pages/{pageId}/export/{requestId}` - Check status
3. **GET** `{downloadLink}` - Download HTML (S3 URL)

Data Flow
1. Request ID - Unique identifier for tracking export
2. Status - Current state of the export (inProgress/complete/failed)
3. Download Link - S3 URL to get the final HTML content

Error Handling
- 404 Error - Request ID expired, restart process
-Failed Status - Export failed, exit script
- Other Errors - Wait and retry

______________________________________________________________________________