# Keystone Solid Surfaces - Moraware System Documentation

**Version**: 2.0 | **Last Updated**: December 2025 | **Generated from**: Live System Exploration + Codebase Analysis

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Job Structure](#job-structure)
4. [Workflow & Activity Types](#workflow--activity-types)
5. [Job Forms](#job-forms)
6. [Inventory & Products](#inventory--products)
7. [LeadTracker System](#leadtracker-system)
8. [API Integration](#api-integration)
9. [Settings Architecture](#settings-architecture)
10. [Field Mappings & IDs](#field-mappings--ids)
11. [Common Operations](#common-operations)
12. [Safety Rules & Gotchas](#safety-rules--gotchas)

---

## System Overview

Keystone Solid Surfaces uses Moraware Systemize as their ERP (Enterprise Resource Planning) system for:
- **Job Management**: Tracking all countertop fabrication projects from lead to invoice
- **LeadTracker**: Managing walk-in showroom customers (pre-sales)
- **Scheduling**: Calendar-based activity and crew assignment
- **Inventory**: Material tracking (stone slabs, solid surface sheets, adhesives)
- **Production**: Fabrication workflow from programming to QC to install

### Key URLs
- **Moraware System**: `https://keystonesolidsurfaces.moraware.net/sys/`
- **API Endpoint**: `https://keystonesolidsurfaces.moraware.net/api.aspx`
- **Jobs List**: `/sys/jobs`
- **LeadTracker**: `/sys/jobs/9` (Process ID 9)
- **Settings**: `/sys/settings/`

---

## Architecture

### Three-Layer Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Keystone Pricing Portal                         │
│                   (React + TypeScript Frontend)                     │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Backend Service Layer                            │
│              (Node.js + Express + TypeScript)                       │
│                                                                     │
│  ┌──────────────────┐ ┌────────────────────┐ ┌──────────────────┐   │
│  │morawareApiService│ │morawareFieldMapping│ │morawareWebService│   │
│  │   (1,868 lines)  │ │    (483 lines)     │ │   (818 lines)    │   │
│  └──────────────────┘ └────────────────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
          ┌──────────────────────────────────────┐
          │         Production: Azure Function   │
          │         Development: Local CLI       │
          └──────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    C# CLI (MorawareCli.exe)                         │
│                   .NET Framework 4.8 Wrapper                        │
│                                                                     │
│  Wraps: Moraware.JobTrackerAPI5.dll (Windows-only SDK)              │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Moraware Systemize                             │
│                     (Cloud-based ERP)                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

1. **Moraware SDK is Windows-only** (.NET Framework DLL)
2. **Render.com runs Linux** - Cannot execute Windows binaries
3. **Azure Functions** - Provides Windows runtime for CLI execution in production
4. **Local Development** - Direct CLI execution on Windows dev machines

---

## Job Structure

### Job Detail Page Components

A job in Moraware contains the following sections:

#### 1. Job Info
| Field | Description | Example |
|-------|-------------|---------|
| Job Name | Customer/project name | "Donahoo" |
| Account | Dealer/partner account | "Sherri's Kitchen & Bath" |
| Creation Date | When job was created | "12/11/2025" |
| Salesperson | Assigned sales rep | "Chip Anderson" |
| Job Number | Display number | "20246" |
| Onsite Primary Contact | Primary site contact | "Sherri 816-262-1044" |
| Keystone PM | Project manager | "Jennifer Farris - 316-945-6605" |
| Job Site | Project type | "Remodel", "New Construction" |
| Cabinets | Cabinet status | "New Cabinets", "Existing" |

#### 2. Job Address
- Street address, city, state, zip for installation site
- Separate from Account Address

#### 3. Job Activities (Workflow)
- 16+ activities per job (see [Workflow](#workflow--activity-types))
- Each has: Status, Phase, Start Date, Sched Time, Duration, Assigned To, Material

#### 4. Forms (Data Collection)
- Job Ticket A/B - Area details (material, edge, sink)
- Install Checklist - Pre-install verification
- Template Check List - Measurement verification
- ST Production Checklist - Fabrication verification

#### 5. Phases
- Jobs can have multiple phases (ST1, ST2 FHBS, etc.)
- Each phase has its own forms and activities
- Phase sequence determines workflow order

#### 6. Quotes
- Associated estimates with revision history
- Links to Price Lists (e.g., "Sherri's - Partner Quote")

#### 7. Files
- PDFs, drawings, photos attached to job
- Visibility toggles: TempLink, InstaLink, Portal

#### 8. Orders & Purchase Orders
- Material orders linked to job
- Supplier/vendor tracking

---

## Workflow & Activity Types

### Complete Activity Sequence (60+ Activities)

The fabrication workflow is defined by Activity Types with dependencies:

#### Pre-Production (Sequences 1-9)
| Seq | Activity | Status | Duration | Assigned To | Dependencies |
|-----|----------|--------|----------|-------------|--------------|
| 1 | Submittal Drawings | Estimate | 1 hour | Kevin | - |
| 2 | Clean Sheet | Estimate | - | - | - |
| 3 | Material Ordering | Auto-Schedule | 5 min | Adam | After Clean Sheet |
| 4 | Contact Customer | Estimate/Pending | - | - | - |
| 5 | Material Available | Estimate | - | - | - |
| 6 | Template | Estimate | 1 hour | - | RED color |
| 7 | Material Viewing | Canceled | - | Jessica | Before Stone RTP -2 days |
| 8 | PM Release | Auto-Schedule | - | - | After Template +1 day |
| 9 | CAD Comm. | Auto-Schedule | 1 hour | - | Multiple dependencies |

#### Production - ST (Stone/Template) (Sequences 10-27)
| Seq | Activity | Status | Duration | Assigned To | Color |
|-----|----------|--------|----------|-------------|-------|
| 10 | CAD Res. | Auto-Schedule | 1 hour | CAD Residential | - |
| 11 | CKF PreFab | Auto-Schedule | 1 hour | - | #ffeeff |
| 14 | Programming | Auto-Schedule | 1 hour | Programming | GREEN |
| 16 | Mat'l Handling | Auto-Schedule | - | ST Production | #ffe0aa |
| 18 | Stone RTP | Auto-Schedule | 5 min | ST Production | #22ff22 |
| 24 | CNC | Auto-Schedule | 1 hour | - | #ff22ff |
| 26 | Polish | Auto-Schedule | 1 hour | ST Production | Aqua |

#### Quality Control (Sequences 36-40)
| Seq | Activity | Status | Duration | Assigned To | Color |
|-----|----------|--------|----------|-------------|-------|
| 36 | **Stone RZ/QC** | Estimate | 5 min | ST Shop Tech, ST Production | RED |
| 37 | SS Comm. RZ | Estimate | 1.5 hrs | SS Production | #ff6622 |
| 38 | SS Res. RZ | Estimate | 1.5 hrs | SS Production | Olive |
| 39 | SS Crating | Estimate | - | - | #ff88ff |
| 40 | ST Crating | Estimate | 1.5 hrs | - | #ff88ff |

**RZ = Review Zone = QC Checkpoint**

#### Delivery & Install (Sequences 41-56)
| Seq | Activity | Status | Duration | Assigned To |
|-----|----------|--------|----------|-------------|
| 41 | Sinks & Accessories | Auto-Schedule | 1 hour | Seth Ferreira |
| 42 | Transfer to Lee's Summit MO | Estimate | 1.5 hrs | Joel Delivery |
| 43 | Transfer to Jobsite | Estimate | 2.5 hrs | Joel Delivery |
| 44 | Transfer to Wichita | Estimate | 1.5 hrs | Joel Delivery |
| 47 | **Install** | Estimate | 3 hrs | - |
| 48 | HD Install | Estimate | 3 hrs | - |
| 51 | Delivery | Estimate | 1.5 hrs | Joel Delivery |
| 52 | Customer Pick-up | Auto-Schedule | 1.5 hrs | Cust. Pick up |

#### Closeout & Remake (Sequences 54-60)
| Seq | Activity | Status | Duration | Assigned To |
|-----|----------|--------|----------|-------------|
| 54 | Service Ticket | Estimate | 2 hrs | - |
| 55 | Callback | Estimate | 2 hrs | - |
| 56 | Job Visit | Estimate | 2 hrs | - |
| 57 | **Invoice** | Auto-Schedule | - | Cyle |
| 58 | ST Remake | Complete | 1 hour | - |
| 59 | SS Remake | Complete | 1 hour | - |
| 60 | Shop Time | Estimate | 2 hrs | ST Shop Tech |

### Activity Statuses
| Status | Color | ID | Usage |
|--------|-------|-----|-------|
| Estimate | - | - | Default starting status |
| Pending | Orange | 11 | Waiting on customer/info |
| Confirmed | Green | 2 | Customer confirmed |
| Auto-Schedule | Purple | 4 | System-scheduled |
| Complete | Blue | 3 | Finished |
| Canceled | Red | 5 | Not needed |

### Process Types
| Process ID | Name | Description |
|------------|------|-------------|
| 9 | LeadTracker | Pre-sales walk-in customers |
| Other | Job | Full fabrication projects |

---

## Job Forms

### Form Templates (43 Total)

| ID | Form Name | Show on Calendar | Process |
|----|-----------|------------------|---------|
| 1 | Job Ticket A | Yes | Job |
| 2 | Job Ticket | Yes | Job |
| 5 | Install Checklist | Yes | Job |
| 6 | Template Check List | Yes | Job |
| 7 | ST Production Checklist | Yes | Job |
| 8 | Callback Ticket | Yes | Job |
| 9 | Service Ticket | Yes | Job |
| 10 | Customer Pick Up | Yes | Job |
| 11 | Delivery Ticket | Yes | Job |
| 12 | Job Visit | Yes | Job |
| 13 | Warranty | Yes | Job |
| 15 | Prevailing Wage | Yes | Job |
| 47 | LeadTracker | Yes | LeadTracker |

### Job Ticket A - Kitchen (Example Form Fields)

```
┌─────────────────────────────────────────────────────────────────┐
│ Job Ticket A - Kitchen                        Phase: ST1        │
├─────────────────────────────────────────────────────────────────┤
│ Job Number: 20246                                               │
│ Job Name: Donahoo                                               │
│ Job Phase Name: ST1                                             │
│ Transfer to Lee's Summit MO: [Phase]                            │
├─────────────────────────────────────────────────────────────────┤
│ Onsite Primary Contact: Sherri 816-262-1044                     │
├─────────────────────────────────────────────────────────────────┤
│ Job Site: Remodel      Cabinets: New Cabinets                   │
│ TP Code: 5089          Phase Total Sq. Ft: 80                   │
│ Job Ticket A Sq. Ft: 89.5                                       │
├─────────────────────────────────────────────────────────────────┤
│                        Room: Kitchen                            │
├─────────────────────────────────────────────────────────────────┤
│ Material Thickness: 3cm                                         │
│ Material/Color: Cambria Warwick                                 │
│ Edge Profile: (ST) 1/8" Double Roundover                        │
├─────────────────────────────────────────────────────────────────┤
│ Backsplash: Loose                                               │
│ Backsplash Thickness: 3CM                                       │
│ Backsplash height: 4"                                           │
├─────────────────────────────────────────────────────────────────┤
│ Sink Mount: UM                                                  │
│ Faucet: Drill Onsite                                            │
│ Faucet by: Others Onsite                                        │
│ Cooking Unit/Misc. Cutouts: fs                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Inventory & Products

### Product Categories

#### Product Families
| Family | Description |
|--------|-------------|
| Adhesive | Glues, sealers (Integra, Join.It, Mastidek) |
| Brackets | Support brackets |
| Fabrication | Tile fabrication |
| Maintenance | Wear parts, consumables |
| Sheet | Solid surface, porcelain, engineered composite |
| Slab | Stone slabs (granite, quartz, marble) |

### Sheet Products (Solid Surface - 69 Total)

| Product | Line | Variants | Supplier |
|---------|------|----------|----------|
| Avonite 1/2" | Solid Surface | 52 colors | Jaeckle Distributors |
| Avonite 1/4" | Solid Surface | 6 colors | Jaeckle Distributors |
| Avonite Studio 1/2" | Solid Surface | 42 colors | Jaeckle Distributors |
| Bellavati | Solid Surface | 2 colors | Doyle Farris, LLC |
| Corian SS 1/2" | Solid Surface | 123 colors | Hallmark Building Supplies |
| Corian SS 1/4" | Solid Surface | 2 colors | Hallmark Building Supplies |
| Diamond Surfaces | Solid Surface | 47 colors | Diamond Surfaces USA |
| Formica 1/2" | Solid Surface | 38 colors | Compi Distributors |
| Hanex 1/2" | Solid Surface | 92 colors | Edgebanding Services |
| HiMacs 1/2" | Solid Surface | 162 colors | LX Hausys |
| HiMacs 1/4" | Solid Surface | 4 colors | LX Hausys |
| Livingstone 1/2" | Solid Surface | 78 colors | US Surfaces |
| Staron 1/2" | Solid Surface | 107 colors | ASMI/Doyle Farris |

### Adhesive Products

| Product | Unit | Variants | Supplier |
|---------|------|----------|----------|
| Integra | Each | 97 colors | BB Industries |
| Join.It | Each | 141 variants | Join.It Adhesives |
| Mastidek 215ml | Lin. Ft. | 27 colors | GMR Quality Stone Products |

### Inventory Settings Structure

```
Inventory Settings
├── Costs / Cost Lists
├── Inventory Locations
├── Labels
├── Products
│   ├── Product Attributes
│   └── Product Hierarchy
├── Purchase Order Fields/Forms/Settings/Status Colors
├── Serial Number Fields
├── Ship-To Locations
├── Suppliers / Supplier Fields
└── Units of Measure
```

---

## LeadTracker System

### Overview
LeadTracker (Process ID 9) manages **pre-sales walk-in customers** from the kiosk/showroom before they become full jobs.

### LeadTracker List View
| Column | Description |
|--------|-------------|
| Account | Partner/dealer account |
| LeadTracker Name | Customer name |
| Showroom Visit - Date | When they visited |
| LeadTracker Followup - Date | Next action date |

### LeadTracker Form (Template 47/1120) - Field Mappings

| Field ID | Field Name | Type | Purpose |
|----------|------------|------|---------|
| 3407 | Notes | MultilineText | Area notes |
| 3411 | Keystone Select | LOV | Material category |
| 3412 | Area Name | Text | "Kitchen", "Master Bath" |
| 3413 | Color Selection | Text | Material name |
| 3414 | Edge Profile | LOV | Stone/Solid Surface edges |
| 3415 | Material Thickness | LOV | 1cm, 2cm, 3cm |
| 3416 | Partial Slab ID | Text | Slab number |
| 3417 | Splash/Backsplash | LOV | 7 splash options |
| 3418 | Splash Height | LOV | Splash thickness |
| 3420 | Stock Sink | LOV | 66 stock sink models |
| 3421 | Sink by Customer | Checkbox | Customer provides sink |
| 3422 | Customer Sink Model | Text | Customer sink model |
| 3440 | Lead Source | LOV | 9 lead source options |
| 3441 | Referral | Text | Referral name |
| 3442 | Marketing Opt-In | Checkbox | Marketing consent |
| 3523 | Target Install Date | Date | Scheduled install |
| 3525 | Plumbing Needed | LOV | Yes/No |
| 3526 | Tearout Needed | LOV | Yes/No/Not Sure |

### Edge Profile LOV Values (Field 3414)

**Stone Edges (ST)**
| ID | Edge Name |
|----|-----------|
| 368132 | (ST) 1/8" Double Radius |
| 368133 | (ST) 1/8" Double Roundover |
| 368134 | (ST) Bullnose |
| 368135 | (ST) Chamfer |
| 368136 | (ST) Chisel |
| 368137 | (ST) Flat Polish |
| 368138 | (ST) Half Bullnose |
| 368139 | (ST) Half Moon |
| 368140 | (ST) Micro Bevel |
| 368141 | (ST) Miter |
| 368142 | (ST) Ogee |
| 368143 | (ST) Waterfall |

**Solid Surface Edges (SS)**
| ID | Edge Name |
|----|-----------|
| 368144 | (SS) Double Round |
| 368145 | (SS) Top Round/Bottom Flat |
| 368146 | (SS) Top Round |
| 368147 | (SS) Double Bevel |
| 368148 | (SS) Cove |
| 368149 | (SS) Full Bullnose |
| 368150 | (SS) Half Bullnose |
| 368151 | (SS) Chisel |
| 368152 | (SS) Eased |
| 368153 | (SS) Large Ogee |
| 368154 | (SS) Reverse Ogee |
| 368155 | (SS) Double Round w/ Cove Bottom |
| 368156 | (SS) No Drip |
| 368159 | (SS) Thin Edge |

### Lead Source LOV Values (Field 3440)
| ID | Source |
|----|--------|
| 368530 | Facebook |
| 368531 | Google |
| 368532 | Radio |
| 368533 | Campaign ID 12345 |
| 368534 | Friends/Family |
| 368535 | KC CarShow |
| 368536 | Referral/Other |
| 368734 | Drove By |
| 380282 | Trade Partner |
| 389276 | Via Assigned Account (Partner/dealer) |

---

## API Integration

### CLI Commands (MorawareCli.exe)

Located at: `tools/moraware-cli/bin/Release/net48/MorawareCli.exe`

#### LeadTracker Operations
```bash
# Create new lead
create-leadtracker --json '{"Name":"John Doe","Email":"john@email.com",...}'

# Search leads
search-leadtrackers --phone "316-555-1234"
search-leadtrackers --email "john@email.com"

# Find by LeadTracker ID
find-job-by-leadtracker-id --id "LT-00038"
find-job-by-number --number "LT-00065"
```

#### Job Operations
```bash
# Get job details
get-job --id 22317

# Get job forms
get-job-forms --job-id 22317

# Get job activities
get-job-activities --job-id 22317

# Update job
update-job --id 22317 --json '{"Name":"Updated Name"}'
```

#### Form Operations
```bash
# Create form on job
create-job-form --job-id 22317 --template-id 16 --phase-name "ST1" --json '{...}'

# Update form fields
update-job-form --form-id 12345 --json '{"3412":"Kitchen","3413":"Cambria Warwick"}'
```

#### Activity Operations
```bash
# Get remake activities (date range)
get-remake-activities --from-date 2025-11-01 --to-date 2025-12-09

# Add activity
add-job-update-activity --job-id 22317 --activity-type-id 29

# Update activity status
update-activity-status --activity-id 12345 --status-id 3
```

### Key Moraware API Calls (via morawareApiService.ts)

| Operation | Method | Purpose |
|-----------|--------|---------|
| create-leadtracker | POST | Create new lead from kiosk |
| search-leadtrackers | GET | Find existing customer |
| get-job | GET | Retrieve job details |
| get-job-forms | GET | List forms on job |
| create-job-form | POST | Add form to job |
| update-job-form | PUT | Update form fields |
| get-job-activities | GET | Get workflow activities |
| update-activity-status | PUT | Change activity status |
| get-field-activities | GET | Today's field activities |
| get-jobs-for-account | GET | Jobs for a dealer/partner |
| get-account-stats | GET | Material usage, job counts |

---

## Settings Architecture

### Settings Menu Structure

```
Settings
├── Account
├── Billing (external)
├── Calendar
│   └── Import Data
├── Inventory
│   ├── Costs
│   ├── Cost Lists
│   ├── Inventory Locations
│   ├── Labels
│   ├── Products
│   ├── Product Attributes
│   ├── Product Hierarchy
│   ├── Purchase Order Fields/Forms/Settings/Status Colors
│   ├── Serial Number Fields
│   ├── Ship-To Locations
│   ├── Suppliers
│   ├── Supplier Fields
│   └── Units of Measure
├── Job
│   ├── Activity Fields
│   ├── Activity Forms
│   ├── Activity Packets
│   ├── Activity Sets
│   ├── Activity Statuses
│   ├── Activity Types ← Full workflow definition
│   ├── Assignees ← Crews/staff
│   ├── File Fields
│   ├── Job Detail
│   ├── Job Fields
│   ├── Job Forms ← 43 form templates
│   ├── Job Form Sets
│   ├── Issue Categories
│   ├── Issue Forms
│   ├── Order Area Forms
│   ├── Processes
│   ├── Salespeople
│   └── Templates
├── Shop
├── System
└── Users & Roles
```

---

## Field Mappings & IDs

### Process IDs
| ID | Name |
|----|------|
| 9 | LeadTracker (pre-sales) |

### Form Template IDs
| ID | Form Name |
|----|-----------|
| 47 | LeadTracker Template (auto-attached) |
| 1041 | Job Ticket A |
| 1077 | Install Checklist |
| 1115 | Remake Tracking |
| 1120 | LeadTracker Form |

### Activity Type IDs
| ID | Type Name |
|----|-----------|
| 2 | Template |
| 4 | Install |
| 16 | Invoice |
| 29 | Contact Customer |
| 47 | Job Visit |
| 48 | Service Ticket |
| 93 | Showroom Visit |

### Activity Status IDs
| ID | Status | Color |
|----|--------|-------|
| 2 | Confirmed | Green |
| 3 | Complete | Blue |
| 4 | Auto-Schedule | Purple |
| 5 | Canceled | Red |
| 11 | Pending | Orange |
| 12 | Not Ready | Dark Red |
| 18 | Ready to Schedule | Pink |

### Custom Field IDs
| ID | Field Name | Type |
|----|------------|------|
| 13 | Job Number | Text |
| 77 | Keystone PM | LOV |
| 314 | Appointment With | LOV |
| 315 | LeadTracker ID | Text (LT-00038) |
| 321 | Portal Code | Text |
| 327 | Portal Contact | Text |

---

## Common Operations

### Kiosk Lead Creation Flow

```
1. Customer enters info in Kiosk
2. Portal backend calls create-leadtracker
3. Moraware creates LeadTracker (Process ID 9)
4. Form 1120 auto-attached with area data
5. Showroom Visit activity created (Type 93)
6. SMS/Email notifications sent
```

### Job Conversion (LeadTracker → Job)

```
1. PM reviews LeadTracker in Moraware
2. PM changes Process to Job type
3. Phase(s) added (ST1, etc.)
4. Job forms created (Job Ticket A, etc.)
5. Activities scheduled
6. Portal can only READ after conversion
```

### Multi-Area Form Support

When customer selects multiple areas (Kitchen + Master Bath):

```
1. First area → Uses existing form from LeadTracker
2. Additional areas → Creates dated forms:
   - "Kitchen - 12/12/2025"
   - "Master Bath - 12/12/2025"
3. Each form populated with area-specific data
```

---

## Safety Rules & Gotchas

### Critical Safety Rules

#### NEVER modify Jobs after conversion
```
LeadTracker (Process ID 9) = Portal CAN update
Job (any other Process ID) = Portal CANNOT update
```

Why: Once converted, the Project Manager owns the data. Portal must never overwrite PM's work.

#### Phase Association Timing
```
WRONG: CreateJobForm() → AddPhase()   // Form shows "(None)" for phase
RIGHT: AddPhase() → CreateJobForm()   // Form correctly associated
```

Always add phase BEFORE creating forms.

#### Use --phase-name Instead of --phase-id
```
WRONG: --phase-id 12345   // May be stale
RIGHT: --phase-name "ST1" // CLI looks up current ID
```

Phase IDs change; names are stable.

### Common Bugs & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Triple lead creation | Azure cold starts, no idempotency | useRef guard in submitLead() |
| SMS/Email not sending | Env vars wrong on Render | Check TWILIO_ACCOUNT_SID starts with "AC" |
| Form shows "Phase: (None)" | Phase added after CreateJobForm | Use --phase-name flag |
| Address missing in Moraware | Field not extracted | Destructure address fields in kiosk.ts |
| Session timeout | Long operations | Re-auth and retry |

### Forbidden Operations

The following operations are **NEVER** allowed from the portal:
- DeleteJob
- DeleteAccount
- DeleteJobActivity
- UpdateAccount
- UpdateJob on converted Jobs (non-LeadTracker)

---

## Appendix: Showroom IDs

| Location | ID |
|----------|----|
| Wichita | 21 |
| Kansas City | 2109 |

---

## Appendix: Account Types

| Account Type | Description | Example |
|--------------|-------------|---------|
| Retail | Direct customer | Individual homeowner |
| Dealer | Kitchen/bath dealers | Sherri's Kitchen & Bath |
| Partner | Trade partners | KC Branch Projects |
| Home Depot | Big box retail | Home Depot Store 2204 |

---

*Generated by Claude Code - December 2025*
*Based on live Moraware system exploration and portal codebase analysis*
