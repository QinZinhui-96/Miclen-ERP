# Praetorx Base

**Version:** 19.0.1.0.0
**Author:** Lars Weiler
**Maintainer:** Syntax & Sabotage
**License:** LGPL-3

## Overview

Praetorx Base is a technical foundation module that provides reusable patterns extracted from production Odoo implementations. It serves as a building block for robust, maintainable Odoo applications.

## Key Features

### 1. Queue Job System (`praetorx.queue.job`)

Background job processing via cron with state management.

**Use Cases:**
- Process large datasets without blocking UI
- Batch operations on multiple records
- Asynchronous calculations and updates

**Example:**
```python
self.env['praetorx.queue.job'].create({
    'name': 'Update Product Prices',
    'model_name': 'product.product',
    'method_name': 'recompute_prices',
    'record_ids': json.dumps([1, 2, 3, 4, 5])
})
```

**Features:**
- Automatic processing via cron (every 1 minute)
- State tracking (pending → processing → done/failed)
- Error logging and retry capability
- Batch processing (100 jobs per run)
- User-friendly notifications

### 2. Validation Mixin (`praetorx.validation.mixin`)

Structured validation with HTML-formatted summaries.

**Use Cases:**
- Complex document validation
- Multi-step validation workflows
- User-friendly validation feedback

**Example:**
```python
class MyModel(models.Model):
    _name = 'my.model'
    _inherit = ['praetorx.validation.mixin']

    validation_summary = fields.Html(
        compute='_compute_validation_summary',
        sanitize=False
    )

    def validate_all(self):
        results = []
        if not self.required_field:
            results.append({
                'level': 'error',
                'message': 'Required field is missing',
                'field': 'required_field'
            })
        if self.amount < 0:
            results.append({
                'level': 'warning',
                'message': 'Amount is negative',
                'field': 'amount'
            })
        return results

    @api.depends('required_field', 'amount')
    def _compute_validation_summary(self):
        for record in self:
            record.validation_summary = record.get_validation_summary_html()
```

**Features:**
- Structured validation results (errors vs warnings)
- HTML-formatted summaries with Bootstrap styling
- Helper methods: `is_valid()`, `assert_valid()`, `get_validation_errors()`
- Batch validation support

### 3. Batch Processing Mixin (`praetorx.batch.mixin`)

State machine pattern for parent-child workflows.

**Use Cases:**
- Document workflows (invoices, settlements, orders)
- Header-line patterns (batch processing)
- Multi-stage approval processes

**Example:**
```python
class Settlement(models.Model):
    _name = 'my.settlement'
    _inherit = ['praetorx.batch.mixin']

    line_ids = fields.One2many('my.settlement.line', 'settlement_id')

    def _validate_before_post(self):
        super()._validate_before_post()
        if not self.line_ids:
            raise UserError("Cannot post without lines")

    def _post_processing(self):
        super()._post_processing()
        self._create_journal_entries()
```

**Features:**
- Standard workflow: draft → validated → posted
- Cancellation support with reset to draft
- Extensible validation hooks
- Button visibility computed automatically
- Deletion protection for posted documents

### 4. Split View OWL Component

Reusable master-detail UI pattern.

**Use Cases:**
- Email-style interfaces (list + detail)
- Settings panels (categories + options)
- Document browsers (files + preview)

**Example:**
```xml
<SplitView
    masterItems="state.items"
    selectedId="state.selectedId"
    onSelect.bind="onItemSelect"
    masterWidth="'30%'"
>
    <t t-set-slot="master" t-slot-scope="item">
        <div t-esc="item.name"/>
    </t>
    <t t-set-slot="detail" t-slot-scope="selected">
        <div t-esc="selected.description"/>
    </t>
</SplitView>
```

**Features:**
- Customizable master/detail widths
- Slot-based content injection
- Active item tracking
- Responsive layout
- Empty state handling

## Installation

1. Add module to addons path
2. Update apps list
3. Install "Praetorx Base"

## Dependencies

- `base`
- `mail`

## Technical Details

All patterns are implemented as abstract models or mixins that can be inherited by concrete models. This promotes:

- **Code Reuse:** Write once, use everywhere
- **Consistency:** Standard patterns across modules
- **Maintainability:** Changes propagate to inheriting models
- **Testability:** Patterns are well-tested in production

## Usage in Other Modules

Add `praetorx_base` to module dependencies:

```python
{
    'name': 'My Module',
    'depends': ['praetorx_base'],
    # ...
}
```

Then inherit the patterns you need:

```python
class MyModel(models.Model):
    _name = 'my.model'
    _inherit = [
        'praetorx.validation.mixin',
        'praetorx.batch.mixin',
    ]
```

## Support

**Website:** https://praetorx.net
**Email:** support@syntaxandsabotage.io

## Credits

Patterns extracted from real-world implementations including:
- Compay Subledger Module (accounting workflows)
- CUSTODIA Suite (property management)
- Various client projects (2020-2025)

## License

LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html)

Copyright 2025 Lars Weiler
