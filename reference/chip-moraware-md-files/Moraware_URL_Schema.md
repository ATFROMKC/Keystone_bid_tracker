# Moraware URL Schema - Complete Reference

## Base URL Structure

```
https://{subdomain}.moraware.net/sys/jobs?
  &view={viewId}
  &status={statusFilter}
  &sort={sortOrder}
  &cols={columns}
  &pageSize={pageSize}
  &filters={filterString}
  &mrv={mostRecentViewId}
```

---

## URL Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `view` | View ID (`0` = unsaved/custom view) | `view=0` or `view=507` |
| `status` | Global job status filter | `status=0` (all) |
| `sort` | Sort order: `a`=ascending, `d`=descending + column index | `sort=a0` |
| `cols` | Comma-separated column codes | `cols=JN1,JA13` |
| `pageSize` | Results per page | `pageSize=30` |
| `filters` | Filter string (multiple filters separated by `!`) | See below |
| `mrv` | Most recent saved view ID | `mrv=507` |

---

## Filter Types (cboMajorFilterType)

| Value | Filter Type |
|-------|-------------|
| `1` | Job Activity Info |
| `2` | Job Field |
| `3` | Account Field |
| `4` | Job Issue |
| `13` | Form |
| `14` | Job Search |

---

## Column Codes

### Basic Job/Account Fields

| Code | Field Name | Category |
|------|-----------|----------|
| `CN1` | Account Name | Contact Name |
| `CA{n}` | Account custom field (n = field ID) | Contact Attribute |
| `JN1` | Job Name | Job Name |
| `JN4` | Job Material | Job Name |
| `JN5` | Salesperson | Job Name |
| `JN15` | Job Issues | Job Name |
| `JN22` | Job Notes | Job Name |
| `JA13` | Job Number | Job Attribute |
| `JA60` | Onsite Primary Contact | Job Attribute |
| `JA77` | Keystone PM | Job Attribute |
| `JA78` | Job Site | Job Attribute |
| `JA79` | Cabinets | Job Attribute |
| `JA80` | Tear out | Job Attribute |

### Activity Type Columns (grouped with `;`)

Format: `AT{activityTypeId}_{subfield}` or `CT{activityTypeId}.{customFieldId}`

| Code Pattern | Meaning |
|--------------|---------|
| `AT{n}` | Activity Date |
| `AT{n}_3` | Activity Status |
| `AT{n}_13` | Activity Notes |
| `AT{n}_14` | Activity Duration |
| `AT{n}_15` | Scheduled Time |
| `AT{n}_16` | Assigned To |
| `AT{n}_18` | Phase |
| `CT{n}.75` | Arrival Window |
| `CT{n}.71` | TP Code |
| `CT{n}.72` | Activity SqFt |
| `CT{n}.96` | Lineal Ft |
| `CT{n}.265` | HOS |
| `CT{n}.311` | Geofence HOS |

### Form Fields

| Code Pattern | Meaning |
|--------------|---------|
| `FR{formId}_{fieldId}` | Form row field |
| `FF{fieldId}` | Form field |

---

## Activity Type IDs

| ID | Activity Type |
|----|---------------|
| `2` | Template |
| `4` | Install |
| `7` | Programming |
| `16` | Invoice |
| `24` | CNC |
| `25` | Polish |
| `29` | Contact Customer |
| `30` | Clean Sheet |
| `31` | Material Ordering |
| `32` | CAD Comm. |
| `33` | PM Release |
| `36` | Stone RTP |
| `37` | Stone RZ/QC |
| `38` | Sinks & Accessories |
| `39` | SS RTP |
| `40` | SS Comm. RZ |
| `43` | Delivery |
| `44` | Customer Pick-up |
| `45` | Shop Time |
| `46` | Help Carry |
| `47` | Job Visit |
| `48` | Service Ticket |
| `49` | Callback |
| `50` | Tear Out |
| `51` | Material Viewing |
| `52` | Miter |
| `53` | ST Remake |
| `54` | SS Remake |
| `55` | Chisel Edge |
| `56` | SS Shop Rework |
| `57` | ST Shop Rework |
| `59` | Substrate |
| `60` | Transfer to Lee's Summit MO |
| `61` | Transfer to Wichita |
| `62` | Stacked Lam |
| `63` | Pre-Programming |
| `64` | Leather Edge |
| `65` | Submittal Drawings |
| `66` | Ship To Customer |
| `67` | SS Crating |
| `68` | CAD Res. |
| `69` | CKF PreFab |
| `70` | ST Crating |
| `72` | Honing |
| `73` | Install Supports |
| `74` | HD Install |
| `77` | Milling |
| `78` | V-Groove |
| `79` | Slabsmith |
| `80` | SS Comm. Fab |
| `81` | Mat'l Handling |
| `82` | Leveling |
| `83` | SS Res. Fab |
| `84` | SS Res. RZ |
| `85` | SS Programming |
| `86` | SS Custom Fab |
| `87` | FTR Tracking |
| `89` | Job Creation Date |
| `90` | Material Available |
| `91` | Transfer to Jobsite |
| `92` | Tower Tracking |
| `93` | Showroom Visit |
| `94` | LeadTracker Followup |

