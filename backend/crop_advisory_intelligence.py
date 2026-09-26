"""
TerraMind Crop Advisory Intelligence Engine
===========================================
World-class agricultural advisory system providing comprehensive farm-level decision support:
1. Pest & Disease Doctor (Diagnostic Catalog with active chemical dosages, bio-control, and PHI)
2. Crop Stage-Wise Package of Practices (POP from seed to harvest with active stage tracking)
3. Smart Fertilizer & NPK Dosage Calculator (Acre/Bigha conversions, commercial bags, split timing, rain leaching alerts)
4. Agrochemical Spray Advisor (Delta-T, wind drift limits, rainfastness lead time, tank-mix compatibility)
5. Crop Water Requirement & Evapotranspiration (FAO-56 Hargreaves ET0, Kc, net irrigation requirement)
6. APMC Mandi Market Intelligence & Post-Harvest Storage Guide

Grounded in authoritative institutional sources:
- ICAR-NRRI (National Rice Research Institute) & BCKV Agromet
- ICAR-CPRI (Central Potato Research Institute) & BCKV Mohanpur
- ICAR-DRMR (Directorate of Rapeseed-Mustard Research)
- ICAR-CRIJAF (Central Research Institute for Jute and Allied Fibres)
- ICAR-IIHR & State Agromet (Govt. of West Bengal)
- CPCB & IMD Agromet Advisory Service (AAS)
"""

import math
from datetime import date, datetime
from typing import Dict, Any, List, Optional

from backend.phenology_engine import get_crop_phenology


# ============================================================
# 1. PEST & DISEASE DIAGNOSTIC CATALOG
# ============================================================

