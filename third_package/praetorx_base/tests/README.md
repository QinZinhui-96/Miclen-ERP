# Praetorx Base - Test Suite

Comprehensive unit tests for the praetorx_base module covering all core functionality.

## Test Coverage

### test_queue_job.py (20 tests)
Tests for the background job queue system:
- Job creation and state management
- Success and failure scenarios
- Cron batch processing
- FIFO ordering
- Retry and cancel actions
- Edge cases (empty records, invalid JSON, missing records)

### test_validation_mixin.py (20 tests)
Tests for the validation mixin:
- HTML summary generation
- Error and warning display
- Validation state checks
- assert_valid() behavior
- Batch validation
- Field-specific error messages

### test_batch_processing_mixin.py (33 tests)
Tests for the batch processing state machine:
- State transitions (draft → validated → posted)
- Cancel and reset workflows
- Button visibility computation
- Delete restrictions
- Batch operations on multiple records
- Custom validation hooks
- is_editable() and is_posted() utilities

## Running Tests

### Run all praetorx_base tests:
```bash
cd /Volumes/External/Odoo\ Development/Hausverwaltung
odoo-bin -c config/odoo.conf \
  --test-tags praetorx \
  --stop-after-init \
  -d hausverwaltung \
  -u praetorx_base
```

### Run specific test file:
```bash
# Queue job tests only
odoo-bin -c config/odoo.conf \
  --test-tags praetorx \
  --test-file addons/praetorx_base/tests/test_queue_job.py \
  --stop-after-init \
  -d hausverwaltung

# Validation mixin tests only
odoo-bin -c config/odoo.conf \
  --test-tags praetorx \
  --test-file addons/praetorx_base/tests/test_validation_mixin.py \
  --stop-after-init \
  -d hausverwaltung

# Batch processing tests only
odoo-bin -c config/odoo.conf \
  --test-tags praetorx \
  --test-file addons/praetorx_base/tests/test_batch_processing_mixin.py \
  --stop-after-init \
  -d hausverwaltung
```

### Run with verbose output:
```bash
odoo-bin -c config/odoo.conf \
  --test-tags praetorx \
  --log-level test:DEBUG \
  --stop-after-init \
  -d hausverwaltung \
  -u praetorx_base
```

## Test Tags

All tests are tagged with:
- `post_install` - Run after module installation
- `-at_install` - Do not run during installation
- `praetorx` - Custom tag for filtering praetorx tests

## Test Structure

Each test class follows these conventions:
- `setUpClass()` - Create test data once for all tests
- `setUp()` - Reset state before each test
- Test methods numbered sequentially (test_01, test_02, ...)
- Clear docstrings describing what is being tested
- Self-contained tests with no dependencies between tests

## Edge Cases Covered

### Queue Jobs
- Invalid model names
- Invalid method names
- Malformed JSON in record_ids
- Non-existent records
- Empty record lists
- Processing already-processed jobs
- Concurrent batch processing

### Validation Mixin
- Empty validation results
- Errors only
- Warnings only
- Mixed errors and warnings
- Missing field names
- Batch validation across multiple records

### Batch Processing
- State transition restrictions
- Delete restrictions by state
- Batch operations on recordsets
- Custom validation hooks
- State tracking in chatter

## Expected Results

All 73 tests should pass:
- ✓ 20 queue job tests
- ✓ 20 validation mixin tests
- ✓ 33 batch processing tests (30 basic + 3 hooks)

## Notes

### Test Models
Some tests create temporary test models (test.batch.model, test.batch.validation)
for testing abstract mixins. These are only available during test execution.

### Database
Tests use TransactionCase which automatically rolls back changes after each test.
No test data persists in the database.

### Performance
All tests should complete in under 30 seconds total on standard hardware.

## Troubleshooting

### Tests not running
- Check database exists: `psql -l | grep hausverwaltung`
- Check module is installed: Look for `praetorx_base` in installed modules
- Check test tags match: Use `--test-tags praetorx`

### Import errors
- Ensure all dependencies are installed (base, mail)
- Check __init__.py includes all test files

### Random failures
- Tests should be deterministic
- If random failures occur, check for race conditions or state leakage
- Run individual test file to isolate issue