---

## Activity Status Codes

| Code | Status | Color |
|------|--------|-------|
| `1` | Estimate | Black |
| `2` | Confirmed/In Process | Green |
| `3` | Complete | Blue |
| `4` | Auto-Schedule | #990099 (Purple) |
| `5` | Canceled | #ee0000 (Red) |
| `11` | Pending | Orange |
| `12` | Not Ready | #aa0000 (Dark Red) |
| `13` | Ready to Schedule KC | Teal |
| `16` | MULTIPLIER | #bbbbbb (Gray) |
| `17` | Review | #dd4411 (Orange-Red) |
| `18` | Ready to Schedule | #ff44ff (Pink) |

---

## Job Status Codes (for Job Field filter)

| Code | Status |
|------|--------|
| `1` | Active |
| `2` | Complete |
| `3` | Unscheduled |
| `4` | 30+ Days Old |

---

## Job Issue Status Codes

| Code | Status |
|------|--------|
| `1` | Urgent |
| `2` | Open |
| `3` | Closed |

---

## Filter String Encoding

### Multiple Filters
Multiple filters are separated by `!`:
```
filter1!filter2!filter3
```

### Activity Filter (Type `1`)

Format:
```
1|{activityTypeId}:{statusCode}:{quantifier}:{dateMode}:{dateMode}:3:1:{fromDate}:{toDate}:
```

| Position | Meaning | Values |
|----------|---------|--------|
| 1 | Filter type | `1` = Activity filter |
| 2 | Activity Type ID | See Activity Type IDs table |
| 3 | Status Code | See Activity Status Codes table |
| 4 | Quantifier | `1`=At least one, `5`=??? |
| 5 | Date Mode | `1`=Any, `2`=Specific range |
| 6 | Date Mode (duplicate) | `1`=Any, `2`=Specific range |
| 7 | Constant | `3` |
| 8 | Constant | `1` |
| 9 | From Date | `YYYY-M-D` format or empty |
| 10 | To Date | `YYYY-M-D` format or empty |

**Examples:**
```
# Install activity, Status = Complete, Any date
1|4:3:1:1:1:3:1:::

# Template activity, Status = Estimate, Date range 12/1-12/15/2025
1|2:1:5:2:2:3:1:2025-12-1:2025-12-15:

# HD Install activity, Status = Canceled, Any date
1|74:5:1:1:1:3:1:::
```

### Job Field Filter (Type `2`)

Format:
```
2|{subtype}:{operator}:{fieldId}:{fieldType}:{fieldId};{selectedValues};{flag}
```

| Position | Meaning | Values |
|----------|---------|--------|
| 1 | Filter type | `2` = Job Field |
| 2 | Subtype | `3` for built-in fields |
| 3 | Operator | `0`=is, `1`=is not |
| 4 | Field ID | e.g., `j19` for Job Status |
| 5 | Field Type | `10` for list fields |
| 6 | Field ID + values | `{fieldId};{value1},{value2};{flag}` |

**Examples:**
```
# Job Status is Active
2|3:0:j19:10:j19;1;0

# Job Status is Active or Complete
2|3:0:j19:10:j19;1,2;0
```

### Account Field Filter (Type `3`)