PEST_AND_DISEASE_DB: Dict[str, List[Dict[str, Any]]] = {
    "paddy": [
        {
            "id": "paddy_blast",
            "name": "Rice Blast (Pyricularia oryzae)",
            "type": "Fungal Disease",
            "symptoms": [
                "Spindle-shaped elliptical lesions with brown borders and grey/ash centers on leaf blades",
                "Dark brown lesions at neck node causing panicle breakage (Neck Blast)",
                "Chaffy or unfilled grains with black discoloration",
            ],
            "visual_tags": ["Spindle lesions", "Neck breakage", "Grey centers", "Leaf spots"],
            "weather_triggers": "Persistent RH >85%, temperatures between 20°C and 28°C, cloudy skies with light drizzles.",
            "chemical_control": {
                "active_ingredient": "Tricyclazole 75% WP or Isoprothiolane 40% EC",
                "dilution_per_liter": "0.6 g / L (Tricyclazole) or 1.5 ml / L (Isoprothiolane)",
                "acre_dosage": "120 g / acre in 200 L water",
                "phi_days": 30,
            },
            "biological_control": "Spray Pseudomonas fluorescens @ 5 g/L of water or apply Trichoderma viride enriched FYM @ 50 kg/acre.",
            "cultural_prevention": "Avoid excessive nitrogenous fertilizer application. Drain ponded water temporarily during cloudy spells.",
            "source": "ICAR-NRRI Cuttack & BCKV Mohanpur",
            "severity": "High",
        },
        {
            "id": "paddy_sheath_blight",
            "name": "Sheath Blight (Rhizoctonia solani)",
            "type": "Fungal Disease",
            "symptoms": [
                "Oval, water-soaked greyish-green lesions on leaf sheaths near water line",
                "Lesions enlarge with irregular dark reddish-brown borders (snake-skin appearance)",
                "In severe infection, lesions reach the flag leaf causing lodging and premature drying",
            ],
            "visual_tags": ["Snake-skin spots", "Water-soaked lesions", "Sheath drying", "Stem rot"],
            "weather_triggers": "High temperatures (28-32°C), high humidity (>85%), dense plant canopy and stagnant water.",
            "chemical_control": {
                "active_ingredient": "Hexaconazole 5% EC or Validamycin 3% L",
                "dilution_per_liter": "2.0 ml / L (Hexaconazole) or 2.5 ml / L (Validamycin)",
                "acre_dosage": "400 ml / acre in 200 L water",
                "phi_days": 21,
            },
            "biological_control": "Foliar spray of Trichoderma harzianum @ 5 g/L at early tillering stage.",
            "cultural_prevention": "Ensure optimum planting spacing (20cm x 15cm). Keep bunds weed-free.",
            "source": "ICAR-NRRI & BCKV Agromet Field Unit",
            "severity": "High",
        },
        {
            "id": "paddy_stem_borer",
            "name": "Yellow Stem Borer (Scirpophaga incertulas)",
            "type": "Insect Pest",
            "symptoms": [
                "Drying of central tiller shoot forming 'Dead Heart' during vegetative stage",
                "Emerged panicles dry and turn completely white forming 'White Earhead' at reproductive stage",
                "Tiny pinholes with frass visible at the base of the stem",
            ],
            "visual_tags": ["Dead heart", "White earhead", "Stem holes", "Caterpillar frass"],
            "weather_triggers": "Warm humid weather (25-30°C) with low nocturnal wind speed and light rains.",
            "chemical_control": {
                "active_ingredient": "Chlorantraniliprole 18.5% SC or Cartap Hydrochloride 50% SP",
                "dilution_per_liter": "0.3 ml / L (Chlorantraniliprole) or 1.5 g / L (Cartap)",
                "acre_dosage": "60 ml / acre in 200 L water",
                "phi_days": 28,
            },
            "biological_control": "Install pheromone traps with Scirpo-lure @ 8 traps/acre. Release Trichogramma japonicum egg parasitoids @ 20,000/acre.",
            "cultural_prevention": "Clip seedling tips before transplanting to eliminate egg masses.",
            "source": "ICAR-NRRI & Directorate of Agriculture (GoWB)",
            "severity": "Critical",
        },
        {
            "id": "paddy_brown_planthopper",
            "name": "Brown Plant Hopper / BPH (Nilaparvata lugens)",
            "type": "Insect Pest",
            "symptoms": [
                "Circular patches of yellowing and drying plants known as 'Hopper Burn'",
                "Large clusters of brownish nymphs and adults congregating at the base of tillers above water level",
                "Sooty mold growth on honey-dew excreted at plant base",
            ],
            "visual_tags": ["Hopper burn", "Yellowing patches", "Stem clustering", "Honey dew"],
            "weather_triggers": "Continuous cloudy weather, high humidity (>90%), warm temperatures (28-32°C), and stagnant micro-climate.",
            "chemical_control": {
                "active_ingredient": "Trifflumezopyrim 10% SC or Pymetrozine 50% WG",
                "dilution_per_liter": "0.5 ml / L (Trifflumezopyrim) or 0.6 g / L (Pymetrozine)",
                "acre_dosage": "94 ml / acre directed at the base of plants",
                "phi_days": 21,
            },
            "biological_control": "Conserve predatory mirid bugs and spiders. Avoid synthetic pyrethroids which cause BPH resurgence.",
            "cultural_prevention": "Alternate wetting and drying (AWD) irrigation; create 30cm alleyways every 2 meters for aeration.",
            "source": "ICAR-NRRI Cuttack",
            "severity": "Critical",
        },
    ],
    "potato": [
        {
            "id": "potato_late_blight",
            "name": "Late Blight (Phytophthora infestans)",
            "type": "Fungal Oomycete",
            "symptoms": [
                "Water-soaked irregular pale to dark green lesions at leaf tips and margins",
                "White cottony mildew growth visible on the lower leaf surface in early morning",
                "Rapid purplish-brown blighting of entire foliage within 48-72 hours; foul rotting odor",
            ],
            "visual_tags": ["Water-soaked spots", "White leaf underside", "Black foliage blight", "Tuber rot"],
            "weather_triggers": "Smith Period: Night temp 10-15°C, day temp <22°C, relative humidity >85% for 48 consecutive hours, dense fog.",
            "chemical_control": {
                "active_ingredient": "Prophylactic: Mancozeb 75% WP | Curative: Cymoxanil 8% + Mancozeb 64% WP or Dimethomorph 50% WP",
                "dilution_per_liter": "2.5 g / L (Mancozeb) or 2.0 g / L (Cymoxanil + Mancozeb)",
                "acre_dosage": "600 g / acre in 250 L water",
                "phi_days": 14,
            },
            "biological_control": "Prophylactic spray of Trichoderma harzianum @ 5 g/L with sticker before canopy closure.",
            "cultural_prevention": "Proper earthing-up to prevent spore wash into tuber beds. Destroy infected haulms 10 days before harvest.",
            "source": "ICAR-CPRI Shimla & BCKV Kalyani",
            "severity": "Critical",
        },
        {
            "id": "potato_early_blight",
            "name": "Early Blight (Alternaria solani)",
            "type": "Fungal Disease",
            "symptoms": [
                "Concentric rings on older leaves forming 'target board' lesions",
                "Brown angular spots surrounded by narrow chlorotic yellow halos",
                "Premature defoliation of lower leaves progressing upward",
            ],
            "visual_tags": ["Target board spots", "Concentric rings", "Yellow halos", "Lower leaf drop"],
            "weather_triggers": "Alternating wet and dry periods, warm temperatures (24-30°C) with morning dew.",
            "chemical_control": {
                "active_ingredient": "Chlorothalonil 75% WP or Azoxystrobin 23% SC",
                "dilution_per_liter": "2.0 g / L (Chlorothalonil) or 1.0 ml / L (Azoxystrobin)",
                "acre_dosage": "400 g / acre in 200 L water",
                "phi_days": 14,
            },
            "biological_control": "Foliar application of Bacillus subtilis @ 5 ml/L.",
            "cultural_prevention": "Maintain adequate crop nutrition (potassium and phosphorus); avoid drought stress.",
            "source": "ICAR-CPRI & BCKV Mohanpur",
            "severity": "Medium",
        },
        {
            "id": "potato_aphids",
            "name": "Potato Aphids (Myzus persicae)",
            "type": "Insect Vector",
            "symptoms": [
                "Clusters of tiny green/yellow wingless nymphs sucking sap on tender shoot tips and lower leaf surfaces",
                "Upward leaf curling and crinkling with stunted growth",
                "Transmission of viral degeneration (Potato Virus Y, Leaf Roll Virus)",
            ],
            "visual_tags": ["Curled leaves", "Sticky foliage", "Yellow dwarf", "Aphid clusters"],
            "weather_triggers": "Cool cloudy weather (15-20°C) with low wind velocity and zero rainfall.",
            "chemical_control": {
                "active_ingredient": "Imidacloprid 17.8% SL or Thiamethoxam 25% WG",
                "dilution_per_liter": "0.3 ml / L (Imidacloprid) or 0.4 g / L (Thiamethoxam)",
                "acre_dosage": "60 ml / acre in 200 L water",
                "phi_days": 21,
            },
            "biological_control": "Yellow sticky traps @ 15 traps/acre. Spray 5% Neem Seed Kernel Extract (NSKE) or Neem oil 1500 ppm @ 3 ml/L.",
            "cultural_prevention": "Dehaulming when aphid population exceeds critical threshold (>20 aphids / 100 compound leaves) in seed potato.",
            "source": "ICAR-CPRI & National Seed Corporation",
            "severity": "High",
        },
    ],
    "mustard": [
        {
            "id": "mustard_aphids",
            "name": "Mustard Aphids (Lipaphis erysimi)",
            "type": "Insect Pest",
            "symptoms": [
                "Dense colonies of tiny green-black aphids completely covering inflorescences, pods, and tender shoots",
                "Devitalized flowers fail to set pods (siliquae); pods become curled, shriveled, and empty",
                "Abundant honeydew causing black sooty mold over the entire canopy",
            ],
            "visual_tags": ["Colonies on flowers", "Empty pods", "Sooty mold", "Sticky shoots"],
            "weather_triggers": "Cloudy, calm weather with temperatures between 10°C and 20°C and RH >70%.",
            "chemical_control": {
                "active_ingredient": "Dimethoate 30% EC or Oxydemeton-methyl 25% EC",
                "dilution_per_liter": "1.7 ml / L (Dimethoate)",
                "acre_dosage": "350 ml / acre in 200 L water (spray in late afternoon to protect foraging honeybees)",
                "phi_days": 15,
            },
            "biological_control": "Conserve ladybird beetles (Coccinella septempunctata). Spray Verticillium lecanii @ 5 g/L.",
            "cultural_prevention": "Early sowing before October 25 avoids peak aphid incidence during flowering.",
            "source": "ICAR-DRMR Bharatpur & BCKV Nadia KVK",
            "severity": "Critical",
        },
        {
            "id": "mustard_white_rust",
            "name": "White Rust (Albugo candida)",
            "type": "Fungal Oomycete",
            "symptoms": [
                "Prominent white, raised pustules (blisters) on the underside of lower leaves",
                "Yellow chlorotic patches on corresponding upper leaf surfaces",
                "Severe systemic floral malformation ('Staghead' gall hypertrophy)",
            ],
            "visual_tags": ["White blisters", "Staghead galls", "Chlorotic patches", "Floral distortion"],
            "weather_triggers": "Moist cool weather (12-18°C) with heavy morning dew and fog.",
            "chemical_control": {
                "active_ingredient": "Metalaxyl 8% + Mancozeb 64% WP",
                "dilution_per_liter": "2.0 g / L",
                "acre_dosage": "400 g / acre in 200 L water",
                "phi_days": 21,
            },
            "biological_control": "Seed treatment with Trichoderma viride @ 6 g/kg seed before sowing.",
            "cultural_prevention": "Collect and burn staghead galls. Avoid late sowing.",
            "source": "ICAR-DRMR & BCKV Agromet",
            "severity": "High",
        },
    ],
    "jute": [
        {
            "id": "jute_stem_rot",
            "name": "Stem Rot & Macrophomina Blight (Macrophomina phaseolina)",
            "type": "Fungal Disease",
            "symptoms": [
                "Brownish-black necrotic lesions on stem near collar region or leaf nodes",
                "Shredding of stem bark exposing dark fibrous strands covered with black sclerotial dots",
                "Premature plant wilting and breakage at the lesion point",
            ],
            "visual_tags": ["Black stem lesions", "Shredded bark", "Sclerotia dots", "Stem breakage"],
            "weather_triggers": "Intermittent hot humid weather (30-35°C), waterlogged soil followed by dry spell.",
            "chemical_control": {
                "active_ingredient": "Carbendazim 50% WP or Mancozeb 75% WP",
                "dilution_per_liter": "1.5 g / L (Carbendazim) or 2.5 g / L (Mancozeb)",
                "acre_dosage": "300 g / acre in 200 L water",
                "phi_days": 21,
            },
            "biological_control": "Seed treatment with Trichoderma viride @ 5 g/kg seed and soil application with compost.",
            "cultural_prevention": "Ensure good field drainage. Apply potash @ 40 kg/ha to improve stem fiber resilience.",
            "source": "ICAR-CRIJAF Barrackpore",
            "severity": "High",
        },
        {
            "id": "jute_yellow_mite",
            "name": "Yellow Mite (Polyphagotarsonemus latus)",
            "type": "Acarine Pest",
            "symptoms": [
                "Downward curling and inverting of apical leaves (boat-shaped leaf curling)",
                "Coppery-bronze discoloration and brittle thickening of younger leaves",
                "Severe stunting of terminal apical shoot halting plant vertical elongation",
            ],
            "visual_tags": ["Boat-shaped curling", "Bronze leaves", "Terminal stunting", "Curled shoot tip"],
            "weather_triggers": "Dry, warm pre-monsoon weather (30-36°C) with low relative humidity.",
            "chemical_control": {
                "active_ingredient": "Spiromesifen 22.9% SC or Wettable Sulphur 80% WP",
                "dilution_per_liter": "0.7 ml / L (Spiromesifen) or 3.0 g / L (Sulphur)",
                "acre_dosage": "150 ml / acre in 200 L water",
                "phi_days": 14,
            },
            "biological_control": "Conserve predatory phytoseiid mites. Spray 5% neem extract.",
            "cultural_prevention": "Provide light irrigation during prolonged dry spells to raise canopy relative humidity.",
            "source": "ICAR-CRIJAF Barrackpore",
            "severity": "High",
        },
    ],
    "vegetables": [
        {
            "id": "veg_damping_off",
            "name": "Nursery Damping Off (Pythium / Rhizoctonia)",
            "type": "Fungal Complex",
            "symptoms": [
                "Water-soaked collar constriction at soil line causing seedlings to collapse and topple over",
                "Failure of germinated seeds to emerge (pre-emergence damping off)",
            ],
            "visual_tags": ["Collapsing seedlings", "Water-soaked collar", "Rotting nursery", "Seedling wilt"],
            "weather_triggers": "Excessive soil moisture, poor drainage, high humidity (>90%), and overcast days.",
            "chemical_control": {
                "active_ingredient": "Copper Oxychloride 50% WP or Metalaxyl 35% WS",
                "dilution_per_liter": "2.5 g / L (Copper Oxychloride)",
                "acre_dosage": "Soil drench nursery bed @ 3-5 L solution / m²",
                "phi_days": 14,
            },
            "biological_control": "Treat raised nursery beds with Trichoderma viride @ 25 g/m² mixed with vermicompost.",
            "cultural_prevention": "Prepare 15cm raised nursery seedbeds with sand-soil mix to ensure instantaneous drainage.",
            "source": "ICAR-IIHR & State Agromet (GoWB)",
            "severity": "High",
        },
        {
            "id": "veg_fruit_borer",
            "name": "Fruit and Shoot Borer (Helicoverpa / Leucinodes)",
            "type": "Insect Pest",
            "symptoms": [
                "Wilting and dropping of terminal shoots in brinjal/tomato/chili",
                "Circular bore holes in fruits plugged with caterpillar excreta",
                "Internal rotting of developing fruits rendering produce unmarketable",
            ],
            "visual_tags": ["Bore holes in fruit", "Wilted shoots", "Fruit rot", "Caterpillar damage"],
            "weather_triggers": "Warm temperatures (24-32°C) with sporadic rain showers.",
            "chemical_control": {
                "active_ingredient": "Emamectin Benzoate 5% SG or Spinosad 45% SC",
                "dilution_per_liter": "0.4 g / L (Emamectin) or 0.3 ml / L (Spinosad)",
                "acre_dosage": "80 g / acre in 200 L water",
                "phi_days": 3,
            },
            "biological_control": "Install pheromone traps with Lucilure / Helilure @ 10 traps/acre. Release Trichogramma chilonis.",
            "cultural_prevention": "Collect and destroy all bore-damaged fruits and shoots twice a week.",
            "source": "ICAR-IIHR & BCKV Directorate of Research",
            "severity": "Critical",
        },
    ],
}


