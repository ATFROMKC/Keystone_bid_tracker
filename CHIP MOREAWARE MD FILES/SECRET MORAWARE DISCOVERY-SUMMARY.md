# Moraware Secret API Discovery Summary

**Date**: 2026-01-16
**Status**: SUCCESS - Major data extracted!

---

## KEY BREAKTHROUGH: CounterGo Drawing Data Extracted!

We successfully extracted `g_quoteInfo` which contains **full CounterGo drawing data**:
- Shape geometry with exact coordinates
- Counter dimensions (depth, width, angles)
- Sink cutouts with position, size, and model info
- Edge profiles (finished/unfinished, splash heights)
- Material/price list references
- Revision history

This is the data needed to recreate drawings programmatically!

---

## Successfully Extracted Data (Programmatic)

### 1. Global Variables (via `page.evaluate`)

These are available on every Moraware page and contain valuable configuration data:

| Variable | Data Type | Description |
|----------|-----------|-------------|
| `g_jobProcesses` | Array | All job processes (Job, LeadTracker, Quote) |
| `g_arrStatuses` | Array | All status definitions with colors (11 statuses) |
| `g_permissionNames` | Object | Full permission system (335 permissions!) |
| `g_featureFlags` | String | Comma-separated active feature flag IDs |
| `g_userId` | Number | Current logged-in user ID |
| `g_userName` | String | Current logged-in username |
| `g_isCounterGoLicensed` | Number | CounterGo license status (1 = licensed) |
| `g_isNVInventoryLicensed` | Number | NV Inventory license status |
| `g_JTAccessRights` | String | Encoded access rights for JobTracker |
| `g_CGAccessRights` | String | Encoded access rights for CounterGo |
| `g_strVer` | String | Moraware version (5_0_1099) |
| `g_currencySymbol` | String | Currency symbol ($) |
| `g_calMinSchedHour` | Number | Calendar min hour (5) |
| `g_calMaxSchedHour` | Number | Calendar max hour (23) |
| `g_workDaysOfTheWeekBitmask` | Number | Work days bitmask (31 = Mon-Fri) |

### 2. Page-Specific Globals

| Page | Globals Found | Key Data |
|------|---------------|----------|
| `/sys/admin` | 537 | Core system settings |
| `/sys/inventory` | 315 | Inventory configuration |
| `/go/pricelists` | 328 | CounterGo price list config |
| `/sys/accounts` | 557 | Account page configuration |

### 3. Working RPC Commands

| Command | Parameters | Returns |
|---------|------------|---------|
| `Customer_GetTopAccountInfosGivenPrefix` | `(prefix, maxResults)` | URL-encoded account list |
| `Admin_GetAttributeValueTable` | `()` | (empty - needs context) |

### 4. RPC Commands That Need Parameters

| Command | Required Parameter | From Error Message |
|---------|-------------------|-------------------|
| `Admin_GetViewByName` | `PageId` | "Required parameter #0, 'PageId'" |
| `Admin_GetProductOptionElementsForPriceList` | `PriceTypeId` | "Required parameter #0, 'PriceTypeId'" |
| `CG_GetSelectCGPriceListsTable` | `FormId` | "Required parameter #0, 'FormId'" |
| `Customer_GetTopAccountInfosGivenPrefix` | `IncludeInactive` | (optional, defaults to false) |

### 5. RPC Command Class Structure

From error messages, we discovered the RPC command class naming:

| Prefix | Class Name | Purpose |
|--------|------------|---------|
| `Customer_` | `cRsAccountFunctions` | Account/customer operations |
| `Admin_` | `cRsAdminFunctions` | Admin/settings operations |
| `CG_` | `CounterGoHandler` | CounterGo operations |
| `Job_` | `cRsJobFunctions` | Job operations |
| `Quote_` | `cRsQuoteFunctions` | Quote operations |

---

## Data Extracted

### Files Created

| File | Contents |
|------|----------|
| `extracted-globals.json` | Core globals from admin page |
| `inventory-page-globals.json` | All 315 inventory globals |
| `countergo-page-globals.json` | All 328 CounterGo globals |
| `all-accounts-rpc.json` | Account list from RPC |
| `attribute-value-table.json` | (empty) |

### Key Data Points

1. **Job Processes**: 3 processes (Job, LeadTracker, Quote)
2. **Statuses**: 11 statuses with IDs, names, colors
3. **Permissions**: 335 permission definitions (CRUD for all entities)
4. **Feature Flags**: 33 active feature flags
5. **Version**: Moraware 5.0.1099

---

## Next Steps

### High Priority

1. **CounterGo Quote Data** - Navigate to `/go/viewquote/{id}` to get `g_quoteInfo`
2. **Price List Details** - Find correct FormId for `CG_GetSelectCGPriceListsTable`
3. **Complete Account Data** - Use SDK `GetAccounts` for full details

### Medium Priority

1. **Issue Data** - Find correct RPC commands for issues
2. **Activity Data** - Extract from job pages
3. **Form Data** - Extract form templates and definitions

### Low Priority

1. **Report Templates** - Extract report definitions
2. **Email Templates** - Extract email configuration
3. **Calendar Settings** - Extract calendar config

---

## Technical Notes

### RPC Execution Pattern

```javascript
// jsrsExecute wraps ServerCall.LegacyRemoteScripting.jsrsExecute
jsrsExecute(callback, commandName, params, errorCallback)
```

### Response Parsing

Account search returns URL-encoded format:
```
1;id1:name1:flag1,id2:name2:flag2,...
```

### Browser Requirements

- Puppeteer with headless mode
- 30 second timeout for navigation
- 2 second wait after navigation for JS init

---

## Files Structure

```
tools/moraware-extractor/
├── src/
│   ├── browser.ts          # Puppeteer session management
│   └── rpc.ts              # jsrsExecute wrapper
├── output/
│   ├── extracted-globals.json
│   ├── inventory-page-globals.json
│   ├── countergo-page-globals.json
│   ├── all-accounts-rpc.json
│   └── DISCOVERY-SUMMARY.md
├── test-simple.ts          # Working extraction script
├── discover-commands.ts    # Command discovery
└── discover-commands-v2.ts # Improved discovery
```