Format similar to Job Field Filter:
```
3|{subtype}:{operator}:{fieldId}:{fieldType}:{fieldId};{selectedValues};{flag}
```

### Job Issue Filter (Type `4`)

Format:
```
4|{issueStatusCodes}
```

Where `issueStatusCodes` is comma-separated list of: `1`=Urgent, `2`=Open, `3`=Closed

### Form Filter (Type `13`)

Format:
```
13|0:0:{fieldId}:{dataType}:{fieldId};{operator},{subOp},{valueType},{value1},{value2}
```

| Position | Meaning | Values |
|----------|---------|--------|
| 1 | Filter type | `13` = Form filter |
| 2-3 | Constants | `0:0` |
| 4 | Field ID | `ft_{formId}_{fieldId}` format |
| 5 | Data type | `13` = numeric, `19` = text, `10` = list |
| 6 | Field + values | See below |

**Number operators:**
- `2` = Between
- (other operators TBD)

**Example:**
```
# Job Ticket A - TP Code is between 100 and 500
13|0:0:ft_1041_1834:13:ft_1041_1834;2,2,3,100,500
```

---

## Field ID Formats: Columns vs Filters

**Important:** Column codes and filter field IDs use different formats for the same fields!

| Field | Column Code | Filter Field ID |
|-------|-------------|-----------------|
| Form field (e.g., TP Code) | `FF1834` | `ft_1041_1834:13` |
| Form row field | `FR1041_4` | `ft_1041_4:??` |

The relationship:
- **Column**: `FF{fieldId}` or `FR{formId}_{fieldId}`
- **Filter**: `ft_{formId}_{fieldId}:{dataType}`

The `fieldId` is the same (e.g., `1834`), but the prefix and format differ.

---

## Job Field IDs

### Built-in Job Fields

| Field ID | Field Name |
|----------|------------|
| `j17` | Job Name |
| `j19` | Job Status |
| `j3` | Job Creation |
| `j4` | Job Salesperson |
| `j5` | Job Notes |

### Custom Job Fields

| Field ID | Field Name |
|----------|------------|
| `13:17:3` | Job Number |
| `60:15:3` | Onsite Primary Contact |
| `61:15:3` | Onsite Secondary Contact |
| `77:1:3` | Keystone PM |
| `78:1:3` | Job Site |
| `79:1:3` | Cabinets |
| `80:1:3` | Tear out |

---

## Account Field IDs

| Field ID | Field Name |
|----------|------------|
| `a1:11` | Account Name |
| `a2:10` | Account Salesperson |
| `a5:10` | Account Status |
| `58:1:2` | PM |
| `65:1:2` | Account Manager |
| `66:1:2` | Customer Type |
| `231:1:2` | Lead Source |
| `262:1:2` | KC Acct |

---

## Form IDs

| Form ID | Form Name |
|---------|-----------|
| `1041` | Job Ticket A |
| `1086` | Job Ticket |
| `1059` | Job Ticket B |
| `1060` | Job Ticket C |
| `1077` | Install Checklist |
| `1085` | Template Check List |
| `1089` | ST Production Checklist |
| `1039` | Callback Ticket |
| `1069` | Service Ticket |
| `1075` | Delivery Ticket |
| `1071` | Warranty |
| `1115` | Remake Tracking |
| `1120` | LeadTracker |

---

## Form Field IDs

### Job Ticket A (Form ID: 1041)