# ============================================================
# 2. STAGE-WISE PACKAGE OF PRACTICES (POP)
# ============================================================

POP_CATALOG: Dict[str, List[Dict[str, Any]]] = {
    "paddy": [
        {
            "stage_id": "nursery",
            "stage_name": "Nursery & Seedling Raising",
            "duration_days": "Days 0 – 25",
            "ideal_gdd": "0 – 250 GDD",
            "key_operations": [
                "Seed selection using salt solution (sp. gr. 1.06) to discard floating unfilled seeds",
                "Seed treatment with Carbendazim 50% WP @ 2 g/kg seed or Trichoderma viride @ 5 g/kg seed",
                "Nursery seed rate: 16–20 kg/acre for Aman paddy; sow in raised beds with 5cm channels",
            ],
            "water_management": "Keep soil moist but not inundated for the first 5 days; maintain 2cm water depth after 7 days.",
            "nutrient_advice": "Apply 10 kg DAP and 5 kg MOP per 10 decimals of nursery bed as basal.",
            "pest_scouting": "Inspect for thrips and seedling blast. Clip tip leaves before pulling seedlings.",
        },
        {
            "stage_id": "transplanting_tillering",
            "stage_name": "Transplanting & Active Tillering",
            "duration_days": "Days 25 – 60",
            "ideal_gdd": "250 – 650 GDD",
            "key_operations": [
                "Transplant 21-25 day old seedlings at 2-3 seedlings per hill",
                "Spacing: 20 cm x 15 cm row-to-row and hill-to-hill distance",
                "Cono-weeding or hand weeding at 20 and 40 days after transplanting (DAT)",
            ],
            "water_management": "Maintain shallow water depth of 2–3 cm to encourage active tiller initiation.",
            "nutrient_advice": "Apply 1st top dressing: 25% Urea (20 kg/acre) + Zinc Sulphate @ 5 kg/acre at active tillering (21 DAT).",
            "pest_scouting": "Scout for Yellow Stem Borer (dead hearts) and Sheath Blight lesions along water line.",
        },
        {
            "stage_id": "panicle_flowering",
            "stage_name": "Panicle Initiation & Flowering",
            "duration_days": "Days 60 – 95",
            "ideal_gdd": "650 – 1150 GDD",
            "key_operations": [
                "2nd top dressing of nitrogenous fertilizer at panicle initiation",
                "Foliar spray of water-soluble Boron (20%) @ 1 g/L to improve pollen fertility and grain setting",
                "Strict avoidance of agrochemical spraying during peak anthesis (9:00 AM – 11:30 AM)",
            ],
            "water_management": "Critical moisture stage: maintain 5 cm standing water. Water stress at flowering causes up to 50% spikelet sterility.",
            "nutrient_advice": "Apply remaining 25% Urea (20 kg/acre) + 10 kg MOP per acre at panicle emergence.",
            "pest_scouting": "Monitor for Rice Blast, Neck Blast, and Brown Plant Hopper (BPH) at tiller base.",
        },
        {
            "stage_id": "maturity_harvest",
            "stage_name": "Grain Filling, Maturity & Harvest",
            "duration_days": "Days 95 – 130",
            "ideal_gdd": "1150 – 1600 GDD",
            "key_operations": [
                "Drain water from field completely 10-14 days before expected harvest date",
                "Harvest when 85% of panicles turn golden yellow and grain moisture is ~20%",
                "Sun dry harvested paddy on clean threshing floor to 12-14% moisture before storage",
            ],
            "water_management": "Complete terminal drainage to hasten uniform ripening and facilitate mechanical harvesting.",
            "nutrient_advice": "Zero fertilizer application. No pesticide spraying within 20 days of harvest.",
            "pest_scouting": "Check for ear-cutting caterpillars and post-rain grain discoloration.",
        },
    ],
    "potato": [
        {
            "stage_id": "seed_tuber_planting",
            "stage_name": "Seed Preparation & Tuber Planting",
            "duration_days": "Days 0 – 20",
            "ideal_gdd": "0 – 200 GDD",
            "key_operations": [
                "Procure certified whole tubers (40-50g size) pre-sprouted with 1cm sturdy green sprouts",
                "Seed treatment: Dip tubers in Mancozeb 75% WP @ 2.5 g/L for 10 minutes; shade dry",
                "Planting geometry: Ridge-and-furrow method with 60 cm row-to-row and 20 cm tuber spacing",
            ],
            "water_management": "Plant in moist soil. First light irrigation 5-7 days after planting when sprout emergence begins.",
            "nutrient_advice": "Apply full DAP, full Potash, and 50% Urea as basal placement in furrows 5cm below tubers.",
            "pest_scouting": "Inspect for cutworms and bacterial soft rot in seed tubers.",
        },
        {
            "stage_id": "vegetative_earthing",
            "stage_name": "Vegetative Growth & Earthing-Up",
            "duration_days": "Days 20 – 45",
            "ideal_gdd": "200 – 500 GDD",
            "key_operations": [
                "First intercultural hoeing and weeding at 20-25 days after planting (DAP)",
                "Earthing-up operation at 30 DAP to build high, loose soil ridges preventing tuber greening (solanine)",
                "Foliar spray of Mancozeb 75% WP @ 2.5 g/L as prophylactic barrier against Late Blight",
            ],
            "water_management": "Furrow irrigation every 8-10 days ensuring water does not submerge ridge tops.",
            "nutrient_advice": "Top dress remaining 50% Urea (40 kg/acre) just prior to earthing-up.",
            "pest_scouting": "Monitor lower leaves daily for Smith Period conditions (fog, high humidity, water-soaked blight spots).",
        },
        {
            "stage_id": "tuber_bulking",
            "stage_name": "Tuber Bulking & Tuberization",
            "duration_days": "Days 45 – 80",
            "ideal_gdd": "500 – 850 GDD",
            "key_operations": [
                "Peak tuber expansion phase: foliar spray of Potassium Nitrate (13:0:45) @ 5 g/L at 55 and 70 DAP",
                "Maintain continuous Late Blight fungicidal cover spray at 7-10 day intervals",
                "Scout for aphid buildup using yellow sticky traps (threshold >20 aphids / 100 leaves)",
            ],
            "water_management": "Even moisture is critical: fluctuating soil moisture causes tuber cracking and knobbiness.",
            "nutrient_advice": "Foliar micronutrient spray (Zinc + Boron @ 1 g/L) to prevent hollow heart.",
            "pest_scouting": "Curative spray with Cymoxanil + Mancozeb if Late Blight lesions are detected in neighborhood.",
        },
        {
            "stage_id": "dehaulming_harvest",
            "stage_name": "Dehaulming & Harvest Curing",
            "duration_days": "Days 80 – 105",
            "ideal_gdd": "850 – 1100 GDD",
            "key_operations": [
                "Stop all irrigation 10-12 days before dehaulming",
                "Dehaulming: Cut or desiccate aerial foliage 10-12 days before digging to harden tuber skin (periderm)",
                "Harvest in dry, sunny weather; cure tubers in heap under straw for 8-10 days before cold storage",
            ],
            "water_management": "Dry soil is essential to prevent tuber peel damage and bacterial soft rotting during digging.",
            "nutrient_advice": "No fertilizer. Never expose harvested tubers to direct midday sunlight.",
            "pest_scouting": "Grade out all cut, bruised, or blighted tubers prior to bagging.",
        },
    ],
    "mustard": [
        {
            "stage_id": "sowing_seedling",
            "stage_name": "Sowing & Early Vegetative",
            "duration_days": "Days 0 – 30",
            "ideal_gdd": "0 – 350 GDD",
            "key_operations": [
                "Optimal sowing window: October 15 – November 5 in West Bengal",
                "Seed rate: 1.5–2.0 kg/acre; mix with dry sand for uniform shallow placement (2-3 cm depth)",
                "Thinning operation at 15-20 DAS to maintain plant-to-plant distance of 10-15 cm",
            ],
            "water_management": "First light irrigation at 25-30 DAS (rosette stage) accompanied by intercultural weeding.",
            "nutrient_advice": "Apply full P, full K, and 50% N along with Sulphur (Bentonite Sulphur @ 10 kg/acre) as basal.",
            "pest_scouting": "Watch for flea beetle and early seedling damping off.",
        },
        {
            "stage_id": "flowering_pod",
            "stage_name": "Flowering & Siliquae Formation",
            "duration_days": "Days 30 – 75",
            "ideal_gdd": "350 – 750 GDD",
            "key_operations": [
                "Crucial stage: avoid drought stress during peak flowering and pod enlargement",
                "2nd top dressing with remaining 50% Urea (20 kg/acre) just before pre-flowering irrigation",
                "Foliar spray of Dimethoate 30% EC in late evening if mustard aphid colonies appear on inflorescences",
            ],
            "water_management": "Second irrigation at siliquae development stage (55-60 DAS). Avoid irrigation during windy spells to prevent lodging.",
            "nutrient_advice": "Foliar spray of Borax @ 1 g/L at early flowering enhances oil content and pod filling.",
            "pest_scouting": "Monitor aphid index and white rust stagheads.",
        },
        {
            "stage_id": "ripening_harvest",
            "stage_name": "Siliquae Ripening & Threshing",
            "duration_days": "Days 75 – 105",
            "ideal_gdd": "750 – 1050 GDD",
            "key_operations": [
                "Harvest when 75% of siliquae turn yellowish-brown to avoid seed shattering loss",
                "Harvest early in the morning when morning moisture prevents pod shattering",
                "Dry sheaves in sun for 4-5 days; thresh and dry seed to <8% moisture for safe oil storage",
            ],
            "water_management": "No water. Keep field completely dry during maturity.",
            "nutrient_advice": "Zero application.",
            "pest_scouting": "Inspect for storage fungal mold if seeds are bagged damp.",
        },
    ],
    "jute": [
        {
            "stage_id": "sowing_emergence",
            "stage_name": "Land Prep & Sowing",
            "duration_days": "Days 0 – 30",
            "ideal_gdd": "0 – 300 GDD",
            "key_operations": [
                "Fine tilth preparation with 4-5 ploughings and application of well-decomposed FYM @ 2 tonnes/acre",
                "Line sowing using seed drill at 25-30 cm row spacing; seed rate 2.5 kg/acre (Capsularis) or 2 kg/acre (Olitorius)",
                "Pre-emergence weed control with Pretilachlor 50% EC @ 3 ml/L within 48 hours of sowing",
            ],
            "water_management": "Ensure adequate soil moisture at sowing. Provide light life-saving irrigation during summer dry spells.",
            "nutrient_advice": "Basal application of N:P:K @ 20:20:20 kg/acre with additional 10 kg lime/bigha in acidic soils.",
            "pest_scouting": "Watch for seedling blight and flea beetle perforations.",
        },
        {
            "stage_id": "grand_growth",
            "stage_name": "Vegetative & Grand Growth",
            "duration_days": "Days 30 – 100",
            "ideal_gdd": "300 – 1200 GDD",
            "key_operations": [
                "First thinning and hand weeding at 15-20 DAS; second thinning at 30-35 DAS to 5-7 cm plant spacing",
                "Top dressing with Urea in 2 equal splits at 30 and 45 DAS",
                "Inspect apical shoots for Yellow Mite curling and hairy caterpillar infestations",
            ],
            "water_management": "Jute tolerates heavy monsoon rain but cannot tolerate stagnant water before 60 days of age.",
            "nutrient_advice": "Apply 15 kg Urea/acre after weeding followed by soil hoeing.",
            "pest_scouting": "Foliar spray of Spiromesifen @ 0.7 ml/L if yellow mite causes downward leaf curling.",
        },
        {
            "stage_id": "harvest_retting",
            "stage_name": "Harvest, Retting & Fiber Extraction",
            "duration_days": "Days 100 – 130",
            "ideal_gdd": "1200 – 1600 GDD",
            "key_operations": [
                "Ideal harvest stage: Small pod formation stage (110-120 DAS) yields optimum quality and quantity of golden fiber",
                "Defoliate harvested bundles in field for 3-4 days before submerging in slow-moving clean water retting pond",
                "Use microbial retting consortia (CRIJAF Sona @ 4 kg/tonne) to shorten retting to 10-12 days and produce bright fiber",
            ],
            "water_management": "Bundle submergence under 10 cm water using cement blocks or aquatic plants (never use soil/mud which discolors fiber).",
            "nutrient_advice": "Zero application.",
            "pest_scouting": "Check retting progress daily by stripping sample fiber from the collar.",
        },
    ],
    "vegetables": [
        {
            "stage_id": "nursery_transplant",
            "stage_name": "Nursery & Transplanting",
            "duration_days": "Days 0 – 30",
            "ideal_gdd": "0 – 300 GDD",
            "key_operations": [
                "Raise seedlings on 15cm raised beds with solarized soil and nylon netting protection",
                "Transplant 25-30 day sturdy seedlings in evening hours; water immediately",
                "Dip seedling roots in Pseudomonas fluorescens @ 10 g/L for 20 minutes before transplanting",
            ],
            "water_management": "Provide daily light watering in nursery; furrow irrigation every 4-6 days after transplanting.",
            "nutrient_advice": "Basal application of well-decomposed FYM @ 5 tonnes/acre + 25 kg DAP + 20 kg MOP.",
            "pest_scouting": "Protect against damping off and sucking pests (thrips, whiteflies).",
        },
        {
            "stage_id": "vegetative_growth",
            "stage_name": "Vegetative Growth & Trellising",
            "duration_days": "Days 30 – 55",
            "ideal_gdd": "300 – 650 GDD",
            "key_operations": [
                "Staking of plants using bamboo sticks or trellising for tomato, brinjal, and cucurbits",
                "First intercultural hoeing and weeding followed by earthing up",
                "Prune lower yellowing leaves and water suckers to improve aeration and light penetration",
            ],
            "water_management": "Maintain consistent furrow or drip irrigation every 5-7 days; avoid root flooding.",
            "nutrient_advice": "1st top dressing: Apply 15 kg Urea per acre followed by light hoeing.",
            "pest_scouting": "Inspect shoots for early borer wilting and whitefly vectors.",
        },
        {
            "stage_id": "fruiting_harvest",
            "stage_name": "Flowering, Fruiting & Continuous Picking",
            "duration_days": "Days 55 – 110",
            "ideal_gdd": "650 – 1200 GDD",
            "key_operations": [
                "Foliar spray of 19:19:19 (NPK water soluble) @ 5 g/L + micronutrients during active flowering",
                "Harvest mature, marketable fruits every 3-4 days in early morning hours to maintain freshness",
                "Grade fruits and pack in ventilated crates for mandi transport",
            ],
            "water_management": "Uniform moisture is critical; alternating drought and excess water causes fruit cracking.",
            "nutrient_advice": "Top dress 10 kg Urea per acre after every second flush of picking.",
            "pest_scouting": "Inspect for fruit borer holes, downy mildew spots, and leaf curl virus.",
        },
    ],
}


