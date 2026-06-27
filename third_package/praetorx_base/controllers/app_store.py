# Copyright 2026 Lars Weiler
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

import logging

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

_logger = logging.getLogger(__name__)


class PraetorxAppStoreController(http.Controller):

    def _check_admin(self):
        if not request.env.user.has_group("base.group_system"):
            raise AccessError("Only administrators can access the App Store.")

    def _get_praetorx_category_ids(self):
        """Return IDs of PraetorX parent + child categories."""
        Category = request.env["ir.module.category"].sudo()
        praetorx_cat = Category.search(
            [("name", "=", "PraetorX"), ("parent_id", "=", False)], limit=1
        )
        if not praetorx_cat:
            return [], None
        child_cats = Category.search([("parent_id", "=", praetorx_cat.id)])
        return [praetorx_cat.id] + child_cats.ids, praetorx_cat

    def _get_praetorx_module(self, module_id):
        """Browse module and verify it belongs to a PraetorX category."""
        module = request.env["ir.module.module"].sudo().browse(module_id)
        if not module.exists():
            raise ValueError("Module not found")
        cat = module.category_id
        while cat:
            if cat.name == "PraetorX" and not cat.parent_id:
                return module
            cat = cat.parent_id
        raise AccessError("Module is not part of the PraetorX suite.")

    @http.route(
        "/praetorx/appstore/modules",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def get_modules(self):
        """Return PraetorX modules grouped by subcategory."""
        self._check_admin()
        Module = request.env["ir.module.module"].sudo()

        all_cat_ids, praetorx_cat = self._get_praetorx_category_ids()
        if not all_cat_ids:
            return []

        modules = Module.search([("category_id", "in", all_cat_ids)])

        # Batch-load uninstalled dependency names to avoid N+1
        all_dep_names = set()
        for mod in modules:
            if mod.state == "uninstalled":
                all_dep_names.update(mod.dependencies_id.mapped("name"))
        uninstalled_deps = {}
        if all_dep_names:
            dep_mods = Module.search([
                ("name", "in", list(all_dep_names)),
                ("state", "=", "uninstalled"),
            ])
            for dm in dep_mods:
                uninstalled_deps[dm.name] = dm.shortdesc or dm.name

        result = []
        for mod in modules:
            deps = []
            if mod.state == "uninstalled":
                for dep in mod.dependencies_id:
                    if dep.name in uninstalled_deps:
                        deps.append(uninstalled_deps[dep.name])

            cat_name = mod.category_id.name
            if mod.category_id == praetorx_cat:
                cat_name = "Core"

            result.append({
                "id": mod.id,
                "name": mod.name,
                "shortdesc": mod.shortdesc or mod.name,
                "summary": mod.summary or "",
                "version": mod.installed_version or mod.latest_version or "",
                "state": mod.state,
                "icon": mod.icon or "/base/static/description/icon.png",
                "category": cat_name,
                "dependencies": deps,
            })

        return result

    @http.route(
        "/praetorx/appstore/install",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def install_module(self, module_id):
        """Install a PraetorX module."""
        self._check_admin()
        module = self._get_praetorx_module(module_id)
        module.button_immediate_install()
        return {"success": True}

    @http.route(
        "/praetorx/appstore/uninstall",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def uninstall_module(self, module_id):
        """Uninstall a PraetorX module."""
        self._check_admin()
        module = self._get_praetorx_module(module_id)
        module.button_immediate_uninstall()
        return {"success": True}