| Field ID | Field Name | Column Code |
|----------|------------|-------------|
| `1792` | Onsite Primary Contact | `FF1792` |
| `1793` | Phase Total Sq. Ft | `FF1793` |
| `1796` | Sink (Brand, Model, & Color) | `FF1796` |
| `1804` | Special Edge Info | `FF1804` |
| `1810` | Special Material Info | `FF1810` |
| `1813` | Special Backsplash Info | `FF1813` |
| `1817` | Material/Color | `FF1817` |
| `1819` | Material Thickness | `FF1819` |
| `1821` | Faucet | `FF1821` |
| `1822` | Backsplash | `FF1822` |
| `1823` | Backsplash height | `FF1823` |
| `1825` | Sink Mount | `FF1825` |
| `1826` | Sink Location | `FF1826` |
| `1828` | Edge (old) - Inactive | `FF1828` |
| `1830` | Backsplash Thickness | `FF1830` |
| `1833` | Onsite Secondary Contact | `FF1833` |
| `1834` | TP Code | `FF1834` |
| `1791` | Cooking Unit/Misc. Cutouts | `FF1791` |
| `2041` | Job Site | `FF2041` |
| `2042` | Cabinets | `FF2042` |
| `2044` | Faucet by | `FF2044` |
| `2045` | Room | `FF2045` |
| `2046` | Support | `FF2046` |
| `2094` | Support By | `FF2094` |
| `2096` | Special Sink/Faucet Info | `FF2096` |
| `2097` | Trash/Grommet Hole Size | `FF2097` |
| `2098` | Special Cooking Unit/Mis. Cutout Info | `FF2098` |
| `2099` | Keystone PM | `FF2099` |
| `2100` | Trash/Grommet Hole Finish | `FF2100` |
| `2146` | Job Ticket A Sq. Ft | `FF2146` |
| `2492` | Remnant Location and Size | `FF2492` |
| `2493` | What CNC | `FF2493` |
| `2514` | Seam Adhesive | `FF2514` |
| `2623` | Job/Production Notes | `FF2623` |
| `2724` | Tear out | `FF2724` |
| `2750` | Edge Profile | `FF2750` |
| `2752` | Year House Built (Docs required Pre 78) | `FF2752` |
| `3305` | Order Name | `FF3305` |
| `3306` | Payment Status | `FF3306` |
| `3307` | Price | `FF3307` |
| `3308` | Total Order Sq. Ft. | `FF3308` |
| `3309` | Sale Date | `FF3309` |

### Remake Tracking (Form ID: 1115)

| Field ID | Field Name | Column Code |
|----------|------------|-------------|
| `3363` | Department Assignment | `FF3363` |
| `3364` | Assignee | `FF3364` |
| `3365` | Additional Notes | `FF3365` |
| `3366` | Reason Code | `FF3366` |

### LeadTracker (Form ID: 1120)

| Field ID | Field Name | Column Code |
|----------|------------|-------------|
| `3407` | Notes | `FF3407` |
| `3411` | Keystone Select | `FF3411` |
| `3412` | Area Name | `FF3412` |
| `3413` | Color Selection | `FF3413` |
| `3414` | Edge | `FF3414` |
| `3415` | Material Thickness | `FF3415` |
| `3416` | Partial Slab ID | `FF3416` |
| `3417` | Splash | `FF3417` |
| `3418` | Splash Thickness | `FF3418` |
| `3420` | Stock Sink | `FF3420` |
| `3421` | Sink By Customer | `FF3421` |
| `3422` | Customer Sink Model | `FF3422` |
| `3423` | Options/Extras | `FF3423` |
| `3424` | Faucet | `FF3424` |
| `3425` | Cooking Unit | `FF3425` |
| `3426` | Cooking Unit Model# | `FF3426` |
| `3427` | Faucet Model | `FF3427` |
| `3440` | Source | `FF3440` |
| `3441` | Referral | `FF3441` |
| `3442` | Marketing Opt In | `FF3442` |
| `3443` | LeadTracker ID | `FF3443` |
| `3518` | Future Use - Multi Line | `FF3518` |
| `3519` | Future Use - Checkbox | `FF3519` |
| `3520` | Future Use - link | `FF3520` |
| `3521` | Future Use - List Of Values | `FF3521` |
| `3522` | Future Use - Text | `FF3522` |
| `3523` | Target Install Date | `FF3523` |
| `3524` | Cabinet Status | `FF3524` |
| `3525` | Plumbing Needed | `FF3525` |
| `3526` | Tearout Needed? | `FF3526` |

---

## Activity Custom Field IDs

These fields can be used with `CT{activityTypeId}.{fieldId}` format.

| Field ID | Field Name | Data Type |
|----------|------------|-----------|
| `75` | Arrival Window | Text |
| `71` | TP Code | Number |
| `72` | Activity SqFt | Number |
| `96` | Lineal Ft | Number |
| `265` | HOS (Hours On Site) | Text |
| `311` | Geofence HOS (test) | Number |

---

