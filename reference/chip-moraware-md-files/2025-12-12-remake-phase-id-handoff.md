# Remake Tracking Form - Phase ID Implementation Handoff

## Date: December 12, 2025

## Goal
When a remake activity (e.g., "ST1 - Remake") is missing its Remake Tracking form, clicking "Send Issue" in the Remakes Manager should:
1. Create an Issue in Moraware (already working)
2. Create a Remake Tracking form **associated with the same phase as the remake activity** (e.g., ST1, st2) - NOT "Phase: (None)"

## What Works
- **CLI `create-job-form --phase-id` command**: Tested and confirmed - creates forms with correct phase association
- **CLI `get-remake-activities` now outputs `phaseId`**: Each activity includes the Moraware phase ID (e.g., 23720, 23618)
- **Database**: `job_phase_id` column added to `remake_tracking` table
- **Backend**: `remakeService.ts` stores phaseId during sync, `admin.ts` passes it to CLI
- **Frontend**: `RemakesManager.tsx` and `api.ts` pass `jobPhaseId` when calling send-issue endpoint
- **UI**: Remakes Manager loads correctly at `https://keystone-pricing-portal-frontend.onrender.com/admin/remakes`

## What Needs Verification
- **Azure CLI deployment**: The CLI with phaseId output may not be deployed to Azure yet
  - GitHub Actions often fails with 500 errors on zipdeploy
  - Manual Kudu upload may be needed
  - Zip file ready at: `C:\Dev\keystone-pricing-portal\azure-function-upload.zip`
  - Upload to: Azure Portal -> Function Apps -> `keystoneportal-e8c6efhyhmfbb7a7` -> Advanced Tools (Kudu) -> Debug console -> site/wwwroot/

## After Azure CLI is deployed
1. Go to Remakes Manager and click "Refresh Data" to sync with new CLI
2. This will populate `job_phase_id` for all remake records
3. Test "Send Issue" on a missing form item - it should create the form with correct phase

## Key Files Modified
- `tools/moraware-cli/Program.cs` - Added phaseId extraction (~lines 3468-3500, 3714-3750)
- `azure-moraware-function/moraware-cli/` - Built CLI binaries for Azure
- `database/migrations/add_job_phase_id.sql` - New column
- `backend/src/services/remakeService.ts` - Store phaseId during sync
- `backend/src/routes/admin.ts` - Pass jobPhaseId to CLI instead of morawareActivityId
- `frontend/src/components/admin/RemakesManager.tsx` - Pass jobPhaseId to API
- `frontend/src/services/api.ts` - Added jobPhaseId to types and functions

## Potential Cleanup Needed
The `backend/src/services/morawareWebService.ts` file contains web-based RPC code (`createIssue`, `createJobFormWithPhase`) that was developed during troubleshooting. This may be dead code if we're using the CLI approach exclusively. Review and potentially remove if unused.

## Important Context
- The CLI's `--phase-id` parameter already existed and works - we just needed to pass the correct phase ID
- Phase ID comes from `activity.JobPhases.First().JobPhaseId` in the Moraware data
- Don't confuse `morawareActivityId` (the activity record ID) with `jobPhaseId` (the phase the activity belongs to)

## Commands to Test Locally
```bash
# Test CLI outputs phaseId
"C:/Dev/keystone-pricing-portal/tools/moraware-cli/bin/Release/net48/MorawareCli.exe" get-remake-activities --from-date 2025-12-01 --to-date 2025-12-12

# Test form creation with phase
"C:/Dev/keystone-pricing-portal/tools/moraware-cli/bin/Release/net48/MorawareCli.exe" create-job-form --job-id 22434 --template-id 1115 --phase-id 23774 --form-name "Test Form"
```

## Recent Commits (for reference)
- `791be4a` - feat: Add phase ID support for Remake Tracking form creation
- `94f370e` - fix: Use job number in CSV export instead of database ID
- `b164358` - feat: Add Remake Tracking form creation + job number display
