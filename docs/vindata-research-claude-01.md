# The "PredictWind for Vineyards" Opportunity: A Deep Strategic, Technical, and Market Assessment

**Prepared for:** Rob 
**Date:** May 2026

---

## 0. Executive Summary

The opportunity to build a hyper-local weather-intelligence + phenology + vineyard-cycle SaaS — pitched as a "PredictWind/Windy for vineyards" — is real, defensible, and timely, but the business shape is **not** an analogue of PredictWind. Vineyards are a 7.1 million hectare, ~~250–400k vineyard~~, ~50k+ winery global market, fragmented across 65+ countries with deep regional regulatory variation. The B2B SaaS layer (Vintrace, InnoVint, eVineyard, AgCode, Process2Wine, vinSUITE) is mature for *cellar/compliance* workflows; the **viticultural intelligence layer** (hyperlocal forecast + phenology + disease pressure + smoke-taint + spray decisions, all unified) is fragmented, mostly point-products, and not well-served outside a few European tools (Vintel/iTK, VitiMeteo, Sencrop). The Australian market in particular has a clear gap that NSW Wine's pilot **WaaS** (Weather as a Service) was attempting to fill — and the fact that WaaS is currently "undergoing maintenance" with only 16 virtual stations live confirms the shortfall.

Realistic shape of the opportunity:
- **Bear:** A regional ANZ leader doing A$1–2M ARR in 3 years, A$3–5M in 5 years, a niche but cash-flowing lifestyle business.
- **Base:** A global niche category-leader doing US$5–10M ARR in 5–7 years, attractive to Bayer/Climate FieldView, Corteva, John Deere, Treasury Wine Estates, AWRI/Wine Australia, or a weather company (DTN/Sencrop/Pessl) for an exit in the US$30–80M range.
- **Bull:** A "Climate Corp for specialty crops" play extended beyond grapes (apples, almonds, hops, cherries) reaching US$30–50M+ ARR and an exit in the US$200M+ range. This requires venture capital and is incompatible with the bootstrapped premise.

The **three viable wedges** to start from in Australia:
1. **Smoke-taint risk + bushfire/inversion alerting** (highest pain, regulatory tailwind, AWRI/La Trobe/Goanna Ag precedent — Wine Australia just put $1.78M federal AEA money behind the WISD program).
2. **Hyperlocal disease-pressure (DM/PM/Botrytis) + spray decision support**, replacing the WaaS pilot in NSW and expanding nationally.
3. **Frost prediction + radiation-cooled microclimate alerts** for cool-climate regions (Orange, Tumbarumba, Tasmania, Adelaide Hills) — currently underserved by 5 km BoM forecasts.

The defensible moat is not the data (most upstream weather data is open) — it is **(a)** a curated, validated stack of phenology and disease models calibrated to Australian cultivars and regions, **(b)** distribution through grower associations, AWRI, and Wine Australia, and **(c)** a multi-tenant platform that ingests every grower's own weather station / sap-flow / soil-moisture data and turns it into a network-effect dataset for better hyperlocal nowcasts.

Recommended technical stack: **PostgreSQL + TimescaleDB + PostGIS** (single-database for time-series, geospatial, and relational), **DuckDB / Iceberg on S3** for the satellite/raw weather lakehouse, **Cloudflare Workers + R2 + D1** for a globally distributed edge/PWA layer, **Hetzner or OVH GPU boxes** for ML training, **Modal or Replicate** for ML inference, **Open-Meteo (commercial tier) + ECMWF Open Data + BoM ACCESS-G/C + SILO** as the upstream weather mix. Bootstrapped target: monthly cloud spend ≤US$500 at MVP, ≤US$3,000 at 200 paying customers.

The remainder of this report substantiates the above.

---

## 1. Existing Solutions — Global Competitive Landscape

The category is fragmented along four orthogonal axes:

1. **Cellar/Winery ERP & compliance** (Vintrace, InnoVint, Process2Wine, vinSUITE, Ekos, Vintegrate, Orion, VinBalance, AgCode, vinCreative)
2. **Vineyard operations / scouting / spray records** (eVineyard, VitiScribe, VineLogic, VinLog, Croptracker, AgCode, Agworld, AgriWebb, VineInfo, Onside)
3. **Viticultural intelligence / decision support** (Vintel/iTK, VitiMeteo, Agrometeo, Fruition Sciences, Tule, FieldClimate/Pessl, Sencrop, Smart Vineyard/PreDiVine, Winessense)
4. **Weather/IoT/sensors** (Davis WeatherLink, Pessl Metos, Sencrop, MEA, Goanna Ag, Sentek, Manna, Arable, Tomorrow.io, Meteomatics, Open-Meteo)

The "leading platform" Rob envisions sits at the intersection of (2) + (3) + (4), which **no single vendor convincingly occupies globally**. The closest competitors are Vintel (in France/Italy/Iberia) and VitiMeteo (in DACH), and both are partial.

### 1.1 Detailed competitor profile table