## Assignee IDs (for Activity Assigned To filter)

| ID | Assignee |
|----|----------|
| `37` | Template 1 (WIC) - Eric Crowell |
| `29` | Template 2 (WIC) - Gabriel Guevara |
| `61` | Template 3 (WIC) - Victor R |
| `65` | Template 4 (KC) - Bryan Giroux |
| `31` | Install Crew 1 (WIC)(HD/Res) - Juan Diaz / Ruben Diaz |
| `32` | Install Crew 2 (WIC)(HD/Res) - Leo Trejo / Lupe Idanez |
| `56` | Install Crew 3 (WIC) - Omar Nunez / Jose |
| `70` | Install Crew 4 (WIC) - Alonso |
| `36` | Install Crew 5 (WIC)(Commercial) - Troy Knutson |
| `64` | Install Crew 6 (WIC)(HD/Res/Comm) - Rosendo Cardosa |
| `67` | Install Crew 7 (KC) - Carl Chizek |
| `87` | Install Crew 8 (KC) - Ronald Guzman |
| `72` | Field Ops 1 (WIC) - Grant |
| `89` | Service 1 (WIC) - Arnoldo Carrera |

---

## Complete URL Examples

### Example 1: Active jobs with Install activity Complete
```
https://keystonesolidsurfaces.moraware.net/sys/jobs?&view=0&status=0&sort=a0&cols=JN1,JA13&pageSize=30&filters=2|3:0:j19:10:j19;1;0!1|4:3:1:1:1:3:1:::
```

### Example 2: Jobs with Template activity on specific date
```
https://keystonesolidsurfaces.moraware.net/sys/jobs?&view=0&status=0&cols=JN1,JA13&pageSize=30&filters=1|2:3:5:2:2:3:1:2025-12-9:2025-12-9:
```

### Example 3: All columns for a comprehensive view
```
https://keystonesolidsurfaces.moraware.net/sys/jobs?&view=0&status=0&sort=a0&cols=CN1,CA58,JN1,JN4,JN15,JN5,JA13,JA60,JA77,JA78,JA79,JA80,JN22,AT2_3;AT2;AT2_15;AT2_14;AT2_16;CT2.75;CT2.71;CT2.72;CT2.96;CT2.265;CT2.311;AT2_13;AT2_18,AT4_3;AT4;AT4_15;AT4_14;AT4_16;CT4.75;CT4.71;CT4.72;CT4.96;CT4.265;CT4.311;AT4_13;AT4_18&pageSize=30
```

---

## Job Fields (Custom)

These are the active custom job fields. Use with `JA{fieldId}` column code format.

| Field ID | Field Name | Data Type |
|----------|------------|-----------|
| `13` | Job Number | Auto-number |
| `60` | Onsite Primary Contact | Text |
| `61` | Onsite Secondary Contact | Text |
| `62` | Account PO/Contract # | Text |
| `77` | Keystone PM | List of values |
| `78` | Job Site | List of values |
| `79` | Cabinets | List of values |
| `80` | Tear out | List of values |
| `81` | Stone Warranty | List of values |
| `82` | Lead Source | Text |
| `205` | Year House Built (Docs required Pre 78) | Number |
| `297` | Millwork, GC Office Contact | Text |

---

## Serial Number Fields

| Field ID | Field Name | Data Type |
|----------|------------|-----------|
| `144` | On Hold? | List of values |
| `145` | Hold for: Job #/ Job Name / Quote Name | Text |
| `148` | Hold Exp. Date | Date |
| `239` | Hold By (PM) | List of values |
| `317` | Hold Start Date | Date |

---

## File Fields

| Field ID | Field Name | Data Type |
|----------|------------|-----------|
| `92` | Show in TempLink | List of values |
| `93` | Show in InstaLink | List of values |
| `325` | Show in Portal (TESTING) | List of values |

---

## Notes

1. **Date Format**: Dates use `YYYY-M-D` format (no leading zeros on month/day)
2. **Multiple Values**: Multiple selected values in list filters are comma-separated
3. **Activity Columns**: Activity columns are grouped with `;` separator
4. **Filter Separator**: Multiple filters are separated by `!`
5. **URL Encoding**: Special characters should be URL-encoded when building URLs programmatically
