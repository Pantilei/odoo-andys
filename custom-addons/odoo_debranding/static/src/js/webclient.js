/** @odoo-module **/

import { useBus, useEffect, useService } from "@web/core/utils/hooks";
import { useTooltip } from "@web/core/tooltip/tooltip_hook";
import { useOwnDebugContext } from "@web/core/debug/debug_context";
import { registry } from "@web/core/registry";
import { DebugMenu } from "@web/core/debug/debug_menu";
import { localization } from "@web/core/l10n/localization";

const { Component, hooks } = owl;
const { useExternalListener } = hooks;
import { patch } from "@web/core/utils/patch";
import { WebClient } from "@web/webclient/webclient";

patch(WebClient.prototype, "remove branding title", {
  setup() {
    this.menuService = useService("menu");
    this.actionService = useService("action");
    this.title = useService("title");
    this.router = useService("router");
    this.user = useService("user");
    useService("legacy_service_provider");
    useOwnDebugContext({ categories: ["default"] });
    if (this.env.debug) {
      registry.category("systray").add(
        "web.debug_mode_menu",
        {
          Component: DebugMenu,
        },
        { sequence: 100 }
      );
    }
    this.localization = localization;
    // Remove title including 'Odoo'!
    // this.title.setParts({ zopenerp: "Odoo" }); // zopenerp is easy to grep
    useBus(this.env.bus, "ROUTE_CHANGE", this.loadRouterState);
    useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", (mode) => {
      if (mode !== "new") {
        this.el.classList.toggle("o_fullscreen", mode === "fullscreen");
      }
    });
    useEffect(
      () => {
        this.loadRouterState();
      },
      () => []
    );
    useExternalListener(window, "click", this.onGlobalClick, { capture: true });
    useTooltip();
  },
});
