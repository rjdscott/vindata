# Canopy MVP — Mt Canobolas Demo

**Prepared for:** Rob — Word of Mouth Wines incoming proprietor
**Demo target:** Cargo Road Wines dinner, ~14 days from today
**Goal:** Live AWS-deployed, publicly-URLed dashboard demonstrating historical, current, and forecast viticultural intelligence for the Mt Canobolas cluster — at higher resolution and lower latency than NSW Wine's WaaS pilot.

> **Working name: "Canopy"** — feel free to rename. It needs to be memorable to vignerons, defensible as a domain, and not collide with VitiCanopy (the Adelaide Uni research app). Suggested alternates: `Vinemet`, `Terroir.io`, `Cuvée Climate`, `Ridgeline`, `1K High` (ties to your dinner-series brand).

---

## 1. Demo Narrative — what the dinner needs to feel like

The dinner is half pitch, half peer-respect-building. Tom Ward (ORVA), the Cargo Road team, and any neighbours present need to walk away with three impressions, in order:

1. **"This is gorgeous."** A Windy/PredictWind-grade map of Mt Canobolas with their vineyard pin lights up, traffic-lights for disease/frost/spray flick on, and a 7-day decision panel slides in. They have never seen viticultural data presented this well.
2. **"This is real."** Click through to *their* block. Show the data lineage — ACCESS-C 1.5km vs ECMWF AIFS vs GFS side-by-side, ground-truthed against the closest BoM AWS station, with a "skill score" panel. Vignerons distrust black boxes; transparency is the trust accelerant.
3. **"This decides things for me."** A "tonight's spray window" card with concrete output — `DeltaT 4.2°C, no rain forecast 36h, downy mildew pressure HIGH (DMCast), powdery LOW (Gubler-Thomas), recommended action: spray window opens 18:00–22:00 tonight`. This is the moment they ask "when can I have it?"

Everything else is supporting cast. **Build for these three moments.**

---

## 2. The 10 Mt Canobolas Demo Sites

The cluster is the volcanic eastern slope of Mount Canobolas, where elevation drives the cool-climate signature. Coordinates approximate; lock in exact lat/lon during week 1 (Day 2 task).