# ============================================================
# 3. SMART FERTILIZER & NPK DOSAGE CALCULATOR
# ============================================================

# Recommended Dose of Fertilizers (RDF) in kg N, P2O5, K2O per Hectare (BCKV Standards)
CROP_RDF_HA: Dict[str, Dict[str, float]] = {
    "paddy": {"n": 80.0, "p": 40.0, "k": 40.0},
    "potato": {"n": 150.0, "p": 100.0, "k": 100.0},
    "mustard": {"n": 60.0, "p": 30.0, "k": 30.0},
    "jute": {"n": 60.0, "p": 30.0, "k": 30.0},
    "vegetables": {"n": 100.0, "p": 50.0, "k": 50.0},
}


def calculate_fertilizer_dosage(
    crop: str,
    field_size: float = 1.0,
    unit: str = "acre",
    soil_type: str = "alluvial",
    rain_next_24h_mm: float = 0.0,
) -> Dict[str, Any]:
    """
    Computes exact commercial fertilizer quantities (Urea, DAP, SSP, MOP)
    based on agricultural land size in Acres, Bighas, or Hectares.
    Includes split timing, micronutrients, and rainfall leaching alerts.
    """
    crop_clean = (crop or "paddy").lower()
    rdf = CROP_RDF_HA.get(crop_clean, CROP_RDF_HA["paddy"])

    # Standard conversion:
    # 1 Hectare = 2.47105 Acres
    # 1 Acre = 3 Bighas (Standard West Bengal Bengal Bigha = 14,400 sq ft)
    field_val = max(0.1, float(field_size))
    unit_clean = (unit or "acre").lower()

    if unit_clean == "bigha":
        acres = field_val / 3.0
        hectares = acres / 2.47105
        display_unit = f"{field_val:.1f} Bigha ({acres:.2f} Acre)"
    elif unit_clean == "hectare" or unit_clean == "ha":
        hectares = field_val
        acres = field_val * 2.47105
        display_unit = f"{field_val:.2f} Hectare ({acres:.2f} Acre)"
    else:  # Acre default
        acres = field_val
        hectares = field_val / 2.47105
        display_unit = f"{field_val:.1f} Acre ({field_val * 3:.1f} Bigha)"

    # Nutrient requirements for the target field area in kg
    target_n = round(rdf["n"] * hectares, 1)
    target_p = round(rdf["p"] * hectares, 1)
    target_k = round(rdf["k"] * hectares, 1)

    # Conversion to commercial grade fertilizers:
    # Option 1: DAP (18% N, 46% P2O5) + Urea (46% N) + MOP (60% K2O)
    dap_kg = round(target_p / 0.46, 1)
    n_from_dap = dap_kg * 0.18
    remaining_n = max(0.0, target_n - n_from_dap)
    urea_kg = round(remaining_n / 0.46, 1)
    mop_kg = round(target_k / 0.60, 1)

    # Standard 45 kg commercial bag equivalents
    urea_bags = round(urea_kg / 45.0, 1)
    dap_bags = round(dap_kg / 50.0, 1)  # DAP standard bag is 50 kg
    mop_bags = round(mop_kg / 50.0, 1)  # MOP standard bag is 50 kg

    # Split Application Schedule
    if crop_clean == "paddy":
        splits = [
            {"timing": "Basal (At final puddling/transplanting)", "urea_kg": round(urea_kg * 0.25, 1), "dap_kg": dap_kg, "mop_kg": round(mop_kg * 0.5, 1), "notes": "Incorporate into mud"},
            {"timing": "1st Top Dressing (Active tillering, 21 DAT)", "urea_kg": round(urea_kg * 0.50, 1), "dap_kg": 0.0, "mop_kg": 0.0, "notes": "Broadcast in thin water film"},
            {"timing": "2nd Top Dressing (Panicle initiation, 45 DAT)", "urea_kg": round(urea_kg * 0.25, 1), "dap_kg": 0.0, "mop_kg": round(mop_kg * 0.5, 1), "notes": "Improves grain filling"},
        ]
        micronutrients = [
            {"name": "Zinc Sulphate (Heptahydrate 21%)", "dosage": f"{round(5.0 * acres, 1)} kg", "application": "Basal application to prevent Khaira disease"},
            {"name": "Solubor Boron (20%)", "dosage": f"{round(0.4 * acres, 1)} kg", "application": "Foliar spray @ 1 g/L at panicle emergence"},
        ]
    elif crop_clean == "potato":
        splits = [
            {"timing": "Basal (In furrows 5cm below seed tubers)", "urea_kg": round(urea_kg * 0.50, 1), "dap_kg": dap_kg, "mop_kg": mop_kg, "notes": "Cover with layer of soil"},
            {"timing": "Top Dressing (At earthing-up, 30 DAP)", "urea_kg": round(urea_kg * 0.50, 1), "dap_kg": 0.0, "mop_kg": 0.0, "notes": "Place between ridges and hill up"},
        ]
        micronutrients = [
            {"name": "Zinc Sulphate 21%", "dosage": f"{round(6.0 * acres, 1)} kg", "application": "Basal soil application"},
            {"name": "Borax (Sodium Tetraborate)", "dosage": f"{round(4.0 * acres, 1)} kg", "application": "Prevents internal tuber necrosis and hollow heart"},
        ]
    elif crop_clean == "mustard":
        splits = [
            {"timing": "Basal (At land preparation)", "urea_kg": round(urea_kg * 0.50, 1), "dap_kg": dap_kg, "mop_kg": mop_kg, "notes": "Include Sulphur"},
            {"timing": "Top Dressing (At rosette stage / 1st irrigation, 30 DAS)", "urea_kg": round(urea_kg * 0.50, 1), "dap_kg": 0.0, "mop_kg": 0.0, "notes": "Broadcast before irrigation"},
        ]
        micronutrients = [
            {"name": "Agricultural Bentonite Sulphur 90%", "dosage": f"{round(10.0 * acres, 1)} kg", "application": "Basal application; essential for mustard oil synthesis"},
            {"name": "Borax", "dosage": f"{round(2.0 * acres, 1)} kg", "application": "Prevents flower dropping"},
        ]
    else:
        splits = [
            {"timing": "Basal Application", "urea_kg": round(urea_kg * 0.50, 1), "dap_kg": dap_kg, "mop_kg": round(mop_kg * 0.5, 1), "notes": "Soil incorporation"},
            {"timing": "Top Dressing (Vegetative growth)", "urea_kg": round(urea_kg * 0.50, 1), "dap_kg": 0.0, "mop_kg": round(mop_kg * 0.5, 1), "notes": "After weeding"},
        ]
        micronutrients = [
            {"name": "Zinc Sulphate 21%", "dosage": f"{round(4.0 * acres, 1)} kg", "application": "Basal soil application"},
        ]

    # Weather constraint alert
    leaching_risk = rain_next_24h_mm >= 10.0
    if leaching_risk:
        leaching_alert = (
            f"⚠️ HIGH NITROGEN LEACHING RISK: {rain_next_24h_mm:.1f} mm rain expected in next 24 hours. "
            "POSTPONE all urea / nitrogen broadcasting until the field drains and dry weather returns. "
            "Broadcasting nitrogen in heavy rain causes 60-80% loss into runoff and ground drainage."
        )
    else:
        leaching_alert = "✓ Low Leaching Risk: Weather is favorable for scheduled basal and top dressing operations."

    return {
        "crop": crop_clean,
        "field_size_input": field_val,
        "unit": unit_clean,
        "display_area": display_unit,
        "hectares": round(hectares, 3),
        "acres": round(acres, 2),
        "nutrients_required_kg": {
            "nitrogen_n": target_n,
            "phosphorus_p2o5": target_p,
            "potassium_k2o": target_k,
        },
        "commercial_fertilizers": [
            {"name": "Urea (46% N)", "quantity_kg": urea_kg, "bags_approx": urea_bags, "bag_spec": "45 kg bag", "color": "#0ea5e9"},
            {"name": "DAP (18% N, 46% P2O5)", "quantity_kg": dap_kg, "bags_approx": dap_bags, "bag_spec": "50 kg bag", "color": "#10b981"},
            {"name": "MOP (60% K2O)", "quantity_kg": mop_kg, "bags_approx": mop_bags, "bag_spec": "50 kg bag", "color": "#f59e0b"},
        ],
        "split_schedule": splits,
        "micronutrients": micronutrients,
        "leaching_risk": leaching_risk,
        "leaching_alert": leaching_alert,
        "source": "Bidhan Chandra Krishi Viswavidyalaya (BCKV) RDF Standards",
    }


