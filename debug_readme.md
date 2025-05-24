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

```
                "type": "paragraph--program_individual",
                "id": "22dd9d35-31b0-4fbd-b565-4ae6ef0c5a98",
                "meta": {
                  "target_revision_id": 2949296,
                  "drupal_internal__target_id": 25351
                }
              },
              "links": {
                "related": {
                  "href": "https://freida-admin.ama-assn.org/api/node/survey_2024/3f9b54d0-9c0a-4cc7-8d0d-83c2c63b3ae2/field_program_contact?resourceVersion=id%3A35435871"
                },
                "self": {
                  "href": "https://freida-admin.ama-assn.org/api/node/survey_2024/3f9b54d0-9c0a-4cc7-8d0d-83c2c63b3ae2/relationships/field_program_contact?resourceVersion=id%3A35435871"
                }
              }
            },
            "field_program_director": {
              "data": {
                "type": "paragraph--program_individual",
                "id": "ccce8a23-4ce3-457f-922a-3d15a6a4f352",
                "meta": {
                  "target_revision_id": 2968396,
                  "drupal_internal__target_id": 25346
                }
              },
              "links": {
                "related": {
                  "href": "https://freida-admin.ama-assn.org/api/node/survey_2024/3f9b54d0-9c0a-4cc7-8d0d-83c2c63b3ae2/field_program_director?resourceVersion=id%3A35435871"
                },
                "self": {
                  "href": "https://freida-admin.ama-assn.org/api/node/survey_2024/3f9b54d0-9c0a-4cc7-8d0d-83c2c63b3ae2/relationships/field_program_director?resourceVersion=id%3A35435871"
                }
              }
            },
            "field_resource_gallery_images": {
              "data": [],
              "links": {
                "related": {
                  "href": "https://freida-admin.ama-assn.org/api/node/survey_2024/3f9b54d0-9c0a-4cc7-8d0d-83c2c63b3ae2/field_resource_gallery_images?resourceVersion=id%3A35435871"
                },
                "self": {
                  "href": "https://freida-admin.ama-assn.org/api/node/survey_2024/3f9b54d0-9c0a-4cc7-8d0d-83c2c63b3ae2/relationships/field_resource_gallery_images?resourceVersion=id%3A35435871"
                }
              }
            },
            "field_resource_institution_leave": {
              "data": null,
              "links": {
                "related": {
--
          "type": "paragraph--program_individual",
          "id": "ccce8a23-4ce3-457f-922a-3d15a6a4f352",
          "links": {
            "self": {
              "href": "https://freida-admin.ama-assn.org/api/paragraph/program_individual/ccce8a23-4ce3-457f-922a-3d15a6a4f352?resourceVersion=id%3A2968396"
            }
          },
          "attributes": {
            "drupal_internal__id": 25346,
            "drupal_internal__revision_id": 2968396,
            "langcode": "en",
            "status": true,
            "created": "2019-10-17T23:09:34+00:00",
            "parent_id": "56176",
            "parent_type": "node",
            "parent_field_name": "field_program_director",
            "behavior_settings": [],
            "default_langcode": true,
            "revision_translation_affected": true,
            "field_address": {
              "langcode": null,
              "country_code": "US",
              "administrative_area": "NY",
              "locality": "New York",
              "postal_code": "10016-6402",
              "address_line1": "Dept of Med NBV 16 N 26",
              "address_line2": "550 1st Ave",
              "organization": "New York University Langone Med Ctr"
            },
            "field_degrees": "MD",
            "field_email": "margaret.horlick@nyulangone.org",
--
          "type": "paragraph--program_individual",
          "id": "22dd9d35-31b0-4fbd-b565-4ae6ef0c5a98",
          "links": {
            "self": {
              "href": "https://freida-admin.ama-assn.org/api/paragraph/program_individual/22dd9d35-31b0-4fbd-b565-4ae6ef0c5a98?resourceVersion=id%3A2949296"
            }
          },
          "attributes": {
            "drupal_internal__id": 25351,
            "drupal_internal__revision_id": 2949296,
            "langcode": "en",
            "status": true,
            "created": "2019-10-17T23:09:34+00:00",
            "parent_id": "56176",
            "parent_type": "node",
            "parent_field_name": "field_program_contact",
            "behavior_settings": [],
            "default_langcode": true,
            "revision_translation_affected": true,
            "field_address": {
              "langcode": null,
              "country_code": "US",
              "administrative_area": "NY",
              "locality": "New York",
              "postal_code": "10016",
              "address_line1": "Dept of Med NBV 16 N 30",
              "address_line2": "550 First Ave",
              "organization": "New York Univ Grossman Sch of Med"
            },
            "field_degrees": "BA",
            "field_email": "jared.ericksen@nyulangone.org",
                "type": "paragraph--program_individual",
                "id": "3564bb8c-98d4-4cf1-8ce1-9706de8a6863",
                "meta": {
                  "target_revision_id": 2995581,
                  "drupal_internal__target_id": 23901
                }
              },
              "links": {
                "related": {
                  "href": "https://freida-admin.ama-assn.org/api/node/survey_2024/8c3aadd1-278f-481f-8c76-2de05a797a05/field_program_contact?resourceVersion=id%3A35562181"
                },
                "self": {
                  "href": "https://freida-admin.ama-assn.org/api/node/survey_2024/8c3aadd1-278f-481f-8c76-2de05a797a05/relationships/field_program_contact?resourceVersion=id%3A35562181"
                }
              }
            },
            "field_program_director": {
              "data": {
                "type": "paragraph--program_individual",
                "id": "ff277f47-99c7-4ac8-8cec-8030f54ea949",
                "meta": {
                  "target_revision_id": 2979171,
                  "drupal_internal__target_id": 23896
                }
              },
              "links": {
                "related": {
                  "href": "https://freida-admin.ama-assn.org/api/node/survey_2024/8c3aadd1-278f-481f-8c76-2de05a797a05/field_program_director?resourceVersion=id%3A35562181"
                },
                "self": {
                  "href": "https://freida-admin.ama-assn.org/api/node/survey_2024/8c3aadd1-278f-481f-8c76-2de05a797a05/relationships/field_program_director?resourceVersion=id%3A35562181"
                }
              }
            },
            "field_resource_gallery_images": {
              "data": [],
              "links": {
                "related": {
                  "href": "https://freida-admin.ama-assn.org/api/node/survey_2024/8c3aadd1-278f-481f-8c76-2de05a797a05/field_resource_gallery_images?resourceVersion=id%3A35562181"
                },
                "self": {
                  "href": "https://freida-admin.ama-assn.org/api/node/survey_2024/8c3aadd1-278f-481f-8c76-2de05a797a05/relationships/field_resource_gallery_images?resourceVersion=id%3A35562181"
                }
              }
            },
            "field_resource_institution_leave": {
              "data": null,
              "links": {
                "related": {
--
          "type": "paragraph--program_individual",
          "id": "ff277f47-99c7-4ac8-8cec-8030f54ea949",
          "links": {
            "self": {
              "href": "https://freida-admin.ama-assn.org/api/paragraph/program_individual/ff277f47-99c7-4ac8-8cec-8030f54ea949?resourceVersion=id%3A2979171"
            }
          },
          "attributes": {
            "drupal_internal__id": 23896,
            "drupal_internal__revision_id": 2979171,
            "langcode": "en",
            "status": true,
            "created": "2019-10-17T23:09:34+00:00",
            "parent_id": "55451",
            "parent_type": "node",
            "parent_field_name": "field_program_director",
            "behavior_settings": [],
            "default_langcode": true,
            "revision_translation_affected": true,
            "field_address": {
              "langcode": null,
              "country_code": "US",
              "administrative_area": "MA",
              "locality": "Boston",
              "postal_code": "02114-2621",
              "address_line1": "Bigelow/746/Medicine",
              "address_line2": "55 Fruit St",
              "organization": "Massachusetts General Hospital"
            },
            "field_degrees": "MD, MPH",
            "field_email": "mghimresidency@partners.org",
--
          "type": "paragraph--program_individual",
          "id": "3564bb8c-98d4-4cf1-8ce1-9706de8a6863",
          "links": {
            "self": {
              "href": "https://freida-admin.ama-assn.org/api/paragraph/program_individual/3564bb8c-98d4-4cf1-8ce1-9706de8a6863?resourceVersion=id%3A2995581"
            }
          },
          "attributes": {
            "drupal_internal__id": 23901,
            "drupal_internal__revision_id": 2995581,
            "langcode": "en",
            "status": true,
            "created": "2019-10-17T23:09:34+00:00",
            "parent_id": "55451",
            "parent_type": "node",
            "parent_field_name": "field_program_contact",
            "behavior_settings": [],
            "default_langcode": true,
            "revision_translation_affected": true,
            "field_address": {
              "langcode": null,
              "country_code": "US",
              "administrative_area": "MA",
              "locality": "Boston",
              "postal_code": "02114",
              "address_line1": "Med Services Bigelow 730",
              "address_line2": "55 Fruit St",
              "organization": "Massachusetts General Hosp"
            },
            "field_degrees": null,
            "field_email": "mghimresidency@partners.org",

```
