 The parser needs to know more details on how the json schema is to be effective

```
(venv) ➜  scrapper git:(master) ✗ jq '.. | objects | .title? // empty' 2.json

"Announcement banner"
"LEARN MORE! "
"Announcement banner"
"System Wide Message"
"Link"
"System Wide Message"
"Mass General Brigham/Massachusetts General Hospital Program"
"Internal Medicine"
"Mass General Brigham/Massachusetts General Hospital Program"
"Massachusetts General Hospital"
"Newton-Wellesley Hospital"
"Mass General Brigham"
"Mass General Brigham/Massachusetts General Hospital Program"
(venv) ➜  scrapper git:(master) ✗ jq '.. | objects | .title? // empty' 1.json

"NYU Grossman School of Medicine Program"
"Internal Medicine"
"NYU Grossman School of Medicine Program"
"NYC Health + Hospitals/Bellevue"
"Manhattan VA Harbor Health Care System"
"NYU Langone Hospital-Brooklyn"
"NYU Langone Hospitals"
"Gouverneur Healthcare Services"
"NYU Grossman School of Medicine"
"NYU Grossman School of Medicine Program"
"Announcement banner"
"LEARN MORE! "
"Announcement banner"
"System Wide Message"
"Link"
"System Wide Message"
```
