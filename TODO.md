# TODO: Fix POST /api/workweek to Create New Row Instead of Upsert

## Steps to Complete

1. **Create Alembic Migration**: Generate a new migration to drop the unique index on `region` in `workweek_policies` table.
2. **Update Model**: Remove `unique=True` from the `region` column in `WorkweekPolicy` model.
3. **Modify Repository**: Change `upsert_workweek` method to always create a new row, remove the existence check.
4. **Test the API**: Verify that POST /api/workweek now creates a new row each time, allowing multiple policies per region.
5. **Update Documentation**: Optionally update the endpoint summary if needed.

## Current Status
- [x] Step 1: Create migration
- [ ] Step 2: Update model
- [ ] Step 3: Modify repository
- [ ] Step 4: Test API
- [ ] Step 5: Update docs if necessary
