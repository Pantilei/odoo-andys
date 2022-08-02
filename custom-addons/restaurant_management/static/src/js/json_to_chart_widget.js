/** @odoo-module **/

import AbstractFieldOwl from "web.AbstractFieldOwl";
import fieldRegistryOwl from "web.field_registry_owl";

const { useState, onWillUpdateProps, onMounted, useRef } = owl.hooks;

export default class JsonToChart extends AbstractFieldOwl {
  constructor(...args) {
    super(...args);
  }

  setup() {
    super.setup();
    console.log("THIS: ", this);
    this.chart = null;

    this.graphCanvasRef = useRef("graphCanvasRef");

    onWillUpdateProps(async (nextProps) => {
      this._renderChart();
    });

    onMounted(() => {
      this._renderChart();
    });
  }

  _renderChart() {
    if (this.chart) {
      this.chart.destroy();
    }
    let chartConfigs = JSON.parse(this.value);
    this.chart = new Chart(this.graphCanvasRef.el, chartConfigs);
  }
}

JsonToChart.template = "JsonToChart";
JsonToChart.components = {};

fieldRegistryOwl.add("json_to_chart", JsonToChart);
