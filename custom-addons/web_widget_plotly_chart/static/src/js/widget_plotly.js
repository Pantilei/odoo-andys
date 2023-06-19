/** @odoo-module **/

import AbstractFieldOwl from "web.AbstractFieldOwl";
import fieldRegistryOwl from "web.field_registry_owl";

const { useState, onWillUpdateProps, onMounted, useRef } = owl.hooks;

export default class PlotlyChartWidget extends AbstractFieldOwl {
  constructor(...args) {
    super(...args);
  }

  setup() {
    super.setup();

    this.state = useState({
      fieldValue: this.value || "",
    });

    onWillUpdateProps(async (nextProps) => {
      this.state.fieldValue = this.value || "";
    });

    onMounted(() => {});
  }
}

PlotlyChartWidget.template = "PlotlyChart";
PlotlyChartWidget.components = {};

fieldRegistryOwl.add("plotly_chart", PlotlyChartWidget);
