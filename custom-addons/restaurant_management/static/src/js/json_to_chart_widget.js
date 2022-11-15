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
    let options = {
      ...chartConfigs.options,
      plugins: {
        datalabels: {
          align: function (context) {
            var index = context.dataIndex;
            var datasets = context.chart.data.datasets;
            var v0 = datasets[0].data[index];
            var v1 = datasets[1].data[index];
            var invert = v0 - v1 > 0;
            return context.datasetIndex === 0
              ? invert
                ? "end"
                : "start"
              : invert
              ? "start"
              : "end";
          },
          backgroundColor: function (context) {
            return context.dataset.labelBackgroundColor;
          },
          borderRadius: 3,
          color: function (context) {
            return context.dataset.labelColor;
          },
          font: {
            weight: "bold",
          },
          offset: 4,
          padding: 2,
          // formatter: Math.round,
        },
      },
    };
    let configs = {
      ...chartConfigs,
      plugins: [ChartDataLabels],
      options,
    };
    this.chart = new Chart(this.graphCanvasRef.el, configs);
  }
}

JsonToChart.template = "JsonToChart";
JsonToChart.components = {};

fieldRegistryOwl.add("json_to_chart", JsonToChart);
