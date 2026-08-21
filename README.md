# Multi_chat — 25 Mangaluru hotel RAG demos

Each hotel folder is independently runnable. The corpus uses official website pages when an official URL was available, and otherwise includes a clearly labeled verification-needed corpus based only on the supplied lead report.

| Folder | Hotel / segment | Website scraped | Chunks | Status |
|---|---|---:|---:|---|
| `goldfinch_hotel_mangaluru` | Goldfinch Hotel Mangaluru | yes | 14 | official pages bundled |
| `the_ocean_pearl` | The Ocean Pearl | yes | 15 | official pages bundled |
| `hotel_deepa_comforts` | Hotel Deepa Comforts | yes | 9 | official pages bundled |
| `hotel_srinivas` | Hotel Srinivas | yes | 9 | official pages bundled |
| `summer_sands_beach_resort` | Summer Sands Beach Resort | yes | 9 | official pages bundled |
| `hotel_poonja_international` | Hotel Poonja International | yes | 8 | official pages bundled |
| `aj_grand_hotel` | AJ Grand Hotel | no | 2 | verify official URL |
| `vivanta_mangalore` | Vivanta Mangalore, Old Port Road | yes | 15 | official pages bundled |
| `hotel_sai_palace` | Hotel Sai Palace Mangalore | yes | 17 | official pages bundled |
| `ginger_mangalore` | Ginger Mangalore | yes | 27 | official pages bundled |
| `hotel_moti_mahal` | Hotel Moti Mahal | no | 2 | verify official URL |
| `the_verda_saffron` | The Verda Saffron | no | 2 | verify official URL |
| `hotel_shoolin_comforts` | Hotel Shoolin Comforts / Shoolin Group | yes | 15 | official pages bundled |
| `royal_plaza_suites` | Royal Plaza Suites | no | 2 | verify official URL |
| `river_roost_resorts` | River Roost Resorts | no | 2 | verify official URL |
| `hotel_bms` | Hotel BMS | no | 2 | verify official URL |
| `hotel_janatha_deluxe` | Hotel Janatha Deluxe | no | 2 | verify official URL |
| `hotel_prestige_mangalore` | Hotel Prestige, Mangaluru | no | 2 | verify official URL |
| `hotel_veenu_international` | Hotel Veenu International | no | 2 | verify official URL |
| `mangalore_international_hotel` | Mangalore International Hotel | no | 2 | verify official URL |
| `hotel_ak_international` | Hotel A.K. International | no | 2 | verify official URL |
| `inland_empire` | Inland Empire | no | 2 | verify official URL |
| `the_ocean_pearl_inn_bejai` | The Ocean Pearl Inn, Bejai | yes | 13 | official pages bundled |
| `mangaluru_convention_banquet_operators` | Mangaluru Convention & Banquet Operators | no | 2 | verify official URL |
| `corporate_airport_corridor_hotels` | Corporate & Airport-Corridor Business Hotels | no | 2 | verify official URL |

## Run a demo
```bash
cd hotel_deepa_comforts
pip install -r requirements.txt
python3 -m http.server 8080 --directory web
```

Set `LLM_PROVIDER=openai-compatible` and `LLM_MODEL=<your-model>` only when you want to use a compatible hosted LLM; the default extractive provider requires no LLM key.