| Vendor | Core proposition | Pricing (where published) | Geo | Ownership / funding | Strengths | Weaknesses |
|---|---|---|---|---|---|---|
| **Vintel (iTK, France)** | Decision-support / irrigation / disease / phenology — mechanistic crop models | "$250 per block" (early reviews); commercial quote-only | France/Italy/Iberia/some US | iTK SAS — long-time partner of Bayer Cropscience, Syngenta, Land O'Lakes; collaborated with INRA & CIRAD; once partnered with Verizon ("AgTech: Vineyard") | Best-in-class water-status mechanistic model (ψstem); strong scientific provenance | Per-block pricing scales poorly; weak in AU/NZ; UI dated; not open data |
| **VitiMeteo (DE/CH)** | Disease (Plasmopara, Erysiphe, Guignardia/Black Rot, grape moth, mites) + growth + phenology forecasts | Free for several jurisdictions, govt-subsidised | Germany, Switzerland, Luxembourg, Austria; meteoblue licensee | Consortium: Staatliches Weinbauinstitut Freiburg + Agroscope + GEOsens (GmbH); meteoblue weather feed | Open, peer-reviewed models (DMCast lineage); leaf-wetness focus; ~67% accuracy on Black Rot in 14-cultivar trials | Region-locked; not commercial; weak UX for owner-operators |
| **Agrometeo (Switzerland)** | Sister platform to VitiMeteo | Free / govt funded | CH | Agroscope | Same as VitiMeteo | Same |
| **Fruition Sciences (FR/US)** | Sap-flow + cloud analytics for vine water status, yield maps, phenology, NDVI overlay | Sensor + service contract; not published | Napa, Bordeaux, Languedoc, AU customers (Two Hands, Brokenwood) | Founded 2007 Oakland by Sebastien Payen & Thibault Scholasch; office Montpellier 2009; not raised material public funding | Premium consulting + tech bundle; deeply scientific; >1,000 blocks monitored | Expensive; sensor-dependent; high-touch |
| **Vintrace (US/AU)** | Cloud winery production, compliance, vineyard tracking | "Around $159/month entry"; tiered, quote-only at higher levels | Global, strong in AU + US | Owned by Encompass Technologies | Mature, AU-aware (originally Australian-built), good compliance | Vineyard module is light; expensive at scale |
| **InnoVint (US)** | Winery operating system: production, inventory, compliance, costing | Quote-only; ~$500+ onboarding | Mostly US, 2,000+ wineries | VC-backed | Best-in-class winemaker UX | Vineyard intelligence is shallow |
| **Process2Wine** | End-to-end winery production, vineyard ops, GPS tracking | Quote-only | Multi-region | Private | Broad coverage | UX dated; vineyard intelligence shallow |
| **eVineyard (Slovenia)** | Vineyard management, mildew/oidium/botrytis pressure, GPS, irrigation forecasts | Lite/Pro/Estate/Enterprise — quote-only after demo (reviews suggest €30–€300/mo by tier) | Europe-primary; multi-country | Private | Well-developed disease pressure module | No US weather/state compliance; pricing opaque; not optimised for AU regulation |
| **VineView (US/CA, formerly SkySquirrel)** | Aerial/drone imagery, EVI vigor maps, leafroll detection, PureCanopy™ | Per-flight / per-acre, custom | California/Oregon/Washington + France/AU/Chile | Merged 2018 with SkySquirrel | Aerial expertise, EVI > NDVI | Service business (not a SaaS); not weather/decision-support |
| **vinSUITE** | DTC, eCommerce, wine club, POS | Quote | US | Private | Strong DTC | Not viticultural |
| **VinBalance / Ekos / Vintegrate / Orion** | Winery accounting/inventory ERPs | $79–$300+/mo | US/global | Private | Mature | Not viticultural |
| **AgCode** | Enterprise vineyard ERP — large CA growers | Custom enterprise; weeks of professional services | California | Private | Deep enterprise feature set | Inaccessible to <500-acre operations |
| **VineLogic, VinLog, VineInfo** | Block-level activity logging, GIS, mobile | $79–$179/mo (VineInfo, AU) | Australia/Napa | Private | AU-aware; cost-effective | No serious weather intelligence |
| **VitiScribe** | US-focused, transparent-pricing spray compliance + scouting | $49 / $99 / $199 per month | US | Private | Pricing transparency leader | US-only; thin viticultural intelligence |
| **Vinwizard / Wine Tech Inc** | Tank/cellar/refrigeration automation; CellarView dashboard | SaaS subscription, undisclosed | NZ/AU/CA/CL/SA — yellow tail, Concha y Toro, Kim Crawford, Staglin, Quintessa | Sold by NZ founders to US Wine Technology Inc, May 2021 | Hardware+software cellar control | Cellar, not vineyard |
| **VINx2** | Weighbridge/harvest integration; bridges into Vinwizard, TankNET | Custom | NZ/AU | Private | Operational glue layer | Niche |
| **Agworld (AU)** | Broad-acre + permanent-crops farm management | Quote (regional) | AU global | Private; recently in alliance with AgriWebb (livestock) | Embedded in AU permanent-crop operations (e.g. Jansz / Penna) | Not viticulturally specialised; weak weather intelligence |
| **AgriWebb (AU)** | Livestock-led farm management | A$30–80/mo | AU/UK/SA/NZ/BR | VC-backed | Fast-growing | Not viticultural |
| **Tule Technologies (US)** | Stem-water-potential / actual ET via field sensors | Sensor + service; $75–125/sensor/mo equiv | US, mostly CA almonds/wine | Acquired by Valley Irrigation (Valmont) — exited the standalone category | Best-in-class ET measurement | No longer independent; expensive |
| **Sencrop (FR)** | Connected ag-weather stations + community network | Stations from ~€595 + ~€20–40/mo subscription | Europe-primary (FR/UK/DE/PL/CZ etc.); rolling out in NA | VC-backed (Series B) | "Network effect" stations + ag app; integrations with xarvio (BASF), eVineyard, VitiMeteo | Hardware-led; AU/NZ presence very limited |
| **Pessl Instruments / Metos / FieldClimate** | Weather stations + decision support models; iMETOS | Stations US$1,500–4,000; FieldClimate subscription | Global, esp. EU/US/BR/AR | Privately owned (Austria) | Most comprehensive ag-weather hardware ecosystem | Hardware-centric; software is a "front-end" not a SaaS |
| **Davis Instruments / WeatherLink** | Vantage Pro2/Vue stations + WeatherLink Cloud | Stations US$500–1,500; WeatherLink Cloud free–$9/mo | Global | Privately owned (US) | Massive installed base; APIs | No viticultural intelligence layer |
| **DTN Ag Weather** | Industrial ag weather + agronomic services | Enterprise | Global | TBC Industries (Schibsted spin-out) | Strong for broad-acre row-crop | Not vineyard specialised |
| **Tomorrow.io (formerly ClimaCell)** | Hyperlocal weather API, recently filed $175M for satellite constellation DeepSky | API tiers; free dev tier | Global | VC-backed | Ag-specific layers; soil moisture, fire risk | Not viticulturally targeted; pricey |
| **Meteomatics** | High-resolution weather API with proprietary EURO1k/US1k models, Meteodrones | Custom B2B | Global | Swiss private | 90 m on-the-fly downscaling; agriculture parameters | Premium pricing |
| **Open-Meteo** | Open-source aggregator over DWD/NOAA/MeteoFrance/CMC; 1–11 km resolution; historical 80yr | Free non-commercial; commercial tiers | Global | Swiss open-source project | Best-in-class commercial *value*; complete source code; AWS Open Data | Not viticultural |
| **Visual Crossing** | Forecast + 47 yr historical + commercial-friendly | Generous free tier; metered | Global | Private | Easy commercial use | Generic |
| **OpenWeather** | Generic forecast + agricultural intelligence platform | Tiered; up to enterprise | Global | Private | Polished | Generic |
| **Cropwise (Syngenta)** | Big-ag platform | Free–enterprise | Global | Syngenta | Extensive | Not viticultural |
| **Climate FieldView (Bayer)** | Big-ag, mostly US row crops | Per-acre subscription | US/EU/BR | Bayer (post-Monsanto) | Distribution power | No vineyard module of consequence |
| **xarvio FIELD MANAGER (BASF)** | Crop-protection decision support | Hectare-based | EU/Americas | BASF | Ties to Sencrop, Pessl, Arable | Not viticultural |
| **FruitionSciences/Fruition** | (See above) | | | | | |
| **Smart Vineyard / PreDiVine (Switzerland) / Senzemo / Winessense / Atfield / Smart Vineyards UK** | Sensor-based microclimate + disease prediction | Sensor + sub | EU/UK/Slovenia | Privately funded | Local microclimate | Small, regional |
| **Winegrid / Watgrid (Portugal)** | In-tank fermentation sensors + AI | Sensor + sub; H2020-funded | EU global | Acquired Nov 2023 by Enartis (Esseco Group, IT) | Productised, fast growing | Cellar, not vineyard |
| **Onside (NZ)** | Vineyard biosecurity + visitor / safety / compliance | Per property | NZ/AU expanding | Private | Strong AU/NZ adoption (Yalumba) | Not weather/phenology |
| **GiESCO** | Academic association, not software | n/a | | | | |
| **Sentek (AU)** | Soil-moisture probes (Drill & Drop, EnviroPro, EnviroSCAN) | Hardware + IrriMAX subscription | Global, Adelaide-based | Private | Mature AU brand, hardware standard | Hardware, narrow scope |
| **Manna Irrigation (IL)** | Satellite-based irrigation scheduling without sensors | Per-hectare SaaS | Global | VC-backed | Sensorless | Not weather/disease |
| **eLEAF** | Satellite ET / canopy biophysics | B2B | EU global | Private | Strong science | Not consumer-grade |
| **Goanna Ag (AU)** | AU agtech: GoField irrigation sensors, GoSense, WAND, **GoWISD** smoke-taint detection (commercialising the La Trobe / Wine Australia WISD program) | Hardware + sub | AU primary | Private | Becoming the AU vineyard sensor leader; just won A$1.78M federal AEA grant with La Trobe + Wine Australia | Hardware-led; not a software platform |
| **VitiCanopy app** | Open-access smartphone canopy LAI estimator (Adelaide Uni) | Free | Global research | Public | Research-grade | Not a platform |

**Key inferences:**
- No vendor today owns the "PredictWind/Windy" experience layer for vineyards: a beautiful, fast, hyperlocal map + free tier + paid pro that growers love, plus a serious commercial backend.
- The Australian market has **Vintrace** as the cellar/compliance ERP standard, **eVineyard / Onside / Agworld / VinLog** as point tools, and **NSW WaaS / La Trobe-Goanna WISD / AWRI / Wine Australia AgTech Hub** as government/research scaffolding — but no integrated commercial intelligence platform.
- The most plausible direct competitive threat is iTK (Vintel) extending into AU, or BASF/Bayer/Syngenta plugging vineyards into Cropwise/FieldView/xarvio. None of these are imminent — vineyards are a strategic afterthought for them.

---

## 2. NSW Wine WaaS — What It Is, Why It's Down, and What That Means

### 2.1 What it is

WaaS (Weather as a Service) is a pilot disease-alert and *virtual weather station* dashboard launched by NSW Wine in late 2025 / early 2026, co-developed with funding from **NSW Wine, Wine Australia, Riverina Winegrape Growers, and Food Innovation Australia (FIAL)**. The platform's distinctive technical characteristic per the published material is:

> "Weather data is at a resolution of **90 m** compared to 5 km for other publicly available forecasts." — nswwine.com.au

The pilot launched **16 virtual weather stations** across Riverina (Yenda, Hanwood, Nericon, Whitton, Leeton), Hunter Valley (Hermitage Rd, Hunter Valley Gardens), Mudgee (Logan, Robert Stein), **Orange (Cargo Rd, Pinnacle Rd)** — directly relevant to Word of Mouth Wines on Wallace Lane / Mt Canobolas — Canberra (Brindabella, Murrumbateman), Tumbarumba (Courabyra), Hilltops (Grove Estate), and Southern Highlands (Sutton Forest), with more planned for 2026.

It provides:
- 3-day forecasts for wind, rainfall, temperature, humidity
- DeltaT (spray suitability)
- Botrytis, downy mildew, powdery mildew alerts
- Locations chosen to "replicate the legacy [physical-station] network to minimise behavioural change"

