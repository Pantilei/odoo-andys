/** @odoo-module **/

import AbstractFieldOwl from "web.AbstractFieldOwl";
import fieldRegistryOwl from "web.field_registry_owl";

const { useState, onWillUpdateProps, onMounted, useRef } = owl.hooks;

export default class JsonToPieChart extends AbstractFieldOwl {
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
      responsive: true,
      maintainAspectRatio: false,
      zoomOutPercentage: 0, // makes chart 40% smaller (50% by default, if the preoprty is undefined)
      layout: {
        padding: 160,
      },
      plugins: {
        legend: false,
        outlabels: {
          text: "%l: %v(%p)",
          color: "white",
          stretch: 15,
          font: {
            resizable: true,
            minSize: 10,
            maxSize: 12,
          },
        },
      },
    };
    let configs = {
      ...chartConfigs,
      options,
    };
    this.chart = new Chart(this.graphCanvasRef.el, configs);
    this.chart.resize();
  }
}

JsonToPieChart.template = "JsonToPieChart";
JsonToPieChart.components = {};

fieldRegistryOwl.add("json_to_pie_chart", JsonToPieChart);
