# 🔐 Web Scraper - Playwright Login & Session Automation

This project logs into a website using credentials stored in a `.env` file, saves the session cookies, and reloads the session later to explore authenticated pages.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Automation-green)](https://playwright.dev/python/)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📦 Features

- Logs in with username & password (from `.env`)
- Saves session cookies to file
- Reloads session without re-logging
- Discovers and prints all links on authenticated pages
- Works with JavaScript-heavy pages (via Playwright)

---

## 🧪 Test Site Used

> Default:  
**URL**: [https://the-internet.herokuapp.com/login](https://the-internet.herokuapp.com/login)  
**Username**: `tomsmith`  
**Password**: `SuperSecretPassword!`

---

## ⚙️ Requirements

```bash
pip install -r requirements.txt
playwright install


```

## Architecture & Flow Chart

```mermaid
flowchart TD
    A[Start: main.py] --> B[Read program IDs CSV]
    B --> C[Launch Playwright browser]
    C --> D[For each program ID]
    D --> E[Visit program detail page]
    E --> F[Extract ng-state JSON]
    F --> G[Parse JSON: find program node]
    G --> H[Find survey node via field_survey]
    H --> I[Extract director/contact info from included]
    I --> J[Assemble all fields]
    J --> K[Write to partial CSV]
    K --> L{More IDs?}
    L -- Yes --> D
    L -- No --> M[Write final CSV]
    M --> N[End]
```

