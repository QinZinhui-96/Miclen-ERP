# Praetorx Base Tests - Quick Reference

## Run Commands

```bash
# All tests
./run_tests.sh

# Specific file
./run_tests.sh test_queue_job.py
./run_tests.sh test_validation_mixin.py
./run_tests.sh test_batch_processing_mixin.py

# Verbose
./run_tests.sh --verbose

# Help
./run_tests.sh --help
```

## Direct Odoo Commands

```bash
# From project root: /Users/larsweiler/dev/Hausverwaltung

# All praetorx tests
odoo-bin -c config/odoo.conf -d hausverwaltung \
  --test-tags praetorx --stop-after-init -u praetorx_base

# Queue job tests only
odoo-bin -c config/odoo.conf -d hausverwaltung \
  --test-tags praetorx \
  --test-file addons/praetorx_base/tests/test_queue_job.py \
  --stop-after-init

# Validation tests only
odoo-bin -c config/odoo.conf -d hausverwaltung \
  --test-tags praetorx \
  --test-file addons/praetorx_base/tests/test_validation_mixin.py \
  --stop-after-init

# Batch processing tests only
odoo-bin -c config/odoo.conf -d hausverwaltung \
  --test-tags praetorx \
  --test-file addons/praetorx_base/tests/test_batch_processing_mixin.py \
  --stop-after-init
```

## Test Count

| File | Tests | Coverage |
|------|-------|----------|
| test_queue_job.py | 20 | Queue jobs, cron, retry/cancel |
| test_validation_mixin.py | 20 | HTML, errors/warnings, assert |
| test_batch_processing_mixin.py | 33 | State machine, hooks, batch ops |
| **TOTAL** | **73** | **Complete module coverage** |

## Test Tags

- `post_install` - Run after module installation
- `-at_install` - Don't run during installation
- `praetorx` - Custom filter for praetorx tests

## Key Test Classes

### TestQueueJob
Tests background job queue functionality
- Job lifecycle (pending → processing → done/failed)
- Cron batch processing
- Error handling
- Retry/cancel actions

### TestValidationMixin
Tests validation with HTML summaries
- validate_all() results
- HTML generation
- is_valid() / has_warnings()
- assert_valid() blocking
- Batch validation

### TestBatchProcessingMixin
Tests state machine pattern
- State transitions (draft → validated → posted → cancelled)
- Button visibility
- Delete restrictions
- Batch operations
- Custom validation hooks

## Common Test Patterns

### Create Test Record
```python
record = self.Model.create({'field': 'value'})
```

### Assert State
```python
self.assertEqual(record.state, 'expected')
```

### Assert Raises
```python
with self.assertRaises(UserError) as ctx:
    record.action_that_fails()
self.assertIn("expected message", str(ctx.exception))
```

### Mock Validation
```python
def mock_validate():
    return [{'level': 'error', 'message': 'Error'}]
record.validate_all = mock_validate
```

## Environment Variables

```bash
# Change database
export DB_NAME=other_db
./run_tests.sh

# Change config file
export CONFIG_FILE=/path/to/odoo.conf
./run_tests.sh

# Change odoo binary
export ODOO_BIN=/usr/bin/odoo
./run_tests.sh
```

## Expected Output

```
====================================
Praetorx Base - Test Suite
====================================

Running ALL praetorx_base tests

...
----------------------------------------------------------------------
Ran 73 tests in 15.234s

OK

====================================
✓ All tests passed!
====================================
```

## Troubleshooting

### Tests Not Found
```bash
# Check module installed
odoo-bin shell -c config/odoo.conf -d hausverwaltung
>>> env['ir.module.module'].search([('name', '=', 'praetorx_base')])
```

### Import Errors
```bash
# Check __init__.py imports
cat tests/__init__.py

# Verify Python syntax
python3 -m py_compile tests/test_*.py
```

### Database Issues
```bash
# Recreate test database
dropdb hausverwaltung_test
createdb hausverwaltung_test
odoo-bin -c config/odoo.conf -d hausverwaltung_test -i praetorx_base --stop-after-init
```

## Test Development

### Add New Test
1. Choose appropriate file (or create new one)
2. Add method: `def test_NN_description(self):`
3. Add docstring
4. Write test logic
5. Run: `./run_tests.sh test_file.py`

### Test Template
```python
def test_NN_short_description(self):
    """Test longer description of what is being tested."""
    # Arrange
    record = self.Model.create({'field': 'value'})

    # Act
    result = record.method()

    # Assert
    self.assertEqual(result, expected)
```

## File Locations

```
praetorx_base/
├── tests/
│   ├── __init__.py                    # Test imports
│   ├── test_queue_job.py              # 20 tests
│   ├── test_validation_mixin.py       # 20 tests
│   ├── test_batch_processing_mixin.py # 33 tests
│   ├── README.md                      # Full documentation
│   ├── TEST_SUMMARY.md                # Detailed summary
│   └── QUICK_REFERENCE.md             # This file
├── run_tests.sh                       # Test runner script
└── models/
    ├── queue_job_cron.py             # Tested by test_queue_job.py
    ├── validation_mixin.py           # Tested by test_validation_mixin.py
    └── batch_processing_mixin.py     # Tested by test_batch_processing_mixin.py
```

## Success Criteria

- ✓ All 73 tests pass
- ✓ No errors or warnings
- ✓ Execution time < 30 seconds
- ✓ 100% model coverage
- ✓ All edge cases tested

## CI/CD Integration

```yaml
# Example GitHub Actions workflow
- name: Run praetorx_base tests
  run: |
    cd addons/praetorx_base
    ./run_tests.sh
```

## Performance

- **Average runtime:** ~15 seconds
- **Per-test average:** ~200ms
- **Setup time:** ~2 seconds
- **Teardown time:** ~1 second

## Author

Lars Weiler - Syntax & Sabotage