| # | Vineyard | Location | Approx elevation | Note |
|---|---|---|---|---|
| 1 | **Word of Mouth Wines** | 42 Wallace Lane, Canobolas | 1,030 m | Your reference site; Davis station Day 1 |
| 2 | **Mayfield Vineyard** | Wallace Lane | ~950 m | Direct neighbour; events transformation blueprint |
| 3 | **Ross Hill Wines** | Wallace Lane | ~950 m | Wallace Lane neighbour; carbon-neutral certified |
| 4 | **Cargo Road Wines** | 763 Cargo Rd, Lidster | ~870 m | The dinner host. WaaS pilot virtual station #1 in Orange |
| 5 | **Philip Shaw Wines** | Caldwell Lane (Hervey's Range) | ~900 m | WaaS pilot virtual station #2 in Orange (Pinnacle Rd cluster) |
| 6 | **Brangayne of Orange** | 837 Pinnacle Rd | ~1,000 m | Same Pinnacle Rd ridge |
| 7 | **Borrodell Vineyard** | Lake Canobolas | ~1,000 m | Highest commercial vineyard in NSW, claim-of-fame |
| 8 | **Heifer Station Wines** | Pinnacle Rd | ~890 m | Mid-range neighbour |
| 9 | **Patina Wines** | Lake Canobolas Rd | ~900 m | Gerald Naef; long-time region figure |
| 10 | **Swinging Bridge** | Cnr Canowindra/Calare | ~700 m | Tom Ward's site (ORVA president) — your highest-priority industry contact |

The cluster spans ~330m of vertical relief inside ~25km — which is *exactly* the case where 5km BoM postcode forecasts fail and a 250m hyperlocal layer earns its keep. **This is your demo's central technical narrative.**

---

## 3. MVP Scope — In / Out

### IN scope (must ship in 14 days)

- **One AWS-deployed Next.js dashboard** behind a custom domain (e.g. `canopy.farm`, `canopy.wine`, `1khigh.app` — register Day 1).
- **10 vineyard sites** modelled as polygon-bounded "blocks" (single block per site for the demo; multi-block schema in place for post-demo expansion).
- **Three data layers per site:**
  - *Historical* — 5-year SILO daily climatology (rainfall, Tmin/Tmax, ET₀, RH, solar exposure).
  - *Current* — last 24h hourly observations from the nearest BoM AWS station + closest Davis WeatherLink (yours) + PurpleAir PM2.5.
  - *Forecast* — 7-day hourly from Open-Meteo (which natively blends BoM ACCESS-G, ECMWF AIFS, GFS, ICON for any lat/lon — no need to wrangle GRIB files for the demo).
- **Five viticultural models live and visible:**
  1. **GDD / phenology** (Winkler base 10°C; current vintage vs 5-yr mean; predicted budburst→flowering→véraison→harvest)
  2. **DMCast** downy mildew pressure (primary + secondary infection windows)
  3. **Gubler-Thomas** powdery mildew risk index (UC Davis)
  4. **Broome / Gubler-Bettiga** botrytis risk (bunch closure → véraison)
  5. **Frost risk** (radiation cooling index based on dewpoint, wind, cloud cover, soil moisture)
- **Two decision tools:**
  - **Spray window finder** — DeltaT + rain wash-off + 24h withholding visualisation
  - **Smoke-taint risk panel** — PM2.5 trajectory from PurpleAir + ACCESS-C wind direction (visual only for demo; real WISD partnership comes later)
- **Map view** (MapLibre + 250m forecast tile overlay for temperature / RH / disease pressure) and **Site detail view** (tabs: Historical, Now, 7-Day, Models).
- **Mobile/iPad responsive** — vignerons will ask to see it on their phones at the dinner.

### OUT of scope (defer post-demo)

- Multi-tenant auth / billing (use a shared password gate or unauth public for the demo)
- Customer self-onboarding
- IoT station ingest beyond your own Davis (manual integration only for WOM)
- Sentinel-2 NDVI overlay (impressive but high build cost; defer to Month 2)
- LLM advisor (Month 3+)
- Mobile push notifications (use email digests if anything)
- Yield forecasting
- Drone / VineView integration
- Compliance / spray-record export
- Multi-region (everything beyond Mt Canobolas)

---

## 4. Data Sources — every endpoint, every cost

The discipline here is to **avoid GRIB wrangling** for the demo. Open-Meteo already does for free what would otherwise take you 4 days to build. SILO already has its archive on AWS S3 Open Data — no need to scrape `silo.longpaddock.qld.gov.au`.

| Source | What you get | Endpoint / SDK | Cadence | Cost (demo) | Use |
|---|---|---|---|---|---|
| **Open-Meteo Forecast API** | 7-day hourly forecast: temp, RH, wind, precip, cloud, solar, dewpoint, soil temp/moisture; ensemble of ACCESS-G, ECMWF, GFS, ICON, AIFS for any lat/lon | `https://api.open-meteo.com/v1/forecast` | Hourly pull | Free non-commercial; €29/mo commercial tier when ARR justifies | **Primary forecast source** — the 4-day accelerator |
| **Open-Meteo Historical API** | ERA5 + ERA5-Land hourly back to 1940 | `https://archive-api.open-meteo.com/v1/archive` | One-shot backfill, weekly top-up | Free | 5-year baseline at each site |
| **SILO (Long Paddock, QLD Govt)** | Australian gridded daily climate 1889–yesterday; 5km; rainfall + Tmin/Tmax + RH + ET₀ + radiation | `s3://silo-open-data/Official/annual/` (Parquet/NetCDF on AWS Open Data Registry) | One-shot backfill, daily increment | Free (AWS Open Data — no egress when reading from same region) | Authoritative AU historical baseline |
| **BoM AWS observations** | Hourly station obs from the closest BoM stations to each site | BoM FTP `ftp://ftp.bom.gov.au/anon/gen/fwo/` for IDV60901 + IDN60801 (NSW); or via `weatherOz` R-package logic ported to Python | Every 30 min | Free (with attribution; commercial use ambiguous — defer commercial use to post-demo) | Ground-truth observations |
| **PurpleAir** | Real-time PM2.5 from citizen sensors; coverage in Orange varies but Bathurst, Lithgow, Sydney West are dense | `https://api.purpleair.com/v1/sensors` | Every 10 min | Free read API with key | Smoke-taint proxy + real-time AQI |
| **OpenAQ** | Aggregated AU air quality (NSW EPA stations: Bathurst, Orange when available) | `https://api.openaq.org/v3/locations` | Hourly | Free | Smoke-taint cross-check |
| **Davis WeatherLink Cloud** | Your station at WOM, hosted | `https://api.weatherlink.com/v2/` | Every 15 min | Free with WeatherLink Cloud sub | Live ground-truth at WOM |
| **NASA POWER** | Daily ag weather (Tmin/Tmax/Tdew/RH/wind/solar/precip) | `https://power.larc.nasa.gov/api/temporal/daily/point` | Daily | Free | Sanity-check fallback |
| **Geoscape Buildings** (optional) | High-res property boundaries | Geoscape API | One-shot | Free for research; paid commercial | Polygon-accurate vineyard boundaries — defer |
| **MapTiler / Stadia / Cloudflare** | Map base tiles | API | On-demand | $0–25/mo at demo scale | MapLibre base layer |

**Architectural rationale for using Open-Meteo as the primary forecast source for the MVP:** building a direct ingest from BoM ACCESS-C THREDDS is a 4-day job (NetCDF/GRIB parsing, regridding, downscaling). Open-Meteo already does this for ACCESS-G + ECMWF + GFS + ICON + AIFS, exposes a clean JSON API per lat/lon, and returns a multi-model ensemble. For the demo, this is a 90% solution at 10% effort. The architecture leaves a clean swap-out point for direct BoM ingest in Month 2 when the additional control matters.

---

## 5. AWS Architecture — the boring, single-operator-friendly version

The principle is: use **boring managed services that don't page you at 2am during vintage**. Specifically, no Kinesis, no MSK, no SageMaker, no Step Functions Express, no EKS. The architecture is:

```
                    ┌──────────────────────────────────────────────┐
                    │  EventBridge Scheduler (cron)                │
                    │   ├─ open-meteo-forecast  (every 1h)         │
                    │   ├─ silo-daily-update    (daily 06:00)      │
                    │   ├─ bom-aws-obs          (every 30min)      │
                    │   ├─ purpleair-pull       (every 15min)      │
                    │   ├─ davis-weatherlink    (every 15min)      │
                    │   └─ run-vit-models       (every 1h)         │
                    └──────────────────────┬───────────────────────┘
                                           │ invokes
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │  AWS Lambda (Python 3.12, container image)   │
                    │  Single repo, multi-handler                  │
                    │  Memory: 1024 MB, Timeout: 5 min             │
                    └──────────────────────┬───────────────────────┘
                                           │ writes / reads
                          ┌────────────────┴────────────────┐
                          ▼                                 ▼
              ┌────────────────────────┐    ┌────────────────────────┐
              │  RDS PostgreSQL 16     │    │  S3 (canopy-data)      │
              │  + TimescaleDB ext.    │    │  ├─ raw/open-meteo/    │
              │  + PostGIS ext.        │    │  ├─ raw/silo/          │
              │  db.t4g.medium         │    │  ├─ raw/bom/           │
              │  Multi-AZ: NO (demo)   │    │  ├─ models/output/     │
              │  20 GB gp3             │    │  └─ tiles/forecast/    │
              └─────────┬──────────────┘    └────────────┬───────────┘
                        │                                │
                        │ reads (Tanstack Query)         │ tile fetch
                        │                                │
              ┌─────────▼──────────────┐    ┌────────────▼───────────┐
              │  AWS App Runner        │    │  CloudFront            │
              │  (Next.js 15 SSR)      │    │  (caches S3 tiles)     │
              │  0.25 vCPU, 0.5 GB     │    └────────────┬───────────┘
              └─────────┬──────────────┘                 │
                        │                                │
                        └────────────┬───────────────────┘
                                     │
                              ┌──────▼──────┐
                              │  Route 53   │
                              │  + ACM TLS  │
                              └──────┬──────┘
                                     │
                                  Internet
                                     │
                                     ▼
                              vignerons' phones
```

### Service-by-service rationale

| AWS service | Choice | Why this, not the alternatives |
|---|---|---|
| **Compute (jobs)** | Lambda with container images | Free tier covers MVP. Container image (vs zip) gives you NumPy, SciPy, GDAL, xarray without layer hell. ECS Fargate is the right step-up at month 3 if a job runs >15 min — for the demo, none will. |
| **Compute (web)** | App Runner | Zero-ops Next.js hosting. Cheaper than ECS Fargate for a single small service, simpler than Amplify for SSR routes. ~$25/mo idle. Alternative: Amplify Hosting if you want SSG-only — but you want SSR for fresh data. |
| **Database** | RDS PostgreSQL 16 + TimescaleDB + PostGIS | The triple stack from the research report. `db.t4g.medium` (2 vCPU, 4 GB) at ~$60/mo handles MVP and 200 customers. Single-AZ for the demo — flip Multi-AZ only post-launch. *Aurora Serverless v2 is tempting but TimescaleDB is not supported on Aurora — this is a hard constraint.* |
| **Time-series store** | Inside same Postgres (TimescaleDB hypertables) | Amazon Timestream is purpose-built and would work, but you double your data plane and lose joins between sensor data and vineyard blocks. TimescaleDB on RDS is the right answer for a 1-person team. |
| **Object storage** | S3 + CloudFront | Standard. Use Intelligent-Tiering for raw weather archives. R2 (Cloudflare) is cheaper but you committed to AWS. |
| **Scheduler** | EventBridge Scheduler | Replaced CloudWatch Events Rules in 2022; supports cron, time zones, retries, DLQ. Native, free at MVP volume. |
| **Secrets** | AWS Secrets Manager | $0.40/secret/mo. Store API keys for Open-Meteo, PurpleAir, Davis. |
| **DNS / TLS** | Route 53 + ACM | $0.50/mo + free certs. |
| **Observability** | CloudWatch Logs + Metrics; one custom dashboard | No Datadog. No New Relic. CloudWatch is sufficient at MVP volume. |
| **Auth** | Defer; Cognito later | For the demo, gate the URL with a Lambda@Edge basic-auth check (5 lines) or use a Cloudflare Access wrapper if domain DNS is on Cloudflare. |
| **CI/CD** | GitHub Actions → ECR → Lambda update / App Runner deploy | Free for public repos; $0–4/mo for private. |
| **IaC** | AWS CDK (TypeScript) | One language for infra and frontend. CloudFormation under the hood. Terraform is fine but CDK is faster for solo. |

### What's deliberately absent

- **No MSK / Kinesis / Kafka.** Volume doesn't justify it. Lambda + cron is fine.
- **No EKS / ECS for ingestion.** Lambda container images cover all jobs.
- **No SageMaker.** Models run as Python in Lambda. Mechanistic models are <500 lines each.
- **No Step Functions.** Job orchestration is "Lambda invokes Lambda via SQS or just runs sequentially" — Step Functions is overkill for 6 daily jobs.
- **No DynamoDB.** Postgres is the single source of truth. Less cognitive overhead.
- **No CloudFront for the API.** App Runner has TLS termination; CloudFront in front of an SSR app adds cache-invalidation pain for no benefit at this scale.

---

## 6. Database Schema — the hypertables that matter

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS h3 CASCADE;

-- Reference / dimension tables
CREATE TABLE region (
  id           SERIAL PRIMARY KEY,
  name         TEXT NOT NULL,         -- e.g. 'Orange', 'Mt Canobolas'
  geom         GEOMETRY(POLYGON, 4326)
);

CREATE TABLE vineyard (
  id           SERIAL PRIMARY KEY,
  region_id    INT REFERENCES region(id),
  name         TEXT NOT NULL,
  owner        TEXT,
  centroid     GEOMETRY(POINT, 4326),
  elevation_m  REAL,
  h3_r10       H3INDEX        -- 65m hex cell — for forecast joins
);

CREATE TABLE block (
  id              SERIAL PRIMARY KEY,
  vineyard_id     INT REFERENCES vineyard(id),
  name            TEXT NOT NULL,
  variety         TEXT,
  rootstock       TEXT,
  planting_year   INT,
  area_ha         NUMERIC(6,3),
  geom            GEOMETRY(POLYGON, 4326)
);

-- Forecast & observation hypertables
CREATE TABLE weather_forecast (
  vineyard_id   INT NOT NULL REFERENCES vineyard(id),
  model         TEXT NOT NULL,       -- 'access_g', 'ecmwf_aifs', 'gfs', 'icon', 'open_meteo_blend'
  issued_at     TIMESTAMPTZ NOT NULL,
  forecast_at   TIMESTAMPTZ NOT NULL,
  temp_c        REAL,
  rh_pct        REAL,
  wind_ms       REAL,
  wind_dir_deg  REAL,
  precip_mm     REAL,
  cloud_pct     REAL,
  solar_wm2     REAL,
  dewpoint_c    REAL,
  PRIMARY KEY (vineyard_id, model, issued_at, forecast_at)
);
SELECT create_hypertable('weather_forecast', 'forecast_at', chunk_time_interval => INTERVAL '7 days');

CREATE TABLE weather_observation (
  vineyard_id   INT NOT NULL REFERENCES vineyard(id),
  source        TEXT NOT NULL,       -- 'silo', 'bom_aws:063292', 'davis:wom1', 'purpleair:12345'
  observed_at   TIMESTAMPTZ NOT NULL,
  temp_c        REAL,
  rh_pct        REAL,
  wind_ms       REAL,
  precip_mm     REAL,
  solar_wm2     REAL,
  pm25_ugm3     REAL,
  leaf_wetness_min INT,
  PRIMARY KEY (vineyard_id, source, observed_at)
);
SELECT create_hypertable('weather_observation', 'observed_at', chunk_time_interval => INTERVAL '30 days');

-- Compress chunks older than 14 days
ALTER TABLE weather_forecast SET (timescaledb.compress, timescaledb.compress_segmentby = 'vineyard_id, model');
SELECT add_compression_policy('weather_forecast', INTERVAL '14 days');

ALTER TABLE weather_observation SET (timescaledb.compress, timescaledb.compress_segmentby = 'vineyard_id, source');
SELECT add_compression_policy('weather_observation', INTERVAL '90 days');

-- Model output hypertable
CREATE TABLE model_output (
  vineyard_id   INT NOT NULL REFERENCES vineyard(id),
  model_name    TEXT NOT NULL,       -- 'dmcast', 'gubler_thomas', 'botrytis', 'gdd', 'frost_risk', 'spray_window'
  computed_at   TIMESTAMPTZ NOT NULL,
  valid_from    TIMESTAMPTZ NOT NULL,
  valid_to      TIMESTAMPTZ NOT NULL,
  risk_level    TEXT,                -- 'low', 'moderate', 'high', 'extreme'
  numeric_score REAL,
  details       JSONB,
  PRIMARY KEY (vineyard_id, model_name, computed_at, valid_from)
);
SELECT create_hypertable('model_output', 'computed_at', chunk_time_interval => INTERVAL '30 days');

-- Continuous aggregate: hourly to daily for fast historical chart queries
CREATE MATERIALIZED VIEW weather_obs_daily
WITH (timescaledb.continuous) AS
SELECT
  vineyard_id, source,
  time_bucket('1 day', observed_at) AS day,
  AVG(temp_c) AS temp_c_avg,
  MIN(temp_c) AS temp_c_min,
  MAX(temp_c) AS temp_c_max,
  SUM(precip_mm) AS precip_mm_sum,
  AVG(rh_pct) AS rh_pct_avg
FROM weather_observation
GROUP BY vineyard_id, source, day;

SELECT add_continuous_aggregate_policy('weather_obs_daily',
  start_offset => INTERVAL '90 days',
  end_offset => INTERVAL '1 hour',
  schedule_interval => INTERVAL '1 hour');
```

This schema scales cleanly from your 10 demo vineyards to 5,000+ without redesign.

---

## 7. The Five Models — what to implement

Each model is mechanistic, peer-reviewed, and implementable in <300 lines of Python. **Do not use ML for the demo.** Mechanistic models are auditable and defensible to viticulturists; ML is a Month 4+ addition. Cite the paper in your UI tooltip — viticulturists love this.

### 7.1 GDD / Phenology (Caffarra-Eccel + GFV)

**Algorithm:** Daily Growing Degree Days at base 10°C (Winkler), accumulated from October 1 (Southern Hemisphere). Phenology stages predicted via the **Grapevine Flowering–Veraison (GFV) model** of Parker et al. (2011, 2013) using F* parameters per cultivar (published table for ~100 cultivars including Pinot Noir, Chardonnay, Riesling, Pinot Gris, Grüner Veltliner, Mencia, Petit Manseng).

**Output:** Current GDD vs 5-year-mean curve; predicted dates of budburst, flowering, véraison, harvest with ±confidence band.

**UI:** Big number + sparkline. "You are 12 GDD ahead of 5-yr mean. Predicted flowering: Nov 18 ± 4 days."

### 7.2 DMCast (Downy Mildew)

**Algorithm:** Park, Seem, Magarey, Gadoury (Cornell, 2002). Primary infection requires (a) oospore maturity (cumulative GDD from Jan 1 in NH / Jul 1 in SH passing threshold), (b) ≥10mm rain in 24h, (c) leaf wetness ≥4h at 11–20°C. Secondary infection: ≥4h leaf wetness at 18–25°C with sporulation conditions (RH >95% overnight + wetness).

**Output:** Risk level per 24h forecast hour (low/moderate/high/extreme); list of "next infection-risk windows" in next 7 days.

**Implementation note:** Leaf wetness is rarely measured directly; estimate from RH ≥90% + cloud cover + recent rain (the standard CIMIS/UC Davis approach). Document the proxy in your UI.

### 7.3 Gubler-Thomas Powdery Mildew Risk Index

**Algorithm:** UC Davis. Score 0–100 based on consecutive days with 6+ hours of temperature in 21–29.4°C (70–85°F) range. Score increments by 20 per qualifying day, decrements by 10 per non-qualifying day. ≥60 = high risk; trigger spray.

**Output:** Current index value + 7-day projection.

**Why it matters:** Trivially implementable, widely trusted, used by Pessl FieldClimate and eVineyard — viticulturists will recognise it instantly.

### 7.4 Broome / Gubler-Bettiga Botrytis Risk

**Algorithm:** Risk window from bunch closure to véraison (BBCH 79–85). Risk elevated when (a) leaf wetness ≥15h, (b) avg temp during wetness 15–25°C, (c) cumulative wetness in past 7 days ≥30h.

**Output:** Days in risk; recommended bunch zone airflow / canopy management note.

### 7.5 Frost Risk

**Algorithm:** Radiation-frost index combining (a) forecast Tmin, (b) dewpoint depression at sunset, (c) wind speed (<2 m/s = high radiation risk), (d) cloud cover (<30% = high risk), (e) soil moisture (low SM = lower thermal mass).

For the demo, a simple 0–100 score with traffic-light cut-offs is sufficient. The serious version (terrain-modulated cold-air pooling using elevation + a digital elevation model) is a Month 2 add.

**Output:** "Frost risk: HIGH at Word of Mouth (1,030m). Advice: Frost fan check by 22:00; fans on at 1.5°C trigger."

### Bonus: Spray Window Finder (decision tool, not a model)

**Algorithm:** Combine `DeltaT = Tdry - Twet` (target 2–8°C; <2 = drift, >8 = evaporation), 24h rain wash-off forecast, withholding period from spray record (or default 14 days), wind speed (<10 km/h ideal). Render next 168h as a 24×7 heatmap of "sprayable hours."

**Output:** "Tonight 18:00–22:00: SPRAY WINDOW (DeltaT 4.2, no rain 36h, wind 6 km/h). Next: Tue 06:00–10:00."

### Bonus: Smoke-Taint Risk Panel

**For the demo, a *visualisation*, not a true model.** Pull PurpleAir PM2.5 from sensors within 100km, overlay ACCESS-C wind trajectory, show 24-h trend. The actual smoke-taint dose model (Favell et al. 2021; AWRI thresholds) is Month 3+ when you partner with Goanna Ag / La Trobe on WISD.

**Demo line:** *"Today's smoke baseline: 4 µg/m³. Threshold of concern from AWRI: 20 µg/m³ over 4 hours. We'd alert you the moment fires within 200km change wind direction toward the cluster."*

---

## 8. Frontend — what gets built

**Stack:** Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui + MapLibre GL + Tanstack Query + Recharts.

**Pages (route → purpose):**

- `/` — landing/map view. MapLibre map of Mt Canobolas with 10 vineyard pins; each pin shows current traffic-lights for the 5 models. Layer toggles: Temperature / RH / Disease pressure / Frost risk. **This is the wow moment.**
- `/site/[slug]` — site detail. Header card with name, elevation, nearest BoM station; 4 tabs:
  - **Now** — current obs from Davis/BoM/PurpleAir; current model traffic-lights; "what's happening right now" prose.
  - **7-Day Forecast** — hourly chart (temp, RH, precip, wind); ensemble side-by-side (ACCESS-G vs ECMWF AIFS vs GFS); model risk projections.
  - **Historical** — 5-yr GDD curve overlay with current vintage; rainfall + ET₀ totals YTD; vintage comparison ("2025/26 vs 2023/24 most-similar vintage").
  - **Decisions** — spray window, frost alert, smoke risk, model details (with paper citations).
- `/methodology` — one page explaining data sources and models. **This is your trust accelerant — viticulturists will read this.**
- `/about` — your story. Grower-built, in Orange, on Mt Canobolas.

**Key components to nail:**
- Traffic-light pill (`<RiskPill level="high" />` — colour + icon + tooltip)
- Ensemble chart (overlaid forecast lines per model + observed)
- Phenology timeline (horizontal stage bar with current position)
- Spray window heatmap (7×24 grid, green = spray, red = don't)
- Map pin with mini risk-summary on hover

**Performance targets:**
- Largest Contentful Paint <2s on 4G
- Map first interaction <3s
- API responses <300ms (App Runner → RDS via VPC; Tanstack Query cache)

---

## 9. The 14-Day Build Plan

Realistic for a senior data engineer working evenings + weekends. Buffer one weekend day at end for slippage. **Do not start the frontend before Day 6** — the temptation is real but data discipline first.

| Day | Focus | Output | Exit criterion |
|---|---|---|---|
| **1 (Sat)** | AWS account, IAM, domain, CDK skeleton, GitHub repo, ECR, RDS provisioned | Empty infra, deployable hello-world Lambda, RDS reachable | `cdk deploy` works; can `psql` into RDS |
| **2 (Sun)** | Schema (Section 6) applied; 10 vineyards seeded with verified lat/lon and elevations; PostGIS sanity checks | Database has reference data | `SELECT * FROM vineyard` returns 10 rows with valid geoms |
| **3 (Mon)** | Open-Meteo forecast ingest Lambda; hourly EventBridge schedule; 10×7×24 = 1,680 forecast rows landing per cycle | Forecasts in DB | `SELECT COUNT(*) FROM weather_forecast` ≥ 1,680 fresh hourly |
| **4 (Tue)** | SILO historical backfill (5 years × 10 sites via S3 Open Data NetCDF → pandas → COPY into Postgres) | 5-yr daily history per site | `weather_obs_daily` continuous aggregate populated |
| **5 (Wed)** | BoM AWS station ingest (closest station per site — likely 063292 Orange Airport for most); PurpleAir + Davis WeatherLink ingest | Live obs flowing | All three sources writing to `weather_observation` |
| **6 (Thu)** | Models 1+2 (GDD/phenology + DMCast) implemented and scheduled hourly | Model outputs landing | `model_output` has GDD + DMCast for all 10 sites |
| **7 (Fri)** | Models 3+4+5 (Gubler-Thomas + Botrytis + Frost) | All five models live | All 10 sites × 5 models = 50 traffic-lights computable |
| — | **End of Week 1 — checkpoint.** Data is the hard part. If behind, cut the smoke-taint visualisation and one of Botrytis/Frost. |
| **8 (Sat)** | Next.js scaffold; Tailwind + shadcn; auth gate (basic-auth Lambda@Edge); App Runner deployed | Empty shell at custom domain with TLS | Live URL loads, auth works |
| **9 (Sun)** | Map view (`/`) with MapLibre + 10 pins + risk-pill overlay | Wow page #1 | Pins clickable, risk-pills correct |
| **10 (Mon)** | Site detail page — Now tab + 7-Day Forecast tab with ensemble chart | Wow page #2 | All 10 sites navigable |
| **11 (Tue)** | Historical tab — GDD curve + vintage comparator | Wow page #3 | 5-yr overlay charts working |
| **12 (Wed)** | Decisions tab — spray window heatmap + frost alert + smoke panel + methodology page | Demo-complete | All decision tools render |
| **13 (Thu)** | Polish: mobile/iPad layout, loading states, empty states, error boundaries; CloudWatch dashboard; pre-load demo data | Production-feeling | Open on iPhone — works |
| **14 (Fri — dinner)** | Morning: dry run from cold cache. Afternoon: take screenshots + record 90s walkthrough as fallback. Charge laptop + iPad. | Demo-ready | You eat dinner. |

### Hard-cut prioritisation (if behind on Day 7)

If by EOD Day 7 you have <4 models live, drop in this order: smoke panel → frost → botrytis → Gubler-Thomas. **Always ship DMCast and GDD** — those are the centrepieces.

---

## 10. AWS Cost Estimate

### Demo phase (10 sites, ~50 model runs/day, ~500 ingest invocations/day)

| Service | Spec | Monthly (USD) |
|---|---|---|
| RDS PostgreSQL | db.t4g.medium, 20 GB gp3, single-AZ | $58 |
| RDS storage I/O & backup | ~5 GB backup | $5 |
| Lambda invocations | ~15k/mo, avg 3s, 1024 MB | $3 |
| Lambda container storage (ECR) | 1 GB image | $0.10 |
| App Runner | 0.25 vCPU, 0.5 GB, ~75% idle | $25 |
| S3 storage | 2 GB raw + 5 GB historical | $0.20 |
| CloudFront | <10 GB egress | $1 |
| EventBridge Scheduler | 5 schedules, ~10k invocations | $0 (free tier) |
| Route 53 | 1 hosted zone | $0.50 |
| ACM | TLS cert | $0 |
| Secrets Manager | 4 secrets | $1.60 |
| CloudWatch | Logs + 1 dashboard | $5 |
| Data transfer | <50 GB egress | $4 |
| **Total** | | **~$103/mo** |

### Post-demo, 200 paying customers

Add: scale RDS to db.t4g.large (~$120/mo), enable Multi-AZ (×1.7), move App Runner to 0.5 vCPU/1GB (~$50), enable CloudFront on the API, add Cognito ($55/mo at MAU scale). Total: **~$400–600/mo**, comfortably below the $3k operating budget set in the original architecture proposal.

### Free-tier offsets (first 12 months only)

- 750 hours t-class EC2 (irrelevant — we're not using EC2)
- 1M Lambda requests free
- 5 GB S3
- 50 GB CloudFront egress
- 750 hours RDS db.t3.micro (too small for our needs — we'll pay for t4g.medium)

**Realistic Day-1-of-Year-2 monthly bill: ~$103.** This is genuinely a lifestyle-business compatible cost.

### Pre-paid one-time costs

- Domain: $12–25/yr (Cloudflare Registrar / Route 53)
- Cargo Road dinner cover: $200 (price in)
- Demo iPad if you don't have one: $0 (use laptop)

---

## 11. The Demo Script — 12 minutes max

Vignerons have short attention for software demos at dinner. Twelve minutes is the budget. Rehearse this on Day 13.

### Minute 0–2: The setup (no laptop yet)

> "Last vintage you watched the BoM postcode forecast for Orange and made a spray decision — but Cargo Road sits at 870 metres and Brangayne is at 1,000. The forecast is the same; the actual weather isn't. NSW Wine tried to fix this with WaaS at 90-metre resolution — there are two virtual stations in Orange today, one of them is yours — but the system has been offline for months. So I've been building a replacement. Let me show you what it looks like."

### Minute 2–4: The map (laptop on table)

Open laptop. Map of Mt Canobolas, 10 pins lit. Hover Cargo Road. Show the risk-pills updating live.

> "Every site you can see is being modelled hourly from a blend of BoM ACCESS, ECMWF, and GFS — downscaled to 250 metres. Right now, downy mildew pressure is moderate, powdery is low, and there's a frost watch overnight at the higher sites." [Toggle frost layer — heatmap glows red around Brangayne and Borrodell.]

### Minute 4–7: The site page — Cargo Road

Click Cargo Road. Now tab.

> "Here's what's happening right now at your block — pulled from Davis, BoM Orange Airport, and PurpleAir. Air quality's fine, rainfall is 4mm overnight, leaf wetness 6 hours."

7-Day tab.

> "Forecast — and importantly, ensemble. ACCESS says rain Tuesday; ECMWF AIFS says it tracks south. Here's both, plus GFS. You decide which model to trust based on how they've performed at this elevation in past vintages." [Hover skill score panel.]

### Minute 7–9: The decision

Decisions tab. Spray window heatmap.

> "Here's tonight's spray window. DeltaT is 4.2, no rain forecast for 36 hours, wind under 8 km/h, your last spray was 11 days ago — withholding clear. So tonight 18:00 to 22:00 is your green light. Next opportunity after that is Tuesday 06:00."

### Minute 9–11: The historical narrative

Historical tab. GDD chart.

> "And to put this season in context — you're tracking 12 degree-days ahead of your 5-year average; closest analogue vintage is 2023/24, which you remember was an early flowering. Predicted flowering for your block: November 18, plus or minus four days."

### Minute 11–12: The pitch

> "I'm building this for the Mt Canobolas cluster first because it's where I live and where the forecast resolution problem matters most. I'd love to give you free access through next vintage in return for your feedback. If it works for the ten of you, the rest of Orange is next."

[*Stop talking. Eat dinner.*]

---

## 12. Risks to the 14-Day Timeline

| Risk | Likelihood | Mitigation |
|---|---|---|
| RDS provisioning hiccup, IAM friction, or VPC misconfig burns Day 1 | Medium | Use AWS CDK with the public RDS-in-public-subnet pattern for the demo only — accept the security debt; lock down post-demo |
| BoM AWS scraping breaks or gets rate-limited | Medium | Open-Meteo already aggregates it. Ship without direct BoM ingest if needed; show "BoM via Open-Meteo blend" in the UI |
| Davis WeatherLink API auth complexity | Low | Use the v2 API key + secret pattern; alternatively skip Davis for demo, use Open-Meteo as proxy for WOM |
| Map performance / tile rendering | Low | Use vector tiles from MapTiler free tier; defer custom raster forecast tiles to Month 2 |
| Phenology / disease model edge cases (negative values, missing data) | Medium | Defensive coding + null-handling everywhere; UI shows "—" not 0 |
| You catch a cold the week of the dinner | Low | Day 13 buffer; demo video as fallback |
| Cargo Road cancels the dinner | Low | Use the same dashboard at the next ORVA event with Tom Ward |
| Domain/TLS provisioning takes 24h to propagate | Medium | Register Day 1; ACM cert provisioning is fast but DNS validation can take time |
| App Runner cold-start on demo night | Low | Send curl request 5 min before dinner to warm it |
| Demo Wi-Fi at Cargo Road is bad | High | Tether off your phone; pre-cache the page in the browser |

---

## 13. After the Dinner — the Path to Production

Assuming the demo lands, the immediate next moves are:

1. **Capture feedback formally.** A 30-minute call with each of the 10 demo vineyards in the two weeks following. Record (with permission). This is your customer-discovery gold.
2. **Lock the WaaS conversation.** Email Matthew Jessop at NSW Wine the week after the dinner. Subject line: *"Filling the WaaS gap from Mt Canobolas — would love your input."* Lead with the demo URL, not a pitch.
3. **Goanna Ag introduction.** Cold-email the Goanna Ag team about the GoWISD program with a specific integration proposal (pull their feed, render it on Canopy as a layer). They have nothing to lose; you have everything to gain.
4. **AWRI introduction.** Through Wine Australia's AgTech Hub or directly to Eric Wilkes / Mark Krstic. Bring a peer-review attitude, not a sales pitch.
5. **NSW DPI introduction.** Darren Fahey runs the Angullong AgTech Demonstration Site 45 min from you. Visit. Offer Canopy as a free tool for the demonstration program in exchange for soil/spray/yield data to validate models.
6. **First paid customer.** Likely Cargo Road or Tom Ward (Swinging Bridge). $49/month. Start the metered clock.
7. **Co-founder search.** Section 9.4 of the prior research applies — viticulturist co-founder is now urgent. Liz Riley (Vitibit), Mary Retallack, or a senior Treasury/Accolade vineyard manager looking for an exit.
8. **The two-year acquisition pitch.** If your stated goal is to be acquired by NSW Wine or its successor body — that's a sub-$1M strategic acquisition path. Realistically a more attractive acquirer will be Wine Australia (federal levy body) for inclusion in the AgTech Hub, or commercial: Goanna Ag, Onside, or Vintrace/Encompass. Set quarterly targets toward that — first 50 paying customers, first $250k ARR, first peer-reviewed validation paper in the AJEV.

---

## 14. One-Page Decision Summary

- **Target dinner:** Cargo Road, +14 days
- **Cluster:** 10 Mt Canobolas vineyards
- **Stack:** Next.js + AWS App Runner + Lambda + RDS (Postgres + TimescaleDB + PostGIS) + S3 + EventBridge
- **Data:** Open-Meteo forecast + SILO historical + BoM AWS obs + PurpleAir + Davis (WOM)
- **Models:** GDD/phenology + DMCast + Gubler-Thomas + Botrytis + Frost + spray window
- **Cost:** ~$103/mo at demo scale; ~$400–600/mo at 200 customers
- **Build time:** 14 days for one senior engineer working evenings + weekends
- **Demo:** 12 minutes, three wow moments (map, ensemble forecast, spray window)
- **Post-demo:** Customer-discovery interviews, NSW Wine + Goanna Ag + AWRI + DPI introductions, co-founder search, first paid customer

Build it.