### 2.2 Why it's "currently undergoing maintenance"

The page presently reads: *"This page is currently undergoing maintenance. Please return at a later date."* The pilot launched only in the 2025/26 growing season and was explicitly framed as a feedback-driven prototype. There is no published post-mortem. Plausible reasons:

1. **Pilot software / hosting fragility.** The platform appears to be a Squarespace-hosted gateway rendering virtual-station tiles from a back-end built on top of "publicly available" data — likely a contractor-built disease-model wrapper around BoM ACCESS-G/SILO/local-AWAP rainfall plus VitiMeteo-style models, and likely under-resourced for the load and feedback iteration it received.
2. **Funding cliff.** WaaS was funded by an industry-cooperative grant model (NSW Wine + WA + Riverina growers + FIAL). Pilot grants typically run 12–24 months; sustaining infrastructure and model calibration is a different cost structure that levy-funded bodies struggle to absorb.
3. **Coverage / accuracy backlash.** 16 stations across NSW's 14+ wine regions is sparse; Orange has only 2 (Cargo Rd, Pinnacle Rd) — neither at Mt Canobolas's 1,000m altitude where Word of Mouth sits, so 90 m "resolution" headlines mask the underlying coarseness of the input model.
4. **Organisational change at NSW Wine.** Single-EO organisation (Matthew Jessop), small team — a key handover or contractor change can take a tool offline.

### 2.3 Successor / parallel programs to know

- **NSW DPI Climate / DPIRD WA / SILO Long Paddock (Qld)** — government-grade gridded historical climate available free. NSW DPI (Darren Fahey, Scott McKinnon, Katie Dunne, Rob Hoogers) operates **Wine Australia AgTech Demonstration Sites** at Angullong (45 min SW of Orange) and in Griffith — directly relevant to Rob's region and a likely partnership channel.
- **Wine Australia AgTech Hub** — runs case studies (Yalumba × Onside, Torbreck × Swan Systems, Penley × Athena Irrigation) and an "Agtech Demonstration Sites" program.
- **AWRI (Adelaide)** — runs the smoke-taint analytical pipeline via Affinity Labs and contributes to research linkages with all major commercial taint research.
- **La Trobe University + Goanna Ag** — commercialising the WISD ("wizard") smoke-taint detector with A$1.78M Australian Economic Accelerator (AEA) grant; this is the closest precedent for a research-backed AU vineyard intelligence product going to market.
- **CSIRO Air Quality Forecasting**, **PurpleAir** consumer sensors — adjacent infrastructure.

### 2.4 International equivalents

- **France:** INRAE + CIRAD + IFV (Institut Français de la Vigne et du Vin) seed Vintel and similar tools; Météo-France AROME 1.3 km model is publicly accessible.
- **Italy:** ARPA regional weather services, plus University of Udine, University of Padua mildew-pressure models.
- **California:** UC Davis Viticulture & Enology + UC Cooperative Extension + CA Pest Management Database; the legacy of Park/Seem/Pearson/Gadoury (Cornell) for DMCast.
- **Switzerland/Germany:** VitiMeteo / Agrometeo (above).
- **South Africa:** ARC Infruitec-Nietvoorbij; Stellenbosch University has remote-sensing groups.
- **Argentina/Chile:** INIA Chile, INTA Argentina; less mature commercially.
- **Israel:** Manna, Prospera (acquired by Valmont), Tevel Aerobotics — agtech strength but not vineyard-specialised.

### 2.5 Implication for the opportunity

The fact that WaaS exists at all signals a clearly-defined latent demand — funded by the industry itself — and the fact that it's now offline confirms that levy-bodies struggle to be product organisations. **A commercial successor that is genuinely product-managed, Australian-aware, and connected to AWRI/La Trobe research has explicit white space**, and an obvious early customer set (the same 16 pilot regions, plus the funding bodies themselves, who would much rather pay a maintenance fee than re-fund a contractor every cycle).

---

## 3. Core Technical Capabilities — What a Leading Platform Must Do

The minimum coherent feature set for a "leading" platform is below. I have grouped them by criticality for Australian boutique-to-mid-commercial vineyards.

### 3.1 Tier-1 features (MVP)

| Capability | Detail | Notes for AU |
|---|---|---|
| Hyperlocal weather forecast | 0–72 h hourly, vineyard-block resolution (≤500 m), updated 4× daily; ensemble of ECMWF + GFS + ICON + ACCESS-G/C; downscaled by terrain & vineyard-station observations | BoM ACCESS-C 1.5 km is now nationwide (since 2022) — must be primary regional model |
| Frost prediction & alerting | Differentiate radiation vs. advection; 6/3/1 h lead times; SMS + push; threshold-configurable per cultivar | Critical for Orange, Tumbarumba, Tasmania, Adelaide Hills |
| Disease pressure modelling | Plasmopara viticola (DMCast / Magarey-Wachtel / VitiMeteo lineage), Erysiphe necator (Gubler-Thomas / UC Davis), Botrytis cinerea (Broome/Gubler-Bettiga, EPI, AusVit-style) | Auto-validate against AWRI / La Trobe data where possible |
| Phenology models | Budburst, flowering, veraison, harvest using Winkler GDD, BBCH stages, Caffarra-Eccel for *Vitis vinifera*, Parker grapevine flowering–véraison (GFV) | Must support cultivar-level parameters (Pinot Noir, Chardonnay, Shiraz, Cabernet Sauvignon, Riesling, Petit Manseng, Grüner Veltliner, Mencia) |
| Smoke-taint risk modelling | Real-time: link smoke dose (PM2.5 + atmospheric mixing) → volatile phenols / phenolic glycosides → cultivar-specific risk | La Trobe / Wine Australia thresholds; integrate WISD/GoWISD output once available |
| Spray decision support | Rain wash-off, withholding periods, AWRI MRL (Maximum Residue Limit) compliance, FRAC code rotation, organic alternatives | Australian "Dog Book" (AWRI Agrochemicals) is the regulatory anchor |
| ETo / irrigation scheduling | FAO Penman–Monteith reference ET; soil-moisture integration; weekly water budget | Cool-climate Orange is largely dry-grown, but pump-fed irrigation is common in Mudgee/Riverina |
| Block / vineyard digital twin | GIS map of every block, variety, rootstock, spacing, training system, planting year, irrigation infrastructure | PostGIS + H3 indexing |
| Activity / spray diary | Pesticide records, withholding compliance, vintage logs, harvest records | Maps to Wine Australia Levy / vineyard register; Sustainable Winegrowing Australia ("Members"/"Sustainable") inputs |

### 3.2 Tier-2 features (post-MVP)

| Capability | Detail |
|---|---|
| Yield forecasting | Image-based (VineView / FruitionSciences-style yield maps); historical regression on flowering count, bunch weight curves; satellite NDVI/EVI overlay |
| Compliance & traceability | Wine Australia Levy, Label Integrity Program (LIP), LRWBS, organic certification (NASAA, ACO), EU PDO/GI export compliance |
| Labour & task management | Crew scheduling, mobile task assignment, harvest team management, piecework rates |
| Pest pressure | Light brown apple moth (LBAM, *Epiphyas postvittana*) GDD model, mealybug, phylloxera (PIRSA biosecurity zones), Queensland fruit fly |
| Weather station integration | Davis WeatherLink, Sencrop, Pessl Metos (FieldClimate), MEA Plexus, Goanna Ag, Hortplus, Onset HOBO |
| Satellite imagery | Sentinel-2 L2A (5-day revisit, 10 m), Landsat-8/9, Planet Labs (3 m daily, paid), Sentinel-1 SAR for cloud-occluded NDVI infill |
| Soil moisture & sap flow | Sentek Drill & Drop / EnviroPro, Edaphic Scientific, Fruition Sciences sensors; ICT International SFM1 |
| Drone integration | DJI Mavic 3 Multispectral, MicaSense, Parrot Sequoia — KMZ/orthomosaic uploads |

### 3.3 Tier-3 features (differentiation / moat)

| Capability | Detail |
|---|---|
| Conversational AI viticulturist | LLM grounded on AWRI fact sheets, AGW & state DPI extension materials, regional viticultural consultants' published advice, and the customer's own block history |
| Cultivar/clone library | Detailed phenology curves and disease susceptibility per clone (Dijon Pinot Noir clones, MV6, etc.) |
| Network effect: shared station mesh | Sencrop-style: every customer's station feeds the regional nowcast |
| Vintage report automation | Generate end-of-season vintage report + Wine Companion-style submission |
| Climate adaptation planner | Long-term plot-level projection for varietal suitability under SSP2-4.5 / SSP3-7.0 (CSIRO ACCESS-CM2, NorESM2-MM data) — strategic replanting tool |

