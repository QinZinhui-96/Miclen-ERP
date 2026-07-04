# Miclen ERP - Odoo 19 AI 代码规范指南

> **本文件供 AI 助手阅读，每次生成或修改本模块代码前必须先阅读本文件，确保产出符合 Odoo 19 语法和本项目编码规范。**
>
> 最后更新: 2026-07-03
> Odoo 版本: 19.0
> 模块版本: 19.0.1.0
> 模块名: miclen_project

---

## 目录

1. [项目概览](#1-项目概览)
2. [Odoo 19 关键语法变更（必读）](#2-odoo-19-关键语法变更必读)
3. [目录结构规范](#3-目录结构规范)
4. [Python 代码规范](#4-python-代码规范)
5. [XML 视图规范](#5-xml-视图规范)
6. [Security 安全规范](#6-security-安全规范)
7. [Data 种子数据规范](#7-data-种子数据规范)
8. [前端 JS / OWL 规范](#8-前端-js--owl-规范)
9. [__manifest__.py 规范](#9-__manifestpy-规范)
10. [命名约定](#10-命名约定)
11. [业务逻辑模式](#11-业务逻辑模式)
12. [常见陷阱与避坑](#12-常见陷阱与避坑)
13. [文件清单与职责](#13-文件清单与职责)

---

## 1. 项目概览

### 1.1 模块定位

`miclen_project` 是 Miclen ERP 的核心定制模块，运行在 Odoo 19 之上，主要实现：

- **行级数据权限控制**：基于 `ir.rule` + `manager_users` 字段，实现作业类型/质量团队/工作中心的按用户隔离
- **采购/销售合作伙伴过滤**：过滤掉个人联系人，仅显示公司型供应商/客户
- **产品三级分类编码体系**：大类→中类→小类 + 宽幅，自动拼接生成 `default_code`
- **工序标准化配置**：工序配置表 → 路由工序 → BOM → 工单 → 看板全链路贯通
- **批量初始化工具**：一键分配作业类型管理用户、一键分配 Odoo 权限组

### 1.2 依赖模块

```python
'depends': ['stock', 'purchase', 'sale', 'mrp', 'quality_control', 'maintenance']
```

### 1.3 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.10+, Odoo 19 ORM |
| 视图 | XML (ir.ui.view) |
| 前端 | 原生 JS + OWL 模板继承 (不使用 @odoo/owl import 方式) |
| 数据库 | PostgreSQL |
| RPC | fetch + JSON-RPC (`/web/dataset/call_kw`) |

---

## 2. Odoo 19 关键语法变更（必读）

### 2.1 `<tree>` → `<list>`（最重要）

**Odoo 19 中，树状列表视图标签从 `<tree>` 改为 `<list>`。** AI 生成代码时必须使用 `<list>`，不得使用 `<tree>`。

```xml
<!-- 正确 (Odoo 19) -->
<list string="Miclen产品类别配置" editable="bottom">
    <field name="sequence" widget="handle"/>
    <field name="name" required="1"/>
</list>

<!-- 错误 (Odoo 17 及以下) -->
<tree string="Miclen产品类别配置" editable="bottom">
    ...
</tree>
```

### 2.2 字段导入方式

Odoo 19 中 `fields.Command` 和 `Domain` 从 `odoo.fields` 导入，而非从 `odoo` 顶层导入：

```python
# 正确 (Odoo 19)
from odoo.fields import Command, Domain

# 旧版写法 (Odoo 16 及以下，不要使用)
from odoo import Command  # 错误!
```

### 2.3 `tool` 模块导入

Odoo 19 的工具函数导入路径：

```python
from odoo.tools import format_amount, format_date, formatLang, groupby, OrderedSet, SQL
from odoo.tools.float_utils import float_is_zero, float_repr
from odoo.exceptions import AccessDenied, UserError, ValidationError
```

### 2.4 `markupsafe` 替代 `html_escape`

```python
# Odoo 19
from markupsafe import escape, Markup
```

### 2.5 `group_ids` 替代 `groups_id`

Odoo 19 中 `res.users` 的权限组字段从 `groups_id` (Many2many) 改为 `group_ids`：

```python
# 正确 (Odoo 19)
user.write({'group_ids': [(6, 0, [group.id for group in groups])]})

# 错误 (Odoo 18 及以下)
user.write({'groups_id': [(6, 0, [group.id for group in groups])]})
```

### 2.6 计算字段 `store=True` + `readonly=False` 模式

Odoo 19 中，如果计算字段需要存储且允许用户手动覆盖，必须同时设置 `store=True` 和 `readonly=False`：

```python
name = fields.Char(
    string='工序名称',
    compute='_compute_miclen_fields',
    store=True,
    readonly=False  # 允许手动覆盖计算结果
)
```

### 2.7 `related` 字段直接写入

Odoo 19 中 `related` 字段默认可写，如需存储到当前模型需显式设置 `store=True`：

```python
miclen_work_id = fields.Many2one(
    related='operation_id.miclen_work_id',
    store=True,
    readonly=False,
    string='工序'
)
```

### 2.8 XML 中 `noupdate` 写法

```xml
<!-- Odoo 19 支持 data noupdate="1" -->
<data noupdate="1">
    <record id="xxx" model="xxx">
        ...
    </record>
</data>
```

### 2.9 `ir.model.access.csv` 权限分配

Odoo 19 中 `group_id:id` 列留空表示所有用户可见：

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_miclen_product_category,miclen.product.category,model_miclen_product_category,,1,1,1,1
```

### 2.10 OWL 模板继承语法

Odoo 19 OWL 模板继承使用 `t-inherit` + `t-inherit-mode="extension"` + `owl="1"`：

```xml
<templates xml:space="preserve">
    <t t-inherit="mrp_workorder.MrpDisplayRecord" t-inherit-mode="extension" owl="1">
        <xpath expr="//div[hasclass('o_mrp_display_record')]" position="inside">
            ...
        </xpath>
    </t>
</templates>
```

---

## 3. 目录结构规范

### 3.1 标准目录布局

```
miclen_project/
├── __init__.py                    # 入口，导入 models
├── __manifest__.py                # 模块清单
├── models/
│   ├── __init__.py                # 导入所有模型
│   ├── product_template.py        # product.template 继承 + 批量工具方法
│   ├── stock_picking_type.py      # stock.picking.type 继承
│   ├── quality_alert_team.py      # quality.alert.team 继承
│   ├── mrp_workcenter.py          # mrp.workcenter 继承
│   ├── purchase_order.py          # purchase.order 继承
│   ├── miclen_product_category.py # 新模型: 大类
│   ├── miclen_category_details.py # 新模型: 中类
│   ├── miclen_category_subcategory.py # 新模型: 小类
│   ├── miclen_mrp_workcenter.py   # 新模型: 工序配置表
│   ├── mrp_routing.py             # mrp.routing.workcenter 继承
│   ├── mrp_production.py          # mrp.production 继承
│   └── mrp_workorder.py           # mrp.workorder 继承
├── views/
│   ├── *.xml                      # 每个模型对应一个视图文件
│   ├── actions.xml                # 集中定义 ir.actions.act_window
│   └── menus.xml                  # 集中定义 menuitem
├── security/
│   ├── ir.model.access.csv        # 模型级 CRUD 权限
│   └── ir_rule.xml                # 行级数据权限规则
├── data/
│   └── *.xml                      # 种子数据 (noupdate="1")
└── static/
    └── src/
        └── mrp_display_record_ext/
            ├── js/
            │   └── mrp_display_record.js
            └── xml/
                └── mrp_display_record.xml
```

### 3.2 __init__.py 导入顺序

`models/__init__.py` 中的导入顺序应与 `__manifest__.py` 的 `data` 列表顺序保持一致，便于代码审查：

```python
from . import product_template
from . import stock_picking_type
from . import quality_alert_team
from . import mrp_workcenter
from . import purchase_order
from . import miclen_product_category
from . import miclen_category_details
from . import miclen_category_subcategory
from . import miclen_mrp_workcenter
from . import mrp_routing
from . import mrp_production
from . import mrp_workorder
```

### 3.3 __manifest__.py data 加载顺序

加载顺序有严格依赖关系，必须按以下顺序：

1. `security/ir.model.access.csv` — 权限先加载
2. `security/ir_rule.xml` — 行级规则
3. `views/*.xml` — 视图
4. `data/*.xml` — 种子数据（在视图之后，因为可能引用视图）
5. `views/actions.xml` — 动作
6. `views/menus.xml` — 菜单（最后加载，引用动作）

---

## 4. Python 代码规范

### 4.1 文件头

每个 Python 文件以 UTF-8 编码声明开头：

```python
# -*- coding: utf-8 -*-
```

### 4.2 导入规范

按以下顺序分组导入：

```python
# 1. 标准库
import logging
from collections import defaultdict
from datetime import datetime

# 2. 第三方库
from dateutil.relativedelta import relativedelta
from pytz import timezone
from ast import literal_eval
from markupsafe import escape, Markup

# 3. Odoo 核心
from odoo import api, fields, models, _
from odoo.fields import Command, Domain
from odoo.tools import format_amount, format_date, formatLang, groupby, OrderedSet, SQL
from odoo.tools.float_utils import float_is_zero, float_repr
from odoo.exceptions import AccessDenied, UserError, ValidationError

# 4. Logger
_logger = logging.getLogger(__name__)
```

**注意**：不是每个文件都需要全部导入，按需导入即可。简单模型只需 `from odoo import fields, models`。

### 4.3 模型定义

#### 4.3.1 继承现有模型 (`_inherit`)

```python
class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    _description = "作业类型中增加仓管"

    manager_users = fields.Many2many(
        'res.users',
        string='管理用户',
        help='选择哪些用户可以查看此作业类型'
    )
```

**规范**：
- 类名使用 PascalCase，与原模型名一致
- `_inherit` 值为字符串（单表继承）
- `_description` 必填，使用中文描述
- 字段定义的 `string` 参数使用中文

#### 4.3.2 新建模型 (`_name`)

```python
class MiclenProductCategory(models.Model):
    _name = 'miclen.product.category'
    _description = "miclen产品类型"

    sequence = fields.Integer('序号', default=10)
    name = fields.Char('编码', tracking=True)
    note = fields.Char('备注', tracking=True)
```

**规范**：
- `_name` 使用点分式，以 `miclen.` 前缀开头
- 类名使用 PascalCase
- 新模型必须有序号字段 `sequence`（用于拖拽排序）
- `name` 字段作为编码字段，不是显示名称

### 4.4 字段定义规范

```python
# Many2one
miclen_category_id = fields.Many2one('miclen.product.category', string='大类', copy=False)

# Many2many
manager_users = fields.Many2many('res.users', string='管理用户', help='选择哪些用户可以查看此作业类型')

# Many2many (关联中间表)
equipment_ids = fields.Many2many('maintenance.equipment', string='设备和工具')

# Char
miclen_width = fields.Char('宽幅')
printing_plate = fields.Char(string='网版')

# Integer (序号)
sequence = fields.Integer('序号', default=10)

# 计算字段 (存储)
description = fields.Char('工序', compute='_compute_name', store=True)

# 计算字段 (存储 + 可覆盖)
name = fields.Char(
    string='工序名称',
    compute='_compute_miclen_fields',
    store=True,
    readonly=False
)

# Related 字段
miclen_work_id = fields.Many2one(
    related='operation_id.miclen_work_id',
    store=True,
    readonly=False,
    string='工序'
)

# Related Many2many (不存储)
equipment_ids = fields.Many2many(
    related='operation_id.equipment_ids',
    string='设备和工具'
)
```

### 4.5 计算方法规范

```python
@api.depends('miclen_category_id', 'miclen_details_id',
             'miclen_subcategory_id', 'miclen_width')
def _compute_default_code(self):
    # 先调用父类方法（处理变体同步）
    super()._compute_default_code()
    # 然后添加自定义逻辑
    for record in self:
        if record.miclen_category_id:
            parts = []
            if record.miclen_category_id:
                parts.append(record.miclen_category_id.name)
            if record.miclen_details_id:
                parts.append(record.miclen_details_id.name)
            if record.miclen_subcategory_id:
                parts.append(record.miclen_subcategory_id.name)
            if record.miclen_width:
                parts.append(record.miclen_width)
            record.default_code = '-'.join(parts) if parts else ''
```

**规范**：
- 方法名以 `_compute_` 开头
- `@api.depends` 必须列出所有依赖字段
- 如果覆盖父类计算方法，先调用 `super()._compute_xxx()`
- 方法体内必须遍历 `self`（`for record in self:`），因为 `self` 可能是多条记录
- 计算字段如果需要清空，使用 `False`（Many2one/Many2many）或 `''`（Char）

### 4.6 create() 重写规范

```python
def create(self, vals_list):
    """
        导入数据的时候直接可以使用工序名称即可导入
    """
    for vals in vals_list:
        work_name = vals.get('miclen_work_id')
        if work_name and not vals.get('workcenter_id') and not vals.get('name'):
            work = self.env['miclen.mrp.workcenter'].browse(vals['miclen_work_id'])
            vals['name'] = work.name
            vals['workcenter_id'] = work.workcenter_id.id
            vals['equipment_ids'] = [(6, 0, work.equipment_ids.ids)]
            vals['printing_plate'] = work.printing_plate
            vals['die_mold'] = work.die_mold
    return super().create(vals_list)
```

**规范**：
- `create()` 的参数是 `vals_list`（列表），不是 `vals`（字典），Odoo 19 统一使用批量创建
- 遍历 `vals_list` 进行预处理
- 最后必须调用 `super().create(vals_list)`
- 使用 docstring 说明重写原因

### 4.7 Many2many 操作元组

```python
# (6, 0, ids) — 替换全部关联
record.write({'manager_users': [(6, 0, users.ids)]})

# (5, 0, 0) — 清空所有关联
record.equipment_ids = [(5, 0, 0)]

# (4, id, 0) — 添加单个关联
# (3, id, 0) — 移除单个关联
# (6, 0, ids) — 替换全部（最常用）
```

### 4.8 动态 domain 字段

本项目中使用计算字段生成 domain 字符串，供视图层 `domain="equipment_domain"` 使用：

```python
equipment_domain = fields.Char(
    '设备详情',
    compute='_compute_equipment_domain',
    store=True
)

@api.depends('workcenter_id')
def _compute_equipment_domain(self):
    for rec in self:
        if rec.workcenter_id:
            equipments = rec.workcenter_id.equipment_ids.ids
            rec.equipment_domain = "[('id', 'in', %s)]" % equipments
        else:
            rec.equipment_domain = "[('id', '=', -1)]"  # 空集
```

### 4.9 sudo() 使用规范

```python
# 需要绕过权限检查时使用 sudo()
picking_ids = self.env['stock.picking.type'].sudo().search([])
users = self.env['res.users'].sudo().search([('login', 'in', [...])])
```

**规范**：
- 仅在初始化工具方法或 cron 任务中使用 `sudo()`
- 普通业务方法中避免使用 `sudo()`，依赖 ir.rule 自动过滤
- `sudo()` 链应紧跟在 `self.env['model']` 之后

### 4.10 Logger 使用规范

```python
_logger = logging.getLogger(__name__)

# 信息日志
_logger.info(f"✅IN: {pick.name} 已分配用户: {[u.login for u in users]}")

# 警告日志
_logger.info(f"⚠️ 跳过未配置的用户: {user.login}")
```

### 4.11 权限组引用规范

```python
# 通过 self.env.ref() 获取权限组
group_user = self.env.ref('base.group_user')
group_system = self.env.ref('base.group_system')
group_sale_manager = self.env.ref('sales_team.group_sale_manager')
group_purchase_manager = self.env.ref('purchase.group_purchase_manager')
group_stock_manager = self.env.ref('stock.group_stock_manager')
group_mrp_manager = self.env.ref('mrp.group_mrp_manager')
group_quality_manager = self.env.ref('quality.group_quality_manager')
group_equipment_manager = self.env.ref('maintenance.group_equipment_manager')
group_account_manager = self.env.ref('account.group_account_manager')
```

---

## 5. XML 视图规范

### 5.1 文件头

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    ...
</odoo>
```

### 5.2 视图继承 (xpath 方式)

```xml
<record id="view_stock_picking_type_form_inherit" model="ir.ui.view">
    <field name="name">stock.picking.type.form.inherit</field>
    <field name="model">stock.picking.type</field>
    <field name="inherit_id" ref="stock.view_picking_type_form"/>
    <field name="arch" type="xml">
        <xpath expr="//field[@name='create_backorder']" position="after">
            <field name="manager_users" widget="many2many_tags"
                   options="{'no_create': True, 'no_open': True}"/>
        </xpath>
    </field>
</record>
```

**position 可选值**：
- `after` — 在目标元素之后
- `before` — 在目标元素之前
- `inside` — 在目标元素内部（末尾）
- `replace` — 替换目标元素
- `attributes` — 修改目标元素的属性

### 5.3 xpath 简写

当目标元素是 `<field>` 且 position 为 `after` 或 `before` 时，可省略 xpath：

```xml
<!-- 简写 -->
<field name="name" position="after">
    <field name="miclen_work_id" optional="show"/>
</field>

<!-- 等价的完整 xpath 写法 -->
<xpath expr="//field[@name='name']" position="after">
    <field name="miclen_work_id" optional="show"/>
</xpath>
```

### 5.4 group 内部插入

```xml
<!-- 使用 position="inside" 向 group 中添加字段 -->
<group name="costing" position="inside">
    <field name="manager_users" widget="many2many_tags"
           options="{'no_create': True, 'no_open': True}"/>
</group>
```

### 5.5 修改字段属性

```xml
<xpath expr="//field[@name='partner_id']" position="attributes">
    <attribute name="domain">[('is_company', '=', True), ('supplier_rank', '>', 0)]</attribute>
</xpath>
```

### 5.6 替换整个字段

```xml
<xpath expr="//page[@name='operations']/field[@name='operation_ids']" position="replace">
    <field name="operation_ids" context="{'default_bom_id': id}">
        <list editable="bottom">
            <field name="sequence" widget="handle"/>
            <field name="miclen_work_id" required="1"/>
            ...
        </list>
    </field>
</xpath>
```

### 5.7 列表视图 (`<list>`)

**Odoo 19 必须使用 `<list>` 而非 `<tree>`：**

```xml
<list string="Miclen工序配置表" editable="bottom">
    <field name="sequence" widget="handle"/>
    <field name="name" required="1"/>
    <field name="workcenter_id" required="1" options="{'no_create': True, 'no_open': True}"/>
    <field name="equipment_domain" column_invisible="1"/>
    <field name="equipment_ids" widget="many2many_tags"
           domain="equipment_domain"
           options="{'no_create': True, 'no_open': True}"/>
    <field name="printing_plate"/>
    <field name="die_mold"/>
    <field name="description"/>
</list>
```

**常用属性**：
- `editable="bottom"` — 行内编辑，新行加在底部
- `column_invisible="1"` — 字段存在但不显示列（用于传递 domain）
- `optional="show"` — 默认显示列，用户可隐藏
- `optional="hide"` — 默认隐藏列，用户可显示

### 5.8 表单视图 (`<form>`)

```xml
<form>
    <sheet>
        <div class="oe_title">
            <h2>
                <field name="description" required="1" nolabel="1" placeholder="工序"/>
            </h2>
        </div>
        <group>
            <group>
                <field name="name" required="1"/>
                <field name="equipment_ids"/>
                <field name="printing_plate"/>
            </group>
            <group>
                <field name="workcenter_id" required="1"/>
                <field name="die_mold"/>
            </group>
        </group>
    </sheet>
</form>
```

### 5.9 搜索视图

```xml
<record id="miclen_mrp_routing_workcenter_search" model="ir.ui.view">
    <field name="name">mrp.routing.workcenter.search.custom</field>
    <field name="model">mrp.routing.workcenter</field>
    <field name="inherit_id" ref="mrp.mrp_routing_workcenter_filter"/>
    <field name="arch" type="xml">
        <xpath expr="//search" position="inside">
            <field name="miclen_work_id" invisible="1"/>
            <field name="equipment_ids" invisible="1"/>
            <field name="printing_plate" invisible="1"/>
            <field name="die_mold" invisible="1"/>
        </xpath>
    </field>
</record>
```

**注意**：在搜索视图中声明字段是强制加载字段数据的方式，即使 `invisible="1"` 也会将字段数据传到前端。这对于看板视图的 JS 异步加载尤其重要。

### 5.10 看板视图继承

```xml
<record id="miclen_inherit_workcenter_line_kanban_view" model="ir.ui.view">
    <field name="name">mrp.production.work.order.kanban.custom</field>
    <field name="model">mrp.workorder</field>
    <field name="inherit_id" ref="mrp.workcenter_line_kanban"/>
    <field name="arch" type="xml">
        <xpath expr="//kanban" position="inside">
            <field name="miclen_work_id"/>
            <field name="equipment_ids" widget="many2many_tags"/>
            <field name="printing_plate"/>
            <field name="die_mold"/>
        </xpath>
    </field>
</record>
```

### 5.11 常用 widget

| widget | 用途 |
|--------|------|
| `many2many_tags` | Many2many 字段的标签展示 |
| `handle` | Integer 序号字段的拖拽排序 |

### 5.12 常用 options

```xml
options="{'no_create': True, 'no_open': True}"
```

| option | 含义 |
|--------|------|
| `no_create: True` | 禁止在下拉中创建新记录 |
| `no_open: True` | 禁止在下拉中打开记录详情 |

### 5.13 动态 domain 在视图中的使用

```xml
<field name="equipment_domain" column_invisible="1"/>
<field name="equipment_ids"
       domain="equipment_domain"
       widget="many2many_tags"
       options="{'no_create': True, 'no_open': True}"/>
```

**模式**：先用一个 `column_invisible="1"` 的字段暴露计算出的 domain 字符串，再在目标字段的 `domain` 属性中引用它。

### 5.14 动作定义 (ir.actions.act_window)

```xml
<record model="ir.actions.act_window" id="action_miclen_mrp_workcenter">
    <field name="name">工序配置</field>
    <field name="res_model">miclen.mrp.workcenter</field>
    <field name="view_mode">list,form</field>
</record>
```

**注意**：Odoo 19 中 `view_mode` 使用 `list` 而非 `tree`。

### 5.15 菜单定义 (menuitem)

```xml
<menuitem id="menu_action_miclen_mrp_workcenter"
          name="工序配置"
          parent="mrp.menu_mrp_configuration"
          sequence="200"
          action="action_miclen_mrp_workcenter"/>
```

**规范**：
- `parent` 引用已有模块的菜单（如 `stock.menu_product_in_config_stock`、`mrp.menu_mrp_configuration`）
- `sequence` 控制菜单排列顺序
- `action` 引用上面定义的 act_window

---

## 6. Security 安全规范

### 6.1 ir.model.access.csv

每个新模型必须在 `ir.model.access.csv` 中声明权限。格式：

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_miclen_product_category,miclen.product.category,model_miclen_product_category,,1,1,1,1
```

**字段说明**：
- `id` — 权限记录的 XML ID，格式 `access_{模型名}`
- `name` — 显示名称
- `model_id:id` — 模型的 XML ID，格式 `model_{模型名（下划线连接）}`
- `group_id:id` — 留空表示所有用户
- `perm_read/perm_write/perm_create/perm_unlink` — 1 表示允许，0 表示禁止

**本项目规范**：新模型的 `group_id:id` 留空（所有用户可访问），行级权限由 `ir.rule` 控制。

### 6.2 ir.rule 行级权限

每个需要权限隔离的模型配两条规则：

```xml
<data noupdate="1">
    <!-- 规则1：管理员全部可见 -->
    <record id="miclen_stock_picking_type_rule_admin" model="ir.rule">
        <field name="name">库存概览 - 管理员全部可见</field>
        <field name="model_id" ref="stock.model_stock_picking_type"/>
        <field name="domain_force">[(1, '=', 1)]</field>
        <field name="groups" eval="[(4, ref('base.group_system'))]"/>
        <field name="perm_read" eval="True"/>
        <field name="perm_write" eval="True"/>
        <field name="perm_create" eval="True"/>
        <field name="perm_unlink" eval="True"/>
    </record>

    <!-- 规则2：普通用户只能看到自己被分配的 -->
    <record id="miclen_stock_picking_type_rule_user" model="ir.rule">
        <field name="name">库存概览 - 按负责人限制</field>
        <field name="model_id" ref="stock.model_stock_picking_type"/>
        <field name="domain_force">[('manager_users', 'in', user.ids)]</field>
        <field name="groups" eval="[(4, ref('base.group_user'))]"/>
        <field name="perm_read" eval="True"/>
        <field name="perm_write" eval="True"/>
        <field name="perm_create" eval="False"/>
        <field name="perm_unlink" eval="False"/>
    </record>
</data>
```

**规则模式**：
- 管理员组 (`base.group_system`)：`domain_force = [(1, '=', 1)]`，全部 CRUD
- 普通用户组 (`base.group_user`)：`domain_force = [('manager_users', 'in', user.ids)]`，仅读 + 写（不可创建/删除）
- 使用 `noupdate="1"` 防止模块升级时覆盖手动调整

**注意**：`model_id` 的 ref 格式是 `{模块名}.model_{模型名（下划线连接）}`，例如 `stock.model_stock_picking_type`。

---

## 7. Data 种子数据规范

### 7.1 文件格式

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<odoo>
    <data noupdate="1">
        <record id="data_category_rm" model="miclen.product.category">
            <field name="sequence">1</field>
            <field name="note">原始未加工材料，通常需经丝印、CNC、冲压或模切</field>
            <field name="name">RM</field>
        </record>
    </data>
</odoo>
```

### 7.2 规范

- 使用 `<data noupdate="1">` 包裹，防止模块升级时重复创建或覆盖
- `id` 命名格式：`data_{模型简称}_{序号或缩写}`
- `sequence` 必须设置，控制排序
- `name` 字段存编码值（如 RM、PT、ASM），不是中文描述
- `note` 字段存中文说明

### 7.3 预置数据体系

本项目预置了产品大类编码：

| 编码 | 含义 | 序号 |
|------|------|------|
| RM | 原始未加工材料 | 1 |
| PT | 自制零件 | 2 |
| ASM | 自制半成品 | 3 |
| ASSY | 最终交付成品 | 4 |
| BO | 外购成品件 | 5 |

---

## 8. 前端 JS / OWL 规范

### 8.1 OWL 模板继承

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-inherit="mrp_workorder.MrpDisplayRecord"
       t-inherit-mode="extension"
       owl="1">
        <xpath expr="//div[hasclass('o_mrp_display_record')]" position="inside">
            <!-- 自定义内容 -->
        </xpath>
    </t>
</templates>
```

**规范**：
- `xml:space="preserve"` 必须设置
- `t-inherit` 指向被继承的模板 ID
- `t-inherit-mode="extension"` 表示扩展模式
- `owl="1"` 标识 OWL 组件

### 8.2 OWL 模板中数据传递

```xml
<!-- 通过 props.record.data 访问字段值 -->
<t t-esc="props.record.data.id"/>
<t t-esc="props.record.data.operation_id.id"/>
<t t-esc="props.record.data.operation_id.display_name or props.record.data.operation_id.id"/>
```

### 8.3 OWL 模板中隐藏数据传递

当需要在原生 JS 中访问 OWL 组件的数据时，使用隐藏 input 作为桥梁：

```xml
<input type="hidden" class="mrp-workorder-id" t-att-value="props.record.data.id"/>
<input type="hidden" class="mrp-operation-id" t-att-value="props.record.data.operation_id.id"/>
```

### 8.4 原生 JS 规范

本项目的前端 JS 不使用 OWL 组件类继承方式，而是使用原生 JS + DOM 操作 + JSON-RPC：

```javascript
// CSRF Token 获取
function getCSRFToken() {
    return window.odoo?.csrf_token ||
           document.querySelector('meta[name="csrf-token"]')?.content ||
           '';
}

// JSON-RPC 调用
async function loadOperationData(operationId) {
    const csrfToken = getCSRFToken();
    const response = await fetch('/web/dataset/call_kw', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Odoo-CSRF-Token': csrfToken
        },
        body: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            params: {
                model: 'mrp.routing.workcenter',
                method: 'read',
                args: [[parseInt(operationId)], ['miclen_work_id', 'equipment_ids', 'printing_plate', 'die_mold']],
                kwargs: { context: {} }
            },
            id: Date.now()
        })
    });
    const result = await response.json();
    return result.result?.[0] || null;
}
```

### 8.5 DOM 监听模式

```javascript
// MutationObserver 监听新卡片出现
const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
        if (mutation.addedNodes.length > 0) {
            const cards = document.querySelectorAll(
                '.card-footer.bg-light.p-2.border-top:not([data-mrp-updated])'
            );
            if (cards.length > 0) {
                setTimeout(processAllCards, 2000);
            }
            break;
        }
    }
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});
```

### 8.6 防重复处理

```javascript
// 使用 dataset 标记已处理过的 DOM 元素
if (card.dataset.mrpUpdated === 'true') {
    continue;
}
// 处理完成后标记
card.dataset.mrpUpdated = 'true';
```

### 8.7 资源声明

在 `__manifest__.py` 的 `assets` 中声明前端资源：

```python
'assets': {
    'web.assets_backend': [
        'miclen_project/static/src/mrp_display_record_ext/xml/mrp_display_record.xml',
        'miclen_project/static/src/mrp_display_record_ext/js/mrp_display_record.js',
    ],
},
```

**规范**：
- XML 模板在 JS 之前加载
- 路径以模块名 `miclen_project/` 开头
- 挂载到 `web.assets_backend`（后端资源包）

---

## 9. __manifest__.py 规范

### 9.1 完整模板

```python
# -*- coding: utf-8 -*-
{
    'name': 'Miclen Project Manager',
    'version': '19.0.1.0',              # 格式: {odoo版本}.{major}.{minor}
    'category': 'Miclen',
    "website": "https://erp.miclen.com",
    'summary': '一句话描述模块用途',
    'description': """
        详细描述，每条功能一行
    """,
    'depends': ['stock', 'purchase', 'sale', 'mrp', 'quality_control', 'maintenance'],
    'data': [
        # 1. 权限
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        # 2. 视图
        'views/xxx_view.xml',
        # 3. 数据
        'data/xxx_data.xml',
        # 4. 动作和菜单
        'views/actions.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'miclen_project/static/src/...',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'author': 'Miclen.',
    'license': 'LGPL-3',
}
```

### 9.2 data 加载顺序原则

```
security/ir.model.access.csv   ← 模型权限先加载
security/ir_rule.xml           ← 行级规则
views/*.xml                    ← 视图 (继承视图 + 新视图)
data/*.xml                     ← 种子数据
views/actions.xml              ← 动作 (引用视图)
views/menus.xml                ← 菜单 (引用动作)
```

---

## 10. 命名约定

### 10.1 Python 命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 类名 | PascalCase | `MiclenProductCategory` |
| 模型名 (`_name`) | 点分式，miclen. 前缀 | `miclen.product.category` |
| 字段名 | snake_case | `miclen_category_id` |
| 方法名 | snake_case | `_compute_default_code` |
| 计算方法 | `_compute_` 前缀 | `_compute_equipment_domain` |
| 常量 | UPPER_SNAKE_CASE | (本项目中暂无) |
| Logger | `_logger` | `_logger = logging.getLogger(__name__)` |

### 10.2 XML 命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 视图 record id | `{模块前缀}_{模型名}_{视图类型}_view` | `miclen_product_category_list_view` |
| 继承视图 id | `view_{模型名}_{视图类型}_inherit` | `view_stock_picking_type_form_inherit` |
| 动作 id | `action_{模型名}` | `action_miclen_mrp_workcenter` |
| 菜单 id | `menu_action_{动作id}` | `menu_action_miclen_mrp_workcenter` |
| ir.rule id | `miclen_{模型名}_rule_{角色}` | `miclen_stock_picking_type_rule_admin` |
| 种子数据 id | `data_{模型简称}_{序号}` | `data_category_rm` |

### 10.3 文件命名

| 类型 | 规则 | 示例 |
|------|------|------|
| Python 模型文件 | {模型名（下划线）}.py | `miclen_product_category.py` |
| 视图文件 | {模型名}_view.xml 或 {模型名}.xml | `stock_picking_type_view.xml` |
| 种子数据文件 | {模型名}_data.xml | `miclen_product_category_data.xml` |
| 安全文件 | ir.model.access.csv / ir_rule.xml | 固定名称 |
| JS 文件 | {功能名}.js | `mrp_display_record.js` |
| OWL 模板 | {组件名}.xml | `mrp_display_record.xml` |

### 10.4 自定义字段前缀

所有 Miclen 自定义字段统一使用 `miclen_` 前缀：

```python
miclen_category_id       # 大类
miclen_details_id        # 中类
miclen_subcategory_id    # 小类
miclen_width             # 宽幅
miclen_work_id           # 工序
```

**例外**：通用的 `manager_users`、`equipment_ids`、`printing_plate`、`die_mold` 不加前缀，因为它们是业务语义字段。

---

## 11. 业务逻辑模式

### 11.1 行级权限隔离模式

**目标**：让用户只能看到自己被分配的记录。

**实现步骤**：

1. 给目标模型添加 `manager_users` (Many2many → res.users) 字段
2. 在表单视图和列表视图中添加该字段（`widget="many2many_tags"`）
3. 在 `ir_rule.xml` 中配置两条规则：
   - 管理员：`[(1, '=', 1)]`
   - 普通用户：`[('manager_users', 'in', user.ids)]`
4. 在 `ir.model.access.csv` 中给所有用户基础权限

**已应用模型**：`stock.picking.type`、`quality.alert.team`、`mrp.workcenter`

### 11.2 合作伙伴过滤模式

**目标**：采购单只选公司型供应商，销售单只选公司型客户。

**实现方式**：通过视图层 xpath 修改 `partner_id` 的 domain：

```xml
<!-- 采购 -->
<attribute name="domain">[('is_company', '=', True), ('supplier_rank', '>', 0)]</attribute>

<!-- 销售 -->
<attribute name="domain">[('is_company', '=', True), ('customer_rank', '>', 0)]</attribute>
```

### 11.3 三级分类编码模式

**目标**：产品编码 = 大类-中类-小类-宽幅。

**实现方式**：

1. 三个独立模型存储分类编码（`miclen.product.category` / `miclen.category.details` / `miclen.category.subcategory`）
2. `product.template` 添加四个字段（三个 Many2one + 一个 Char）
3. `_compute_default_code` 方法拼接生成 `default_code`
4. 种子数据预置大类 (RM/PT/ASM/ASSY/BO)

### 11.4 工序配置链路模式

**目标**：工序配置表 → 路由工序 → BOM → 工单 → 看板全链路贯通。

**数据流**：

```
miclen.mrp.workcenter (工序配置表)
    ↓ 用户选择 miclen_work_id
mrp.routing.workcenter (路由工序) — _compute_miclen_fields 自动带出
    ↓ BOM 引用 operation_ids
mrp.bom (物料清单) — 内联可编辑列表
    ↓ 生成生产订单时创建
mrp.workorder (工单) — related 字段继承
    ↓ 看板展示
OWL 模板 + JS 异步加载设备名称
```

**关键技术点**：

1. `mrp.routing.workcenter` 的 `create()` 重写支持导入场景
2. `_compute_miclen_fields` 中 `readonly=False` 允许手动覆盖
3. `equipment_domain` 计算字段实现动态过滤
4. BOM 的 operation_ids 列表使用 `editable="bottom"` 内联编辑
5. 工单通过 `related` 字段自动继承路由工序的数据
6. 看板视图通过 OWL 模板注入隐藏 input，JS 通过 MutationObserver + JSON-RPC 异步加载设备名称

### 11.5 批量初始化模式

**目标**：系统部署后一键分配用户权限和作业类型管理用户。

**实现方式**：

1. `assign_users_to_work_type()` — 按作业类型编码 (IN/STOR/INT/OUT/PC/MO/SFP) 搜索并分配
2. `assign_user_permissions()` — 按 login 邮箱映射权限组列表

**调用方式**：通过 Odoo shell 或 server action 手动调用

---

## 12. 常见陷阱与避坑

### 12.1 `<tree>` vs `<list>`

**Odoo 19 中必须使用 `<list>`。** 如果使用 `<tree>`，视图会报错或不渲染。

### 12.2 `groups_id` vs `group_ids`

**Odoo 19 中 `res.users` 的权限组字段是 `group_ids`。** 使用 `groups_id` 会报错。

### 12.3 计算字段的 `readonly=False`

如果计算字段需要允许用户手动修改（如选择工序后自动带出但允许覆盖），必须设置 `readonly=False`。否则字段在 UI 上是只读的。

### 12.4 Many2many 清空操作

```python
# 正确：清空 Many2many
record.equipment_ids = [(5, 0, 0)]

# 错误：直接赋空列表
record.equipment_ids = []  # 可能不生效
```

### 12.5 `super()` 调用

覆盖父类方法时，如果父类有同名计算方法，必须先调用 `super()`：

```python
def _compute_default_code(self):
    super()._compute_default_code()  # 先执行父类逻辑
    for record in self:
        # 再执行自定义逻辑
```

### 12.6 `create()` 参数是列表

Odoo 19 的 `create()` 接收 `vals_list`（列表的列表），不是单个字典：

```python
def create(self, vals_list):
    for vals in vals_list:
        # 处理每个 vals
    return super().create(vals_list)
```

### 12.7 看板视图字段加载

看板视图中如果 JS 需要访问字段数据，必须在看板视图中声明该字段（即使 `invisible="1"`）。否则字段数据不会传到前端。

### 12.8 搜索视图强制加载字段

在搜索视图中声明字段（即使 `invisible="1"`）是强制将字段数据传到前端列表/看板视图的常用手段。

### 12.9 `noupdate` 的使用

- 种子数据和 ir.rule 使用 `noupdate="1"`
- 视图定义不使用 `noupdate`（允许升级时更新视图）

### 12.10 `optional` 属性

```xml
<field name="miclen_work_id" optional="show"/>  <!-- 默认显示 -->
<field name="miclen_work_id" optional="hide"/>  <!-- 默认隐藏 -->
```

在继承的列表视图中添加字段时，使用 `optional="show"` 确保默认可见。

### 12.11 `column_invisible` vs `invisible`

- `column_invisible="1"` — 在列表视图中隐藏该列，但字段数据仍然加载
- `invisible="1"` — 完全不可见，可能影响数据加载

当需要字段数据传到前端但不显示列时，使用 `column_invisible="1"`。

### 12.12 动态 domain 的 store

`equipment_domain` 计算字段需要 `store=True`，否则在列表视图中可能无法正确传递 domain 字符串。

---

## 13. 文件清单与职责

### 13.1 Python 模型文件

| 文件 | 模型 | 类型 | 职责 |
|------|------|------|------|
| `product_template.py` | `product.template` | _inherit | 添加分类字段 + 编码计算 + 批量初始化工具方法 |
| `stock_picking_type.py` | `stock.picking.type` | _inherit | 添加 manager_users 字段 |
| `quality_alert_team.py` | `quality.alert.team` | _inherit | 添加 manager_users 字段 |
| `mrp_workcenter.py` | `mrp.workcenter` | _inherit | 添加 manager_users 字段 |
| `purchase_order.py` | `purchase.order` | _inherit | 预留（当前无额外逻辑） |
| `miclen_product_category.py` | `miclen.product.category` | _name | 产品大类编码表 |
| `miclen_category_details.py` | `miclen.category.details` | _name | 产品中类编码表 |
| `miclen_category_subcategory.py` | `miclen.category.subcategory` | _name | 产品小类编码表 |
| `miclen_mrp_workcenter.py` | `miclen.mrp.workcenter` | _name | 工序配置表（核心） |
| `mrp_routing.py` | `mrp.routing.workcenter` | _inherit | 添加 miclen_work_id + 自动带出 + create 重写 |
| `mrp_production.py` | `mrp.production` | _inherit | 预留（当前无额外逻辑） |
| `mrp_workorder.py` | `mrp.workorder` | _inherit | related 字段继承工序信息 |

### 13.2 XML 视图文件

| 文件 | 职责 |
|------|------|
| `stock_picking_type_view.xml` | 作业类型表单/列表添加 manager_users |
| `quality_alert_team_view.xml` | 质量团队表单/列表添加 manager_users |
| `mrp_workcenter_view.xml` | 工作中心表单/列表添加 manager_users |
| `purchase_order_view.xml` | 采购单 partner_id domain 过滤 |
| `sale_order_view.xml` | 销售单 partner_id domain 过滤 |
| `miclen_product_category.xml` | 大类编码列表/表单视图 |
| `miclen_category_details.xml` | 中类编码列表/表单视图 |
| `miclen_category_subcategory.xml` | 小类编码列表/表单视图 |
| `product_template_views.xml` | 产品表单添加分类字段 |
| `miclen_mrp_workcenter.xml` | 工序配置表列表/表单视图 |
| `mrp_routing_views.xml` | 路由工序列表/表单/搜索继承 |
| `mrp_bom_views.xml` | BOM 作业页内联可编辑列表 |
| `mrp_production.xml` | 制造订单视图（当前为注释预留） |
| `mrp_workorder.xml` | 工单列表/看板/搜索继承 |
| `actions.xml` | 4 个 act_window 动作定义 |
| `menus.xml` | 4 个菜单项定义 |

### 13.3 Security 文件

| 文件 | 职责 |
|------|------|
| `ir.model.access.csv` | 4 个新模型的 CRUD 权限 |
| `ir_rule.xml` | 3 组 (6 条) ir.rule 行级权限规则 |

### 13.4 Data 文件

| 文件 | 职责 | 状态 |
|------|------|------|
| `miclen_product_category_data.xml` | 5 个大类种子数据 | 已启用 |
| `miclen_category_details_data.xml` | 中类种子数据 | 已注释 |
| `miclen_category_subcategory_data.xml` | 小类种子数据 | 已注释 |

### 13.5 前端文件

| 文件 | 职责 |
|------|------|
| `mrp_display_record.xml` | OWL 模板继承，在看板卡片中注入工序信息区域 |
| `mrp_display_record.js` | 原生 JS，MutationObserver + JSON-RPC 异步加载设备名称 |

---

## 附录 A: 新增继承模型快速模板

当需要给一个已有模型添加字段并做行级权限控制时，按以下步骤操作：

### A.1 Python 模型文件

```python
# -*- coding: utf-8 -*-

from odoo import fields, models


class TargetModel(models.Model):
    _inherit = 'target.model'
    _description = "目标模型增加管理用户"

    manager_users = fields.Many2many(
        'res.users',
        string='管理用户',
        help='选择哪些用户可以查看此记录'
    )
```

### A.2 视图文件

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_target_model_form_inherit" model="ir.ui.view">
        <field name="name">target.model.form.inherit</field>
        <field name="model">target.model</field>
        <field name="inherit_id" ref="target_module.target_model_form_view"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='some_field']" position="after">
                <field name="manager_users" widget="many2many_tags"
                       options="{'no_create': True, 'no_open': True}"/>
            </xpath>
        </field>
    </record>
</odoo>
```

### A.3 ir.rule

```xml
<data noupdate="1">
    <record id="miclen_target_model_rule_admin" model="ir.rule">
        <field name="name">目标模型 - 管理员全部可见</field>
        <field name="model_id" ref="target_module.model_target_model"/>
        <field name="domain_force">[(1, '=', 1)]</field>
        <field name="groups" eval="[(4, ref('base.group_system'))]"/>
        <field name="perm_read" eval="True"/>
        <field name="perm_write" eval="True"/>
        <field name="perm_create" eval="True"/>
        <field name="perm_unlink" eval="True"/>
    </record>

    <record id="miclen_target_model_rule_user" model="ir.rule">
        <field name="name">目标模型 - 按负责人限制</field>
        <field name="model_id" ref="target_module.model_target_model"/>
        <field name="domain_force">[('manager_users', 'in', user.ids)]</field>
        <field name="groups" eval="[(4, ref('base.group_user'))]"/>
        <field name="perm_read" eval="True"/>
        <field name="perm_write" eval="True"/>
        <field name="perm_create" eval="False"/>
        <field name="perm_unlink" eval="False"/>
    </record>
</data>
```

### A.4 注册

在 `__manifest__.py` 的 `data` 列表中按顺序添加视图和安全文件。

---

## 附录 B: 新增独立模型快速模板

### B.1 Python

```python
# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class MiclenNewModel(models.Model):
    _name = 'miclen.new.model'
    _description = "新模型描述"

    sequence = fields.Integer('序号', default=10)
    name = fields.Char('编码', tracking=True)
    note = fields.Char('备注', tracking=True)
```

### B.2 视图

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record model="ir.ui.view" id="miclen_new_model_list_view">
        <field name="name">miclen.new.model.list</field>
        <field name="model">miclen.new.model</field>
        <field name="arch" type="xml">
            <list string="新模型配置" editable="bottom">
                <field name="sequence" widget="handle"/>
                <field name="name" required="1"/>
                <field name="note"/>
            </list>
        </field>
    </record>

    <record model="ir.ui.view" id="miclen_new_model_form_view">
        <field name="name">miclen.new.model.form</field>
        <field name="model">miclen.new.model</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <group>
                            <field name="name" required="1"/>
                        </group>
                        <group>
                            <field name="note"/>
                        </group>
                    </group>
                </sheet>
            </form>
        </field>
    </record>
</odoo>
```

### B.3 权限

```csv
access_miclen_new_model,miclen.new.model,model_miclen_new_model,,1,1,1,1
```

### B.4 动作 + 菜单

```xml
<!-- actions.xml -->
<record model="ir.actions.act_window" id="action_miclen_new_model">
    <field name="name">新模型</field>
    <field name="res_model">miclen.new.model</field>
    <field name="view_mode">list,form</field>
</record>

<!-- menus.xml -->
<menuitem id="menu_action_miclen_new_model"
          name="新模型"
          parent="stock.menu_product_in_config_stock"
          sequence="230"
          action="action_miclen_new_model"/>
```

### B.5 __init__.py 注册

```python
# models/__init__.py
from . import miclen_new_model
```

---

## 附录 C: AI 生成代码检查清单

每次生成或修改代码后，AI 必须逐项检查：

- [ ] XML 列表视图使用 `<list>` 而非 `<tree>`
- [ ] `view_mode` 中使用 `list` 而非 `tree`
- [ ] `res.users` 的权限组字段使用 `group_ids` 而非 `groups_id`
- [ ] 从 `odoo.fields` 导入 `Command` 和 `Domain`
- [ ] 计算字段需要手动覆盖时设置了 `readonly=False`
- [ ] `create()` 重写使用 `vals_list` 参数
- [ ] Many2many 清空使用 `[(5, 0, 0)]`
- [ ] 新模型在 `ir.model.access.csv` 中声明了权限
- [ ] 行级权限模型配了两条 ir.rule（admin + user）
- [ ] 种子数据和 ir.rule 使用 `noupdate="1"`
- [ ] `__manifest__.py` 的 `data` 列表顺序正确
- [ ] 前端资源在 `assets` 中声明
- [ ] 自定义字段使用 `miclen_` 前缀
- [ ] 字段 `string` 使用中文
- [ ] Python 文件头有 `# -*- coding: utf-8 -*-`
- [ ] OWL 模板使用 `t-inherit` + `owl="1"`
- [ ] 看板视图需要 JS 访问的字段已在视图中声明

---

*本文件随项目迭代持续更新。如有疑问，以实际代码为准。*