# ============================================================
# 4. AGROCHEMICAL SPRAY ADVISOR & TANK-MIX MATRIX
# ============================================================

def evaluate_spray_suitability(
    temp_c: float = 30.0,
    humidity_pct: float = 75.0,
    wind_kmh: float = 12.0,
    rain_prob: float = 0.3,
    rain_mm_24h: float = 2.0,
    dew_point_c: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Evaluates real-time agrochemical spray suitability index (Optimal / Caution / Unfavorable)
    incorporating Delta-T (dew point depression), wind drift threshold, and chemical rainfastness.
    """
    t = float(temp_c)
    rh = float(humidity_pct)
    w = float(wind_kmh)
    rp = float(rain_prob)
    r24 = float(rain_mm_24h)

    # Compute dew point if not provided
    if dew_point_c is None:
        a = 17.27
        b = 237.7
        alpha = ((a * t) / (b + t)) + math.log(max(1.0, rh) / 100.0)
        dp = (b * alpha) / (a - alpha)
    else:
        dp = float(dew_point_c)

    # Delta-T = Ambient Temp - Dew Point
    delta_t = round(t - dp, 1)

    reasons: List[str] = []
    status = "Optimal"
    badge_color = "#10b981"
    score_pct = 95

    # 1. Rain & Rainfastness Check (Requires 3-4 hours dry lead time)
    if rp >= 0.70 or r24 >= 8.0:
        status = "Unfavorable"
        badge_color = "#ef4444"
        score_pct = 20
        reasons.append("High rain probability within next 12-24h will wash off pesticide deposits before plant uptake.")
    elif rp >= 0.40 or r24 >= 3.0:
        if status != "Unfavorable":
            status = "Caution"
            badge_color = "#f59e0b"
            score_pct = min(score_pct, 60)
        reasons.append("Moderate rain risk. Use an organosilicone surfactant/sticker to enhance rainfastness.")

    # 2. Wind Drift Check (Optimal: 3-12 km/h; >15 km/h causes drift; <3 km/h risks thermal inversion)
    if w > 16.0:
        status = "Unfavorable"
        badge_color = "#ef4444"
        score_pct = min(score_pct, 25)
        reasons.append(f"High wind speed ({w:.1f} km/h > 15 km/h) causes severe off-target droplet drift and uneven coverage.")
    elif w > 12.0:
        if status != "Unfavorable":
            status = "Caution"
            badge_color = "#f59e0b"
            score_pct = min(score_pct, 65)
        reasons.append(f"Moderate breeze ({w:.1f} km/h). Use low-drift air-induction nozzles and lower boom height.")
    elif w < 2.5:
        if status != "Unfavorable":
            status = "Caution"
            badge_color = "#f59e0b"
            score_pct = min(score_pct, 70)
        reasons.append("Very low wind speed (<3 km/h). Be cautious of nocturnal surface temperature inversion trapping fine mists.")

    # 3. Delta-T Evaporation Check (Optimal: 2°C - 8°C)
    if delta_t > 10.0:
        status = "Unfavorable"
        badge_color = "#ef4444"
        score_pct = min(score_pct, 30)
        reasons.append(f"High Delta-T ({delta_t}°C > 10°C). Air is too dry; spray droplets evaporate rapidly before contacting foliage.")
    elif delta_t > 8.0:
        if status != "Unfavorable":
            status = "Caution"
            badge_color = "#f59e0b"
            score_pct = min(score_pct, 65)
        reasons.append(f"Marginal Delta-T ({delta_t}°C). Spray only with coarse droplets during morning or late afternoon.")
    elif delta_t < 1.5:
        if status != "Unfavorable":
            status = "Caution"
            badge_color = "#f59e0b"
            score_pct = min(score_pct, 60)
        reasons.append(f"Very low Delta-T ({delta_t}°C < 2°C). High humidity delays droplet drying, causing wash-down or pesticide runoff.")

    if not reasons:
        reasons.append("Weather parameters are ideal for spray operations: excellent droplet retention, calm wind, and zero wash-off risk.")

    # Tank-mix compatibility matrix & protocol
    tank_mix_rules = [
        {"mix": "Fungicide (Mancozeb) + Insecticide (Imidacloprid)", "compatibility": "Compatible", "status_icon": "✓", "note": "Widely safe. Follow proper mixing order."},
        {"mix": "Copper Fungicide (COC) + Alkaline Insecticide (Dimethoate)", "compatibility": "Incompatible", "status_icon": "✗", "note": "Precipitates and reduces biological efficacy. Never mix together."},
        {"mix": "Foliar Micronutrient (Zinc/Boron) + Systemic Fungicide", "compatibility": "Compatible", "status_icon": "✓", "note": "Ensure water pH is between 6.0 and 7.0."},
        {"mix": "Fungicide + Urea Solution (1-2%)", "compatibility": "Compatible", "status_icon": "✓", "note": "Urea enhances stomatal absorption. Dissolve urea completely first."},
    ]

    return {
        "status": status,
        "score_pct": score_pct,
        "badge_color": badge_color,
        "delta_t_c": delta_t,
        "optimal_delta_t_range": "2.0°C – 8.0°C",
        "wind_speed_kmh": w,
        "optimal_wind_range": "3 – 12 km/h",
        "rainfast_window_hours": 4,
        "advisory_reasons": reasons,
        "best_spray_window_today": "07:00 AM – 10:00 AM or 03:30 PM – 05:30 PM",
        "tank_mixing_order_rule": "WALES Protocol: 1. Wettable Powders (WP/WDG) -> 2. Agitate thoroughly -> 3. Liquid Solutions (SC/SL) -> 4. Emulsifiable Concentrates (EC) -> 5. Surfactants/Stickers",
        "tank_mix_matrix": tank_mix_rules,
    }


# ============================================================
# 5. CROP WATER REQUIREMENT (ET0 & ETc) & IRRIGATION BUDGET
# ============================================================

# FAO-56 Crop Coefficients (Kc) for Growth Stages: [Initial, Mid-Season, Late-Season]
CROP_KC_VALUES: Dict[str, Dict[str, float]] = {
    "paddy": {"initial": 1.05, "mid": 1.25, "late": 0.95},
    "potato": {"initial": 0.50, "mid": 1.15, "late": 0.75},
    "mustard": {"initial": 0.35, "mid": 1.10, "late": 0.60},
    "jute": {"initial": 0.60, "mid": 1.15, "late": 0.85},
    "vegetables": {"initial": 0.60, "mid": 1.05, "late": 0.80},
}


def calculate_crop_water_balance(
    crop: str,
    stage_name: str = "vegetative",
    tmax: float = 32.0,
    tmin: float = 24.0,
    rh: float = 75.0,
    wind_kmh: float = 12.0,
    rain_mm: float = 5.0,
) -> Dict[str, Any]:
    """
    Computes Reference Evapotranspiration (ET0) using Hargreaves-Samani method
    and Crop Evapotranspiration (ETc = Kc * ET0) under FAO-56 standards.
    Deducts effective precipitation (Peff) to determine net irrigation requirement.
    """
    crop_clean = (crop or "paddy").lower()
    kc_dict = CROP_KC_VALUES.get(crop_clean, CROP_KC_VALUES["paddy"])

    st_lower = (stage_name or "vegetative").lower()
    if any(k in st_lower for k in ["nursery", "seed", "planting", "emergence"]):
        kc = kc_dict["initial"]
        stage_label = "Initial / Seedling"
    elif any(k in st_lower for k in ["harvest", "maturity", "ripening"]):
        kc = kc_dict["late"]
        stage_label = "Late / Maturity"
    else:
        kc = kc_dict["mid"]
        stage_label = "Mid-Season / Active Vegetative & Flowering"

    # Hargreaves-Samani approximation for Reference ET0 in mm/day
    # ET0 = 0.0023 * (Tmean + 17.8) * (Tmax - Tmin)^0.5 * Ra
    # For Bengal latitude ~23°N, extraterrestrial radiation Ra is ~15.2 mm/day
    tmean = (float(tmax) + float(tmin)) / 2.0
    tdiff = max(1.0, float(tmax) - float(tmin))
    et0 = round(0.0023 * (tmean + 17.8) * math.sqrt(tdiff) * 15.2, 1)

    # Crop Evapotranspiration ETc in mm/day
    etc = round(et0 * kc, 1)

    # Effective Rainfall (USDA SCS formula): Peff = Rain * 0.75 if Rain < 25mm, else Rain * 0.80
    r = float(rain_mm)
    if r <= 0.2:
        peff = 0.0
    elif r < 25.0:
        peff = round(r * 0.75, 1)
    else:
        peff = round(20.0 + (r - 25.0) * 0.50, 1)

    # Net Irrigation Water Requirement: I_req = max(0, ETc - Peff)
    net_irrigation_mm = round(max(0.0, etc - peff), 1)

    # Convert mm of water depth to volumetric units per Acre
    # 1 mm of water over 1 Acre = 4,046.86 Liters = 4.047 m³
    liters_per_acre = int(round(net_irrigation_mm * 4046.86))
    pump_hours_5hp = round(liters_per_acre / 35000.0, 1) if liters_per_acre > 0 else 0.0

    if net_irrigation_mm <= 0.0:
        status = "Rain Surplus (No Irrigation Required)"
        badge_color = "#10b981"
        action = f"Effective rain ({peff:.1f} mm) fully covers daily crop water needs ({etc:.1f} mm). Ensure field drainage channels are open."
    elif net_irrigation_mm <= 2.5:
        status = "Light Soil Moisture Deficit"
        badge_color = "#84cc16"
        action = "Soil moisture is nearly balanced. Delay irrigation by 24 hours to monitor next rainfall."
    elif net_irrigation_mm <= 5.0:
        status = "Moderate Crop Water Deficit"
        badge_color = "#f59e0b"
        action = f"Apply light irrigation of ~{net_irrigation_mm:.1f} mm depth (~{liters_per_acre:,} L/acre or ~{pump_hours_5hp} hrs 5HP pump run)."
    else:
        status = "High Evapotranspiration Deficit"
        badge_color = "#ef4444"
        action = f"Critical water stress zone: apply immediate irrigation of ~{net_irrigation_mm:.1f} mm depth to prevent yield decline."

    return {
        "crop": crop_clean,
        "growth_stage": stage_label,
        "crop_coefficient_kc": kc,
        "reference_et0_mm_day": et0,
        "crop_evapotranspiration_etc_mm_day": etc,
        "daily_rainfall_mm": r,
        "effective_precipitation_mm": peff,
        "net_irrigation_requirement_mm": net_irrigation_mm,
        "water_volume_liters_per_acre": liters_per_acre,
        "pump_run_hours_5hp": pump_hours_5hp,
        "irrigation_status": status,
        "badge_color": badge_color,
        "action_recommendation": action,
    }


# ============================================================
# 6. APMC MANDI MARKET INTELLIGENCE & STORAGE
# ============================================================

MANDI_PRICE_DATA: Dict[str, Dict[str, Any]] = {
    "paddy": {
        "commodity": "Paddy (Dhan / Common)",
        "msp_inr_quintal": 2300,
        "modal_price_inr": 2340,
        "price_range_inr": "2,250 – 2,420 / quintal",
        "weekly_trend": "Rising",
        "trend_arrow": "↗",
        "key_markets": ["Burdwan Mandi", "Nadia Krishnagar Mandi", "North 24 Parganas Barasat"],
        "post_harvest_advice": "Dry paddy to 12-14% moisture before bagging. Every 1% excess moisture increases grain fungal discoloration by 40%.",
        "storage_standard": "Stack gunny bags on wooden dunnage crates 30cm away from brick walls to prevent ground dampness.",
    },
    "potato": {
        "commodity": "Potato (Jyoti / Chandramukhi)",
        "msp_inr_quintal": 1400,
        "modal_price_inr": 1650,
        "price_range_inr": "1,550 – 1,800 / quintal",
        "weekly_trend": "Stable",
        "trend_arrow": "↔",
        "key_markets": ["Hooghly Tarakeswar Mandi", "Purba Bardhaman Memari", "Midnapore Mandi"],
        "post_harvest_advice": "Cure dug tubers for 10-14 days at 15-20°C with 85% RH to heal harvest abrasions before cold store entry.",
        "storage_standard": "Maintain cold storage temperature at 3°C to 4°C with 90% RH to prevent weight shrink and sprouting.",
    },
    "mustard": {
        "commodity": "Mustard Seed (Sarson / Rai)",
        "msp_inr_quintal": 5650,
        "modal_price_inr": 5820,
        "price_range_inr": "5,600 – 6,050 / quintal",
        "weekly_trend": "Rising",
        "trend_arrow": "↗",
        "key_markets": ["Murshidabad Berhampore Mandi", "Nadia Ranaghat Mandi", "Malda Mandi"],
        "post_harvest_advice": "Dry clean seed to <8% moisture. Store in moisture-proof HDPE bags; high moisture turns oil rancid (erucic acid).",
        "storage_standard": "Fumigate storage bins with Aluminium Phosphide if khapra beetle incidence is observed.",
    },
    "jute": {
        "commodity": "Raw Jute (TD-5 Golden Fiber)",
        "msp_inr_quintal": 5050,
        "modal_price_inr": 5280,
        "price_range_inr": "5,100 – 5,450 / quintal",
        "weekly_trend": "Stable",
        "trend_arrow": "↔",
        "key_markets": ["Cuttack-Kolkata Jute Mills", "Nadia Shantipur", "North 24 Parganas Barrackpore"],
        "post_harvest_advice": "Wash retted fiber in clean slow water. Avoid dark mud contact to retain natural golden luster.",
        "storage_standard": "Store baled fiber in well-ventilated dry warehouses on raised wooden platforms.",
    },
    "vegetables": {
        "commodity": "Fresh Seasonal Vegetables (Kharif / Rabi)",
        "msp_inr_quintal": 1800,
        "modal_price_inr": 2200,
        "price_range_inr": "1,800 – 2,600 / quintal",
        "weekly_trend": "Softening",
        "trend_arrow": "↘",
        "key_markets": ["Kolkata Koley Market", "Siliguri Regulated Market", "Howrah Wholesale"],
        "post_harvest_advice": "Harvest early in the morning. Pre-cool produce in shaded shed to remove field heat before transport.",
        "storage_standard": "Transport in perforated plastic crates rather than overloaded jute sacks to avoid crushing.",
    },
}


# ============================================================
# 7. AGGREGATE CROP ADVISORY DOSSIER GENERATOR
# ============================================================

def get_crop_advisory_dossier(
    crop: str,
    panchayat_id: str = "WB_107778",
    field_size: float = 1.0,
    unit: str = "acre",
    current_temp: float = 30.0,
    current_rh: float = 75.0,
    wind_kmh: float = 12.0,
    rain_p50: float = 5.0,
    rain_prob: float = 0.35,
    tmax: float = 32.0,
    tmin: float = 24.0,
    dew_point: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Synthesizes the complete, authoritative 6-module Crop Advisory Dossier.
    """
    clean_crop = (crop or "paddy").lower()
    
    # 1. Phenology & Stage Tracker
    phenology = get_crop_phenology(clean_crop, target_date=date.today(), tmax=tmax, tmin=tmin)
    active_stage_name = phenology.get("stage_name", "vegetative")

    # 2. Disease Catalog
    diseases = PEST_AND_DISEASE_DB.get(clean_crop, PEST_AND_DISEASE_DB["paddy"])

    # 3. Package of Practices
    pop_stages = POP_CATALOG.get(clean_crop, POP_CATALOG["paddy"])

    # 4. Fertilizer Calculator
    fertilizer = calculate_fertilizer_dosage(
        crop=clean_crop,
        field_size=field_size,
        unit=unit,
        rain_next_24h_mm=rain_p50,
    )

    # 5. Spray Advisor
    spray = evaluate_spray_suitability(
        temp_c=current_temp,
        humidity_pct=current_rh,
        wind_kmh=wind_kmh,
        rain_prob=rain_prob,
        rain_mm_24h=rain_p50,
        dew_point_c=dew_point,
    )

    # 6. Water Budget
    water = calculate_crop_water_balance(
        crop=clean_crop,
        stage_name=active_stage_name,
        tmax=tmax,
        tmin=tmin,
        rh=current_rh,
        wind_kmh=wind_kmh,
        rain_mm=rain_p50,
    )

    # 7. Mandi Intelligence
    mandi = MANDI_PRICE_DATA.get(clean_crop, MANDI_PRICE_DATA["paddy"])

    return {
        "crop": clean_crop,
        "panchayat_id": panchayat_id,
        "generated_at": datetime.now().isoformat(),
        "phenology_summary": phenology,
        "package_of_practices": pop_stages,
        "pest_and_disease_doctor": diseases,
        "fertilizer_calculator": fertilizer,
        "spray_advisor": spray,
        "water_irrigation_budget": water,
        "mandi_market_intelligence": mandi,
    }