---

## 4. Data Sources & Technical Architecture — Staff/Principal Engineer Deep Dive

### 4.1 Upstream data sources

#### 4.1.1 Weather (forecast + observation)

| Source | What | Resolution / latency | Cost / licence | Use |
|---|---|---|---|---|
| **BoM ACCESS-G (Australia global)** | Global numerical weather prediction | 12 km, 6-hourly cycle, 10-day | Open access via NCI / BoM FTP / OpenDAP; CC-BY | Day 4–10 forecasts, AU |
| **BoM ACCESS-C (City) / ACCESS-R (Regional)** | High-res nested model | 1.5 km / 12 km, 6h cycle, 78 h | Open data | Day 0–3, AU primary |
| **BoM AWAP / AGCD** | Gridded surface obs | 5 km daily | Open | Historical baseline |
| **BoM observations** | AWS stations | Hourly | FTP free, but commercial use frowned on; CDS for licensed feeds | Real-time obs |
| **SILO (Long Paddock, QLD Govt)** | Continuous gridded interpolated obs 1889–present | 5 km / 0.05° daily | CC-BY-4.0; AWS S3 open data (silo-open-data) | Phenology hindcasts, GDD baselines, climatology — *the* AU historical backbone |
| **DPIRD Weather 2.0 API (WA)** | WA station network | Per-station live | API key required; free | WA |
| **ECMWF HRES** | Best global model | 9 km, 2× daily | Real-time licence ~€50–250k/yr; **ECMWF Open Data** is now free at 0.25° | Use Open Data tier; pay only if scaling |
| **ECMWF AIFS** | AI ensemble | Promising; free Open Data | Free | Ensemble blending |
| **NOAA GFS / GEFS** | US global | 0.25°, 4× daily, 16 day | Free, public domain | Ensemble blending |
| **DWD ICON / ICON-D2** | German global + 2 km regional | Open | Free | Ensemble blending |
| **Météo-France AROME** | 1.3 km regional | Open (FR/EU) | Free | EU customers later |
| **Open-Meteo** | Aggregator over DWD/NOAA/Météo-France/CMC + own forecast | 1–11 km, hourly updates | **Free non-commercial**; commercial tier from a few hundred €/year, scales to enterprise | **Use this as primary commercial fall-back** — best price/coverage |
| **Visual Crossing** | Forecast + 47-yr historical | Generous free tier; metered | Per-call paid | Historical backfill |
| **Tomorrow.io** | Hyperlocal + ag layers | Free dev tier; paid | Mid-tier for soil/fire/agriculture layers | Possibly for fire risk / smoke proxies |
| **Meteomatics** | 90 m on-the-fly downscaling, 2,000+ parameters incl. ag | Premium B2B | Premium | Reserve for enterprise tier |
| **NASA POWER** | Satellite-derived ag weather | Daily, 0.5° | Free | Global historical climatology |
| **Copernicus C3S / ERA5** | Reanalysis | 0.25° hourly | CC-BY (CDS) | Climate adaptation; historical training |
| **PurpleAir / OpenAQ** | Citizen PM2.5 sensors | Real-time | Free | Smoke-taint nowcast input |

**Recommendation:** Mix: ACCESS-G/C as AU primary, ECMWF AIFS + NOAA GFS for ensemble, Open-Meteo commercial as the universal fall-back wrapper, SILO + ERA5 for historical training, PurpleAir/OpenAQ for smoke. Avoid ECMWF HRES license fees until ARR justifies them.

#### 4.1.2 Satellite imagery

| Source | Resolution / revisit | Cost | Use |
|---|---|---|---|
| Sentinel-2 L2A | 10 m, 5 days | Free (Copernicus) | NDVI, EVI, NDRE, NDWI |
| Sentinel-1 GRD | 10 m, 6 days | Free | Cloud-penetrating SAR, NDVI infill |
| Landsat-8/9 | 30 m, 16 days | Free (USGS) | Long historical record |
| Planet PlanetScope | 3 m, daily | Paid (~US$1–2/km²/year) | Premium tier |
| Maxar / WorldView | 0.3 m, on-demand | High | Edge cases |
| **Sentinel Hub (Sinergise)** | Hosted API over above | Tiered (~€30–€2,000/mo) | Don't build raster tiling yourself |
| Microsoft Planetary Computer / AWS Open Data | STAC catalogues | Free compute close to data | Compute satellite indices on-demand |

**Recommendation:** Use Sentinel-2 L2A from AWS Open Data via a STAC + DuckDB-spatial pipeline; expose Planet only on Pro+ tiers.

#### 4.1.3 IoT / weather station ecosystems

- **Davis Vantage Pro2 / Vue / Vantage Connect / Airlink** + **WeatherLink Cloud API** — most common in AU, REST + JSON, a developer's pleasure.
- **Sencrop Raincrop / Windcrop / Leafcrop** — REST API, good docs.
- **Pessl Metos (iMETOS IMT, ECO D3, LoRAIN, µMETOS)** — FieldClimate API.
- **MEA Plexus** — AU ag weather, broad market (DPIRD).
- **Goanna Ag** — proprietary cloud, partner via API.
- **Hortplus** (NZ/AU) — established disease-model-friendly station network.
- **Adcon / OTT HydroMet** — enterprise.

Connectivity: LoRaWAN (TheThingsNetwork, Helium Migaloo, NNNCo) is the dominant protocol for AU rural agtech; NB-IoT (Telstra, Optus) is gaining; Sigfox is essentially gone. Cat-M1 is the right choice for vineyard 4G stations. **Build the platform protocol-agnostic** — don't lock in.

#### 4.1.4 Soil moisture & plant sensors

Sentek (Drill & Drop, EnviroSCAN), Edaphic Scientific, Campbell Scientific, ICT International (SFM1 sap-flow), Fruition Sciences, DFM probes, Goanna Athena.

#### 4.1.5 Open-source phenology and disease models

- **DMCast** (Park/Seem/Pearson/Gadoury, Cornell) — primary infections from oospore maturity + leaf wetness + temperature; secondary infections by leaf-wetness duration + temp during wetness. Reference paper available; algorithm reproducible.
- **Magarey & Wachtel** — Australian *P. viticola* model (CSIRO/AWRI lineage).
- **Gubler-Thomas Powdery Mildew Risk Index** (UC Davis) — temperature-based, widely implemented (used by FieldClimate, eVineyard).
- **Broome / Gubler-Bettiga botrytis** — bunch closure to véraison, leaf wetness + temp.
- **Goidanich's EPI** (Italy) — older, useful as comparator.
- **Caffarra-Eccel (2009)** — robust grapevine phenology model for Vitis vinifera (often cited as the European modern standard).
- **GFV (Grapevine Flowering–Veraison; Parker et al. 2011, 2013)** — cultivar-parameterised across hundreds of cultivars including AU varieties.
- **BBCH scale** — universal phenological staging, must be the canonical state model.
- **Smoke-taint dose model** — La Trobe / Wine Australia (Porter, Wilkinson, Ristic) is proprietary in WISD but academic literature exists; Favell et al. 2021 published predictive off-vine models for British Columbia; the Coulter et al. 2022 thresholds for volatile phenols and phenolic glycosides are the canonical AU reference.

**License note:** All of the above models are described in peer-reviewed literature; reimplementations are legally fine. Do **not** reuse VitiMeteo's compiled algorithms — those are owned by GEOsens.

### 4.2 Recommended modelling stack

```
Layer                | Choice                                  | Why
---------------------|-----------------------------------------|--------------------------------------------
Mechanistic models   | Python with numpy/scipy + pydantic      | DMCast, GDD, Penman-Monteith all expressible in <500 lines each; testable
ML — time series     | PyTorch + lightning + neuralforecast    | LSTM and Temporal Fusion Transformers (TFT) for 1–24 h hyperlocal nowcast
ML — vision          | PyTorch + segmentation_models.pytorch   | Phenology stage from images, leafroll detection
Downscaling          | xarray + climdyn + simple bias-corrected delta-change; or RainNet-style CNN | Statistical downscaling is cheaper than dynamical; aim for 200 m post-processing
Ensemble blending    | Linear / quantile-regression averaging  | Don't overcomplicate; QRA beats most fancy methods
Feature store        | Just Postgres tables until 200+ models  | Resist Feast/Tecton until necessary
Experiment tracking  | Weights & Biases (free for solo) or MLflow self-hosted | 
```

### 4.3 Recommended platform architecture

