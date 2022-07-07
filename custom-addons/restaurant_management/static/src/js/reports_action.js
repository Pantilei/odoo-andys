/** @odoo-module **/

import core from "web.core";
import AbstractAction from "web.AbstractAction";
import { _lt } from "@web/core/l10n/translation";
import { ComponentWrapper, WidgetAdapterMixin } from "web.OwlCompatibility";

const MONTHS_NUM = Array.from(Array(12).keys());

const { Component } = owl;
const {
  useRef,
  useState,
  onMounted,
  onWillStart,
  onWillUpdateProps,
  onWillUnmount,
} = owl.hooks;

class ReportsAppComponent extends Component {
  constructor(componentWrapper, props) {
    super(...arguments);
    this.parent = componentWrapper.parentWidget;
    this.context = componentWrapper.parentWidget.searchModelConfig.context;
  }

  setup() {
    this.months = this.getMonths();
    this.graphCanvasRef = useRef("graphCanvasRef");
    this.chart = null;

    this.state = useState({
      report_type: "audits_per_month_table",
      countPerMonthY1: [],
      countPerMonthY2: [1, 34, 56, 66, 11, 55, 34, 12, 67, 89, 23, 56],
    });

    onWillStart(async () => {
      await this._updateReportData();
    });

    onMounted(() => {
      console.log("moment:", this.getMonths());
      console.log("THIS:", this);
    });
  }

  async _updateReportData() {
    let counts = await this.env.services.rpc({
      model: "restaurant_management.fault_registry",
      method: "get_audit_fault_counts_per_month",
      args: [this.state.report_type],
    });
    this.state.countPerMonthY1.splice(0, this.state.countPerMonthY1.length);
    this.state.countPerMonthY1.push(...counts.audit_counts);

    return counts;
  }

  _onReportTypeChange(ev) {
    console.log(ev.target.value);
    console.log(this.state);
    if (this.state.report_type === "dynamics_of_audits_per_month_graph") {
      this._renderChart();
    } else {
      this.chart.destroy();
    }
  }

  getMonths() {
    let monthObj = moment().localeData().months();
    if (Array.isArray(monthObj)) {
      return monthObj.map((r) => r.toUpperCase());
    }
    return monthObj.standalone.map((r) => r.toUpperCase());
  }

  _getChartConfig() {
    console.log(this.months);
    console.log(this.state.countPerMonthY1);
    console.log(this.state.countPerMonthY2);
    const data = {
      labels: this.months,
      datasets: [
        {
          label: "Фактическое",
          data: this.state.countPerMonthY1,
          borderColor: "rgb(255, 99, 132)",
          backgroundColor: "rgb(255, 99, 132, 0.5)",
          yAxisID: "y1",
        },
        {
          label: "Плановое",
          data: this.state.countPerMonthY2,
          borderColor: "rgb(54, 162, 235)",
          backgroundColor: "rgb(54, 162, 235, 0.5)",
          yAxisID: "y2",
        },
      ],
    };
    return {
      type: "line",
      data,
      options: {
        responsive: true,
        interaction: {
          mode: "index",
          intersect: false,
        },
        stacked: false,
        plugins: {
          title: {
            display: true,
            text: "Chart.js Line Chart - Multi Axis",
          },
        },
        scales: {
          yAxes: [
            {
              id: "y1",
              type: "linear",
              display: true,
              position: "left",
            },
            {
              id: "y2",
              type: "linear",
              display: true,
              position: "right",

              // grid line settings
              grid: {
                drawOnChartArea: false, // only want the grid lines for one axis to show up
              },
            },
          ],
        },
      },
    };
  }

  _renderChart() {
    if (this.chart) {
      this.chart.destroy();
    }
    this.chart = new Chart(this.graphCanvasRef.el, this._getChartConfig());
  }
}

ReportsAppComponent.template = "ReportsAppMain";
ReportsAppComponent.components = {};

const ReportsAction = AbstractAction.extend(WidgetAdapterMixin, {
  start() {
    const Component = new ComponentWrapper(this, ReportsAppComponent);
    return Component.mount(this.el.querySelector(".o_content"));
  },
});

//Add the custom defined widget to registry.
core.action_registry.add("reports_action", ReportsAction);

export default ReportsAction;
