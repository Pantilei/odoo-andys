/** @odoo-module **/

import { registry } from "@web/core/registry";

import { patch } from "@web/core/utils/patch";
import { UserMenu } from "@web/webclient/user_menu/user_menu";

const userMenuRegistry = registry.category("user_menuitems");

patch(UserMenu.prototype, "remove branding menus", {
  getElements() {
    const sortedItems = userMenuRegistry
      .getAll()
      .filter(
        (r) =>
          ["documentationItem", "supportItem", "odooAccountItem"].indexOf(
            r.name
          ) === -1
      )
      .map((element) => element(this.env))
      .sort((x, y) => {
        const xSeq = x.sequence ? x.sequence : 100;
        const ySeq = y.sequence ? y.sequence : 100;
        return xSeq - ySeq;
      });
    return sortedItems;
  },
});