This is the section worth slowing down on. The design goal is a **single small team running a multi-tenant SaaS that serves 10 to 10,000 vineyards from a sub-US$3,000/month cloud bill** at MVP-to-PMF scale.

#### 4.3.1 Datastore — opinionated

**Primary OLTP + time-series + geospatial: PostgreSQL with TimescaleDB and PostGIS extensions, hosted on Tigerdata/Timescale Cloud or self-hosted on Hetzner.**

Why this triple stack rather than InfluxDB/ClickHouse/QuestDB:
- Vineyard data is **bounded and slow** by IoT standards: a station emits perhaps 1–10 readings per minute; even with 5,000 stations × 50 sensors each × 1/min, that's only 250k writes/minute (~4k/sec) — laughably easy for TimescaleDB on a $200/month Hetzner box.
- TimescaleDB's hypertables + columnar compression deliver 90%+ compression on time-series like temperature/humidity/leaf-wetness, eliminating the storage advantage InfluxDB historically had.
- Postgres gives you transactional integrity for tenancy / billing / blocks / activities, ACID joins between station readings and vineyard blocks (essential), and the entire ecosystem of ORMs, BI tools, and tooling.
- PostGIS is unmatched for geospatial; H3 (`pg_h3`) gives you global hex-indexed spatial join performance for assigning every block/station to a forecast cell.
- ClickHouse is *better* for billion-row OLAP analytics, but you don't have those at MVP, and OLAP can be handled by a separate DuckDB-on-Iceberg lakehouse (below) if/when you do.

If at some point hyperlocal forecasting becomes a hot-write workload measured in tens of thousands of writes/second per ingest pipeline, **add ClickHouse as a secondary OLAP store**. Don't start there.

**Lakehouse for raw weather / satellite / model outputs: Apache Iceberg + Parquet on S3-compatible storage (Cloudflare R2 — zero egress charges) + DuckDB for ad-hoc compute.**

- R2 is the single biggest cost win for a bootstrapped agtech startup. Egress-free means satellite tiles, model outputs, and historical archive can be read by anyone, anywhere, with no surprise bill.
- DuckDB-spatial natively reads Parquet/GeoParquet from S3/R2 and is faster than 90% of Spark workloads at this scale.
- Iceberg gives you time-travel, schema evolution, and is now the de-facto open-table standard (Snowflake, AWS, Databricks, Cloudflare all support it).
- Forget Hudi (too operational), Delta (Databricks-anchored). Iceberg is the right bet for a small team.

**Caching: Redis or Cloudflare KV** — KV beats Redis on price for sub-1ms forecast-tile reads served from edge.

#### 4.3.2 Stream processing

- **MVP: Skip stream processing entirely.** Use scheduled Python (Prefect or Dagster, self-hosted) running every 1–15 min. Most weather and IoT pipelines are micro-batch.
- **Once volumes justify:** **Redpanda** (Kafka API, single binary, vastly cheaper to run) over Kafka/Pulsar for ingest fan-out; **Materialize** or **RisingWave** (Postgres-compatible) for streaming SQL; both are runaway easier than Flink for a small team.
- **Avoid Flink** unless headcount > 10. The operational tax is real.

#### 4.3.3 Cloud + compute

- **Cloudflare** is the right global frontend: Workers + Pages + R2 + D1 + Durable Objects + Queues + KV — all priced for bootstrap.
- **Hetzner Auctioned Dedicated Servers (AX-line, 64–256 GB RAM, NVMe)** for Postgres + ML training: ~€60–€400/mo. With ZFS + replicated standby, this is brutally cost-effective.
- **AWS** for what it does best: SES (transactional email), and possibly Amazon Bedrock for LLM inference.
- **GCP** only if you commit to BigQuery (overkill). I would not recommend it for this profile.
- **Modal or Replicate** for ML inference: pay-per-second GPU, serverless. Beats SageMaker for bootstrappers.
- **Containerized on Hetzner via Coolify or Dokku** for the API + worker tier; **serverless on Cloudflare Workers** for the public-facing API and hyperlocal-forecast tile serving.

This **hybrid Cloudflare + Hetzner + Modal** pattern is the most cost-effective architecture in 2026 for a workload that mixes (a) globally distributed read traffic, (b) heavy ML training, and (c) modest write throughput. A typical month's bill at 200 paying customers:

| Item | Cost (US$) |
|---|---|
| Cloudflare Workers + R2 + KV + D1 | $50–150 |
| Hetzner Postgres primary + standby + 2 worker nodes | $200–400 |
| Modal GPU inference | $50–300 (usage-driven) |
| Sentinel Hub | $30–200 |
| Open-Meteo commercial | $50–500 |
| AWS SES + misc | $20 |
| **Total** | **~$400–1,500** |

#### 4.3.4 Multi-tenancy

- **Postgres row-level security (RLS) with a tenant_id column** is more than sufficient. Don't go schema-per-tenant; it's an operational nightmare at >100 tenants.
- For commercial customers wanting "their own" data isolation, offer a **dedicated DB instance** option at $X00/month premium; same code, different connection string.
- Block-level data structure: `tenant -> property -> block -> activity / forecast / sensor reading`. This handles both single-block boutiques (Word of Mouth: 3 ha, ~5–10 sub-blocks by variety) and Treasury Wine Estates (thousands of blocks across hundreds of properties).

#### 4.3.5 Frontend

- **Web app: Next.js (App Router) on Cloudflare Pages** with **MapLibre GL** for maps, **Tanstack Query** for state, **shadcn/ui** for components.
- **Mobile: a PWA, not a native app**, at MVP. Vineyards in cool climates have variable connectivity; **offline-first via service worker + IndexedDB + Dexie** is critical and easier in a PWA than React Native.
- Once Pro tier is paid, wrap the PWA in **Capacitor** for App Store / Play Store presence.
- **Map tile service: a Cloudflare Worker that converts upstream weather GRIB → Cloud Optimised GeoTIFF → MapLibre raster tiles**, cached aggressively at the CF edge. This is the architectural unlock for "Windy-like" performance.

#### 4.3.6 ML inference patterns

| Workload | Pattern | Tool |
|---|---|---|
| Daily batch phenology forecast (every block, 16 d horizon) | Batch | Modal cron job, writes to Postgres + R2 |
| Hyperlocal nowcast (next 6 h, 250 m grid) | Micro-batch every 15 min | Modal scheduled function |
| Smoke-taint risk live | Streaming (when WISD/PurpleAir spike) | Cloudflare Worker + Postgres trigger |
| Computer-vision phenology stage | On-demand from grower upload | Modal endpoint |
| LLM advisor (Tier-3) | On-demand | Replicate or Bedrock; RAG with pgvector |

**Model serving tools comparison:**
- **Modal** — best DX for Python-native engineers, pay-per-second, easy GPU. **Recommended primary.**
- **Replicate** — great for vision/LLM SaaS-style endpoints; community models a plus.
- **AWS SageMaker** — overkill, expensive, slow DX.
- **BentoML / Ray Serve** — only if self-hosting on Hetzner; pay the ops tax.

#### 4.3.7 Data quality & observability

- **Great Expectations or Soda Core** for declarative data quality on every pipeline. Soda is lighter; pick Soda.
- **Application observability:** Grafana Cloud free tier (50 GB log, 10k metrics) → Better Stack / Axiom when you outgrow it.
- **Error tracking:** Sentry.
- **Status page:** Atlassian or BetterStack.

#### 4.3.8 Reference architecture diagram (text form)

```
                         ┌──────────────────────────┐
                         │  Open-Meteo / ECMWF /    │
   Upstream weather  ───►│  BoM / SILO / NOAA / DWD │
                         └────────────┬─────────────┘
                                      │
                         ┌────────────▼─────────────┐
   Weather stations ────►│  Ingest workers          │
   (Davis, Sencrop,      │  (Modal cron / Hetzner)  │
   Pessl, MEA, Goanna)   │  Python + httpx + Pydantic│
                         └────┬──────────┬──────────┘
                              │          │
         ┌────────────────────▼──┐    ┌──▼─────────────────────────┐
         │  Postgres (Timescale  │    │  R2 (Iceberg + Parquet)    │
         │  + PostGIS) — primary │    │  Raw weather, satellite,   │
         │  OLTP + time-series   │    │  archived forecasts        │
         │  + geospatial         │    └──┬─────────────────────────┘
         └─────────┬─────────────┘       │
                   │                     │
         ┌─────────▼─────────────┐  ┌────▼────────┐
         │  Modal: phenology,    │◄─┤  DuckDB on  │
         │  disease, smoke,      │  │  R2 (BI)    │
         │  ML nowcast, vision   │  └─────────────┘
         └─────────┬─────────────┘
                   │
         ┌─────────▼──────────────────────┐
         │  Cloudflare Workers / KV cache │  ◄── PWA (Next.js + MapLibre)
         │  Public API + tile server      │  ◄── Mobile (Capacitor)
         └────────────────────────────────┘
```

---

## 5. Market Sizing & Unit Economics

### 5.1 Global market

Per OIV State of the World Vine and Wine Sector 2024:
- **7.1 million ha** total vineyard surface (note: includes table grapes and dried-grape vineyards, not all wine).
- ~225.8 mhl wine production.
- The European Union is 61% of global production (Italy, France, Spain dominant); the Southern Hemisphere ~20%.

Number of distinct **wine-producing entities** globally is harder. Using regulatory/licence proxies:
- **Australia:** ~2,156 wineries + ~5,408 wine-grape growers (Wine Australia 2024). Total addressable wine-grape vineyards ≈ 7,500.
- **USA:** ~11,691 wineries (Wines Vines Analytics, 2024); California alone ~5,000. Vineyards (separate growers) substantially larger; CA vineyards ≈ 6,000.
- **France:** ~58,000 viticultural holdings (RGA agricultural census).
- **Italy:** ~250,000 wine-grape holdings (most very small; ~46,000 with >1 ha commercial relevance).
- **Spain:** ~140,000 holdings.
- **Germany:** ~13,000.
- **South Africa:** ~2,500 producers.
- **New Zealand:** ~700 wineries, ~2,000 growers.
- **Chile:** ~12,000 vineyard holdings.
- **Argentina:** ~17,000 (mostly Mendoza).

**Globally addressable, *commercial-software-buying* universe:** Realistically **~150,000–250,000 vineyards** globally would consider paying for SaaS. The smaller hobby/co-op tail is irrelevant.

### 5.2 Australia detail

Per Wine Australia 2024-25:
- 2,156 wineries; ~5,408 grape growers; 146,244 ha total vineyard area.
- ~65 wine regions.
- Crush-size distribution (Australian and New Zealand Wine Industry Directory 2025): ~70% of wineries crush <100 t (boutique), ~25% crush 100–10,000 t (mid-commercial), ~5% crush >10,000 t (corporate — TWE, Pernod Ricard, Accolade, Casella, De Bortoli).

Word of Mouth is in the boutique band (3 ha, ~10 t crush); Orange has ~50–60 wineries with ~600 ha; total NSW has ~700 wineries.

### 5.3 IT/software spend benchmarks

- **Cellar/winery software:** US$1,500–10,000 per year for Vintrace/InnoVint mid-tier; US$10–50k+ for AgCode/Vintegrate enterprise.
- **Vineyard scouting/management:** VitiScribe US$49–199/month; eVineyard ~€30–€300/mo; Agworld ~A$1,200–4,000/yr.
- **Weather station hardware:** Davis Vantage Pro2 ~A$1,500; Sencrop Raincrop ~€595 + €240/yr; Pessl Metos ~A$3,000–5,000 + sub.
- **Imagery/aerial:** VineView ~US$50–150/acre/year.
- **AWRI services:** Smoke taint analysis ~A$300–800 per sample.
- Total **annual digital spend per mid-commercial vineyard:** ~A$5,000–25,000; per boutique: ~A$500–2,500.

### 5.4 TAM/SAM/SOM

| | Definition | Estimate |
|---|---|---|
| **TAM (global)** | All commercial wine vineyards × $2,000 avg ARPU | 200,000 × $2,000 = **$400M ARR** as a category cap for the *intelligence layer* alone (not full ERP) |
| **SAM (English-speaking + AU/NZ + South-Hemisphere)** | AU+NZ+US+CA+ZA+UK = ~25,000 prospects × $2,000 | **$50M ARR** |
| **SOM (5-yr realistic)** | AU + NZ + early US west-coast | 1,500–3,000 customers × $1,500 ARPU = **$2.25–4.5M ARR** |

### 5.5 Comparable agtech exits

- **The Climate Corporation → Monsanto, Oct 2013, ~$930M cash + ~$170M retention (~$1.1B reported)** — weather/data analytics platform; arguably the most cited exit in agtech.
- **Granular → DuPont/Corteva, 2017, $300M** — farm management software; reportedly ~100× revenue, indicating strategic premium. Revenue at acquisition therefore ~$3M ARR — extremely high multiple due to strategic value to DuPont.
- **Blue River Technology → John Deere, 2017, $305M** — see-and-spray computer vision.
- **Climate Corp → VitalFields, 2016 (small Estonian acq)** — Climate's first European foothold via FMS.
- **Prospera → Valmont, 2021, $300M** — vision-based ag analytics.
- **WINEGRID → Enartis (Esseco Group), Nov 2023** — fermentation sensors; price not disclosed but considered material.
- **VinWizard (Wine Tech Marlborough) → Wine Technology Inc., May 2021** — winery automation; private, undisclosed.
- **Vintrace (built in Adelaide) → Encompass Technologies** — undisclosed but a clean strategic outcome.

**Take-away:** The agtech exit market is real but requires either *strategic acquirer fit* (Climate Corp / Granular) or *operating cashflow attractiveness* (Vintrace, VinWizard). For a bootstrapped venture, the second path is more reliably bankable.

### 5.6 Realistic ARR scenarios

| Scenario | Yr 3 ARR | Yr 5 ARR | Headcount | Exit valuation (4–8× ARR) |
|---|---|---|---|---|
| **Bear (ANZ niche)** | A$700k | A$2M | 4 | A$8–16M |
| **Base (ANZ leader + early US west coast)** | A$1.5M | US$5M | 8–10 | US$20–40M |
| **Bull (global category leader, perhaps VC-backed) | A$3M | US$15M+ | 25 | US$60–120M+ |

Given Rob is bootstrapped + post-acquisition of an operating vineyard, **the Base scenario is the realistic anchor**.

### 5.7 Pricing benchmarks

| Model | Example | Notes |
|---|---|---|
| Per-month flat | Vintrace ~US$159 entry | Simple but doesn't scale with value |
| Per-hectare/year | Vintel "$250/block" historical; Manna Irrigation ~US$15–30/ha/yr | Aligns with grower mental model |
| Per-user | InnoVint per-seat | Friction for crews |
| Per-property | Onside (NZ) | Good for biosecurity/visitor compliance |
| Freemium + Pro | PredictWind US$0/$29/$249/$499 | What we're considering |

**Recommended tiered pricing** (AU launch):

| Tier | Target | Price |
|---|---|---|
| **Free** | Single-block hobbyist, Pro user-acquisition top-of-funnel | A$0 — basic forecast, basic disease risk, 1 block |
| **Boutique** | <10 ha owner-operator (Word of Mouth profile) | A$49/mo or A$490/yr |
| **Estate** | 10–100 ha, multiple blocks/varieties | A$199/mo or A$1,990/yr |
| **Commercial** | 100–1,000 ha, multi-property, multi-user | A$799/mo + A$5–10/ha |
| **Enterprise** | Treasury / Pernod Ricard / Accolade — multi-region, custom | Custom; A$50k–A$500k/yr |

This produces realistic ARR with 1,000 customers split 30% / 50% / 15% / 5%: ~A$2.6M/yr, matching the Base case.

---

## 6. Go-to-Market & Distribution

### 6.1 Channel partners

**Australia first:**
- **Wine Australia** (statutory body, levy-funded, manages AgTech Hub) — ideal for branded research collaborations and at minimum a "Recommended Tools" listing.
- **Australian Grape & Wine (AGW)** — peak industry body; advocacy + comms reach.
- **AWRI** — research credibility; integrations on smoke taint, MRL spray decision, fermentation data.
- **NSW Wine Industry Association** — direct WaaS successor opportunity (Matthew Jessop, EO).
- **Riverina Winegrape Growers** — was a WaaS funder.
- **Orange Region Vignerons Association (ORVA)** — Rob's local; cellar-door network; rapid trust-building.
- **Hunter Valley Wine & Tourism Association**, **Margaret River Wine Association (Wines of WA)**, **South Australian Wine Industry Association (SAWIA)**, **Wine Tasmania**, **Wine Victoria**, **Vignerons of Mudgee** — regional associations.
- **NSW DPI** (Darren Fahey, Scott McKinnon, Katie Dunne, Rob Hoogers) — Angullong + Griffith demonstration sites.

**International:**
- **Wine Institute (US)** — California
- **CIVB (Bordeaux)**, **Comité Champagne**, **InterRhône**, **InterLoire**
- **OIV** (Paris) — academic legitimacy
- **New Zealand Winegrowers**
- **VinPro (South Africa)**
- **Wines of Argentina, Wines of Chile**

### 6.2 Trade shows / conferences

- **Wine Industry Outlook Conference (AGW)** — Adelaide annually
- **Unified Wine & Grape Symposium** — Sacramento, January, the largest in N. America
- **Vinitech-Sifel** — Bordeaux, biennial, global agtech focus
- **SIMEI** — Milan, biennial
- **WiVi Central Coast** — California
- **Romeo Bragato Conference** — NZ
- **ASVO Technical conferences** (Australian Society of Viticulture & Oenology) — ideal for credentialing.

### 6.3 Influencers / consultants

In Orange / NSW: Liz Riley (Vitibit), Mary Retallack (Retallack Viticulture), James Halliday (Wine Companion). Nationally: Dr Tony Proffitt (AHA Viticulture, WA), Mark Krstic (AWRI), Dr Suzy Rogiers (NSW DPI). Building these relationships (ASVO, Bragato) is the cheapest path to thought-leader endorsement.

### 6.4 Sales motion

- **Bottom-up via boutique cellar door (PLG)**: Free tier + great PWA + word-of-mouth in the regional vigneron WhatsApp groups. Word of Mouth Wines is itself the best demo site.
- **Top-down for commercial**: A salesperson with viticultural credibility (likely a co-founder or hire) targeting Treasury Wine Estates, De Bortoli, Pernod Ricard Australia (Jacob's Creek), Accolade Wines, Casella, Brown Family Wine Group. Sales cycle 6–12 months; deal sizes A$50k–500k.
- **The middle (boutique → estate)** is the sweet spot for SaaS-style self-serve.

### 6.5 The PLG opportunity

A free tier with the *Windy-quality forecast* layer for any vineyard globally is genuinely viable as a customer-acquisition engine. The key is gating: free for forecast-watching; paid for spray decisions, phenology forecasts, alerting, integrations. This mimics PredictWind (free models, paid weather routing).

### 6.6 Partnerships with weather station manufacturers

- **Davis Instruments AU distributor (Rainwise)** — co-marketing.
- **Pessl Australia** — bundle FieldClimate-light into the Estate tier.
- **Goanna Ag** — natural partner for AU smoke-taint/irrigation hardware.
- **MEA (Adelaide)** — established AU brand.
- **Sencrop (when they enter AU/NZ)** — share-of-customer plays.

---

## 7. The "Windy / PredictWind Parallel" — Is It Valid?

### 7.1 What makes Windy and PredictWind work

- **Windy.com** (Czech, founded by Ivo Lukačovič) — beautiful WebGL maps over ECMWF/GFS/ICON, near-zero monetisation pressure (originally a side-project), reach is the moat.
- **PredictWind** (NZ, Jon Bilger, founded 2009; **unfunded per Tracxn**) — uses ECMWF + GFS + UKMO + AROME + their own PWG/PWE/PWAi 1km models; tiered pricing **$0 / $29 / $249 / $499 per year** for Free / Basic / Standard / Professional. Estimated revenue is in the low-to-mid eight figures; sustaining business at modest staff count.

Two structural reasons they work:
1. **Sailors and fishermen are individuals** with discretionary spend; the buying decision is fast and emotional.
2. **The weather data they expose has consumer-friendly "story arcs"** (storm fronts, wind shifts, departure windows) that are visually beautiful.

### 7.2 Vineyards are different

- **Buyers are owner-operators or vineyard managers** — closer to small-business than consumer; slower decision; more concerned with compliance, audit trail, and proven ROI.
- **The data story is less visual.** "Botrytis pressure +1 over baseline" is not the same emotional pull as "20-knot squall arriving in 90 minutes."
- **The integration burden is higher.** Vintrace exports, AWRI MRL tables, sensor APIs — the platform must do real plumbing.
- **Sales cycle is longer.** Estate tier buyer takes 30–90 days; Commercial takes 6–12 months.

### 7.3 What translates from PredictWind / Windy

- **The interface and visual design philosophy** — gorgeous, fast, hyperlocal maps as the front door. This is genuinely missing from every existing vineyard tool.
- **The freemium architecture** — free 3-day forecast + risk traffic-lights for any block in the world; paid spray decisions, alerting, integrations.
- **The "ensemble of models" framing** (PredictWind shows ECMWF/GFS/UKMO/HRRR side-by-side) — Pro viticulturists love comparison; show ACCESS-G vs ECMWF AIFS vs GFS for the same block.
- **API access as a Pro feature** — pulls in viticulture consultants and academic partners.

### 7.4 What doesn't translate

- **Pure consumer pricing** — A$29/year won't fund the model + integration stack. Boutique pricing must be A$49/month or higher.
- **Pure ad/affiliate revenue** — agriculture has no equivalent of Windy's anchor advertisers.

### 7.5 The right framing

**"PredictWind UX × Vintel models × VitiMeteo data depth × AWRI calibration × Australian distribution."** Not literally PredictWind, but Windy-grade visual quality is the *unfair advantage* over the spreadsheet-and-portal incumbents.

---

## 8. Risks, Moats & Strategic Analysis

### 8.1 Defensible moat candidates

| Moat | Strength | Notes |
|---|---|---|
| **Data network effect** (every customer station feeds the regional nowcast) | Strong, compounds | This is the Sencrop play; replicate in AU |
| **Calibrated cultivar/clone library** for AU varietals | Strong, hard to copy | Especially Pinot Noir clones, Shiraz blocks, alt varieties |
| **AU smoke-taint integration** | Medium-Strong | Owned operationally only via partnership with La Trobe / Goanna Ag — go fast |
| **Brand among regional vigneron associations** | Medium | Earned, not bought; takes 2–3 vintages |
| **Distribution through Wine Australia / AWRI** | Medium | Levy-funded body endorsement is rare but compounds |
| **Models themselves** | Weak | DMCast / Caffarra-Eccel / Gubler-Thomas are public; differentiation is in calibration and UX |
| **Weather data** | Very Weak | Open-Meteo / ECMWF Open Data democratised this |
| **LLM advisor** | Weak alone | Becomes strong if grounded on 5+ years of customer-specific block data |

The combination: *network-effect data + AU-calibrated models + viticulturally-credible brand + great UX*.

### 8.2 Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Incumbents (Vintrace, AgCode, Climate FieldView) bolt on a forecast layer | Medium | Move fast; aim to be the de-facto AU hyperlocal layer in 18 months |
| Government provides a free competitor (WaaS revival, BoM expansion) | Medium-Low | Partner with them rather than fight; offer the productisation layer |
| Weather data licensing changes (BoM commercialisation, ECMWF restrictions) | Medium | Multi-source architecture; Open-Meteo as primary commercial fallback |
| Climate adaptation reduces vine plantings | Low-Med | Adaptation actually *increases* demand for this product |
| AWRI / Wine Australia builds in-house | Low | They publish R&D, not products; smoke-taint commercialisation goes via Goanna Ag |
| Rob's domain expertise gap (data engineer ≠ viticulturist) | High | Co-founder must close this; or close advisor (Liz Riley / Mary Retallack / DPI) |
| Bootstrapped capital constraints during 2-yr ARR ramp | High | Maintain a stripped MVP; treat first 50 customers as paid pilots |
| Smoke-taint go-to-market clash with Goanna Ag's WISD | Medium | Partner from day one; integrate their feed, don't replicate |

### 8.3 Why hasn't this been built yet?

Multiple structural reasons:
- **Narrow audience (~250k global vineyards) + high required domain depth** discourages generalist VCs and generalist agtech founders.
- **Each region has bespoke regulation, cultivar, climate, and disease pressure**, raising the marginal cost of every new market.
- **Existing vineyard ERPs (Vintrace, InnoVint) are sticky and "good enough" for owners**, and most growers' viticultural decision support today is a regional consultant + a Davis weather station + intuition.
- **Climate intelligence had to mature first** — only since ECMWF AIFS / Pangu-Weather / GraphCast (2023–2024) has *cheap* hyperlocal forecasting become practical.
- **Australian R&D was scaffolded by levy bodies** — Wine Australia + La Trobe + AWRI did the science; they didn't build the product.

This argues the timing is now — exactly the post-research, pre-commercial moment that catalysed Climate Corp 2008–2012.

### 8.4 Will AI / LLMs change the game?

Yes, in two specific ways:
1. **Conversational vineyard advisor** — "Should I spray tonight given the forecast and yesterday's leaf wetness?" answered by a RAG system grounded in the customer's block history + AWRI fact sheets is a genuine 10× UX improvement and a direct moat against legacy ERPs.
2. **Foundation weather models** — GraphCast (Google DeepMind), Pangu-Weather (Huawei), and ECMWF AIFS are radically cheaper to run than physics-based NWP and scaling laws are still in our favour. Build the platform such that swapping out the forecast model is one config change, not a re-platforming.

### 8.5 Likely acquirers in 5–7 years

| Acquirer | Strategic logic | Probability |
|---|---|---|
| Bayer / Climate FieldView | Specialty-crop expansion vector | Med |
| Corteva (Granular descendant) | FMS playbook in vineyards | Med |
| Syngenta (Cropwise) | Vineyards strategic | Med |
| John Deere | Controls hardware to block | Low–Med |
| BASF (xarvio) | Already partners with Sencrop/Pessl | Med |
| DTN | Weather + ag data | Med |
| Treasury Wine Estates | Operational moat — own the intelligence layer | Low–Med |
| Pernod Ricard | Same | Low |
| AWRI / Wine Australia | Statutory acquirer; rare but possible | Low |
| Sencrop / Pessl | Vertical integration into software | Med |
| iTK (Vintel) | Defensive | Med |
| Vintrace / Encompass | Adjacent ERP layer | Med |
| Onside (NZ) | Adjacent vineyard SaaS | Low |
| Goanna Ag | Natural AU consolidator if they raise VC | Med |
| A weather company (Tomorrow.io, Meteomatics) | "Specialty crop" vertical | Med |

---

## 9. Recommendations & Roadmap

### 9.1 Is this a real opportunity?

**Yes, with strong qualifications.** It is a real, defensible, *base-case A$5M-ARR-in-5-years* opportunity in Australia and NZ, with a credible path to a US$20–40M strategic acquisition. It is **not** a venture-scale "Climate Corp 2.0" unless you raise capital and expand to specialty crops. The bootstrapped + owner-operator profile fits the base case very well.

### 9.2 Top 3 viable wedges

1. **Hyperlocal disease pressure + spray decision support for Australian boutique-to-mid commercial vineyards.** Replace the WaaS pilot. Anchor product. Initial 200 paying boutique vignerons in NSW + Vic + SA + WA + Tas in 18 months.

2. **Smoke-taint + bushfire/inversion alert system** — partnered with La Trobe/Goanna Ag's WISD as the hardware/sensor layer; you provide the SaaS dashboard, multi-property aggregation, and risk-prediction layer plugged into the broader vineyard platform. The federal AEA grant for WISD commercialisation makes this a high-priority strategic alliance, not a competitor.

3. **Frost prediction for cool-climate regions** (Orange, Tumbarumba, Tasmania, Adelaide Hills, Mornington, Yarra Valley, Macedon Ranges) — sub-block-resolution radiation-frost forecasting is genuinely missing from the market and is the highest-impact decision for cool-climate growers (10–60% yield loss when missed).

These three integrate naturally — same data, same backend, three different UI surfaces.

### 9.3 18-month MVP roadmap

| Months | Deliverable |
|---|---|
| **0–3** | Founding team locked. Architecture decided (per Section 4). Vintage at Word of Mouth used as Reference Customer #1. Ingest ACCESS-G/C + SILO + Open-Meteo. Build PWA shell with MapLibre + map tile pipeline. |
| **3–6** | Implement DMCast + Gubler-Thomas + Botrytis + Caffarra-Eccel/GFV phenology. Integrate Davis WeatherLink API. 5 design-partner vineyards in Orange + Mudgee + Hilltops. Daily disease-pressure email. |
| **6–9** | Smoke-taint risk dashboard (using PurpleAir + BoM + ACCESS-C wind-trajectory + WISD/GoWISD partnership feed). Sentinel-2 NDVI/EVI overlay. Public free tier launch. |
| **9–12** | Estate tier (multi-block, multi-user, alerting, integrations). 30 paying boutique customers. ASVO + Outlook + ORVA conference presence. |
| **12–15** | Commercial tier alpha with 1–2 mid-commercial customers. Spray-record export (Vintrace, AWRI MRL compliance). Mobile push alerts via Capacitor. |
| **15–18** | NZ + first US west coast (Sonoma/Oregon) pilot. 100–200 paying customers, A$200–400k ARR. Decide whether to seek seed (A$1–3M) for international expansion or to remain bootstrapped. |

### 9.4 Recommended team

- **Rob (CEO/CTO/Founder).** Data architecture, product, capital strategy. Living in the customer (Word of Mouth) gives unmatched product feedback.
- **Co-founder, viticulture / viticulturalist (CPO equivalent).** Critical hire. Profile: 10+ yrs viticulture, regional consulting credibility, AWRI/ASVO network. Could be a senior viticulturist from a regional consultancy, an ex-DPI viticulture officer (like a peer of Darren Fahey), or a senior vineyard manager from a Treasury/Accolade who wants out of corporate.
- **First 3 hires** (months 6–18): (1) full-stack engineer with PWA + maps experience, (2) ML engineer with time-series/weather ML background, (3) GTM lead with AU wine-industry rolodex.
- **Advisors:** AWRI (Mark Krstic or Eric Wilkes), La Trobe (Ian Porter), NSW DPI (Darren Fahey or Suzy Rogiers), regional consultant (Liz Riley), an experienced agtech founder (e.g. one of the AgriWebb or Onside founders).

### 9.5 Funding strategy

- **Year 0–1:** Bootstrapped from Rob's resources + sweat equity + first paying-pilot revenue. Aim: A$0–250k self-funded; cash-flow break-even on operating cost by month 18.
- **Optional seed (Year 2):** A$1–3M seed only if international expansion is on the table. AU agtech VCs to consider: Tenacious Ventures, GrainInnovate, Telstra Ventures, Investible. Strategic angels: AgriWebb founders, Onside founders, AWRI alumni.
- **Government grants to actively pursue:** Australian Economic Accelerator (AEA — same program funding WISD), Wine Australia Innovation Connections, Cooperative Research Centres - Project (CRC-P), Export Market Development Grant (EMDG), R&D Tax Incentive.

### 9.6 Top 5 risks and mitigations

1. **Domain credibility gap.** *Mitigation:* lock in the viticulturist co-founder before product launch; AWRI/La Trobe/DPI advisor relationships; publish a peer-reviewed validation paper in Aus J Grape & Wine Research or AJEV in year 2.
2. **Customer acquisition cost in a fragmented industry.** *Mitigation:* PLG free tier; regional-association partnerships; the Word of Mouth cellar door as a permanent demo.
3. **Sustaining model accuracy across regions.** *Mitigation:* ensemble approach (don't bet on one model); transparently publish skill/error metrics ("forecast verification" page like PredictWind); allow customers to calibrate their own thresholds.
4. **Cashflow shock during AU drought / industry contraction.** Australian wine is in a contraction cycle (2024 second-lowest crush in a decade). *Mitigation:* serve diversified regions; build a NZ + USA toehold by month 18; price boutique tier accessibly.
5. **Goanna Ag / Sencrop pivots into the same space.** *Mitigation:* deep integrations make you their partner not their competitor; ship features they aren't building (LLM advisor, multi-region commercial tier).

### 9.7 Realistic 3-yr / 5-yr ARR scenarios

| | Yr 1 | Yr 3 | Yr 5 |
|---|---|---|---|
| **Bear** (AU only, slow PLG) | A$80k | A$700k | A$2.0M |
| **Base** (AU + NZ + early US west coast) | A$150k | A$1.5M | US$5M (~A$7.5M) |
| **Bull** (above + commercial tier traction + light VC) | A$300k | A$3M | US$15M+ (~A$22M) |

Cash-flow break-even (Base) ~ month 18; meaningful profitability ~ month 30; potential strategic exit window ~ year 5–7 at the US$20–80M range.

---

## 10. Synthesis — the One-Paragraph Investment Thesis

A Staff/Principal-grade data engineer who is also operating a boutique vineyard at the heart of NSW's cool-climate wine region is structurally one of the very few people on earth who can simultaneously (a) build the deeply-integrated, multi-source weather + phenology + disease + smoke + spray-decision platform vineyards need, (b) sell it credibly to peer growers, and (c) productise the work that government bodies (NSW WaaS), academic researchers (La Trobe/AWRI), and overseas niche players (Vintel, VitiMeteo, Sencrop) have started but not finished. The market is real but bounded, the moat is buildable through model-calibration + network-effect data + brand, the architecture is unusually amenable to a tiny team running on Postgres + TimescaleDB + Cloudflare + Hetzner at sub-$1.5k/month, and the realistic outcome is a **A$5–10M ARR business in 5 years with a credible US$20–80M strategic exit**. The single biggest risk is the domain-knowledge co-founder; the second is moving fast enough on the smoke-taint partnership with Goanna Ag and the institutional-distribution partnership with NSW Wine / Wine Australia / AWRI before someone else does. Build it.
