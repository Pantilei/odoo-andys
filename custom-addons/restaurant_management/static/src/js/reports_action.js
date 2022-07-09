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
      reportType: "audits_per_month_table",

      currentYear: moment().year(),

      checkListCategories: [],
      currentCheckListCategory: "all",

      restaurantNetworks: [],
      currentRestaurantNetwork: "all",

      restaurants: [],
      currentRestaurant: "all",

      faultCountPerMonth: [],
      faultCountPerMonthPerAudit: [],

      auditCountsPerMonth: {
        actual: [],
        planned: [],
      },

      restaurantRating: [],
      relativeRestaurantRating: [],
    });

    onWillStart(async () => {
      await this._getCheckListCategory();
      await this._getRestaurantNetworks();
      await this._getRestaurants();
      await this._getAuditCountsPerMonth();
    });

    onMounted(() => {
      console.log("THIS:", this);
    });

    onWillUnmount(() => {
      if (this.chart) {
        this.chart.destroy();
      }
    });
  }

  _getOptionYears() {
    return Array.from(Array(20)).map((_, index) => moment().year() - index);
  }

  async _getAuditCountsPerMonth() {
    let res = await this.env.services.rpc({
      model: "restaurant_management.restaurant_audit",
      method: "get_audit_counts_per_month",
      args: [parseInt(this.state.currentYear)],
      kwargs: {
        restaurant_id:
          this.state.currentRestaurant === "all"
            ? null
            : parseInt(this.state.currentRestaurant),
        restaurant_network_id:
          this.state.currentRestaurantNetwork === "all"
            ? null
            : parseInt(this.state.currentRestaurantNetwork),
      },
    });
    Object.assign(this.state.auditCountsPerMonth, res);
  }

  async _getRestaurants() {
    let res = await this.env.services.rpc({
      model: "restaurant_management.restaurant",
      method: "search_read",
      kwargs: {
        domain: [],
        fields: ["id", "name", "restaurant_network_id"],
      },
    });
    this.state.restaurants = res;
  }

  async _getRestaurantNetworks() {
    let res = await this.env.services.rpc({
      model: "restaurant_management.restaurant_network",
      method: "search_read",
      kwargs: {
        domain: [],
        fields: ["id", "name"],
      },
    });
    this.state.restaurantNetworks = res;
  }

  async _getCheckListCategory() {
    let res = await this.env.services.rpc({
      model: "restaurant_management.check_list_category",
      method: "search_read",
      kwargs: {
        domain: [],
        fields: ["id", "display_name"],
      },
    });
    this.state.checkListCategories = res;
  }

  async _getRestaurantRatingData() {
    let res = await this.env.services.rpc({
      model: "restaurant_management.fault_registry",
      method: "get_restaurant_rating_data",
      args: [parseInt(this.state.currentYear)],
    });
    this.state.restaurantRating.splice(
      0,
      this.state.restaurantRating.length,
      ...res
    );
  }

  async _getRelativeRestaurantRatingData() {
    let res = await this.env.services.rpc({
      model: "restaurant_management.fault_registry",
      method: "get_restaurant_rating_per_audit_data",
      args: [parseInt(this.state.currentYear)],
    });
    this.state.relativeRestaurantRating.splice(
      0,
      this.state.relativeRestaurantRating.length,
      ...res
    );
  }

  async _onReportTypeChange(ev) {
    let destroyChart = true;
    this.state.reportType = ev.target.value;
    switch (this.state.reportType) {
      case "dynamics_of_faults_per_month_graph":
        await this._getChartData();
        this._renderChart();
        destroyChart = false;
        break;
      case "audits_per_month_table":
        await this._getAuditCountsPerMonth();
        break;
      case "restaurant_rating":
        await this._getRestaurantRatingData();
        break;
      case "relative_restaurant_rating":
        await this._getRelativeRestaurantRatingData();
    }

    if (this.chart && destroyChart) {
      this.chart.destroy();
    }
  }

  async _onCategoryChange(ev) {
    this.state.currentCheckListCategory = ev.target.value;
    if (this.state.reportType === "dynamics_of_faults_per_month_graph") {
      await this._getChartData();
      this._renderChart();
    }
  }

  async _onRestaurantNetworkChange(ev) {
    this.state.currentRestaurantNetwork = ev.target.value;
    this.state.currentRestaurant = "all";
    if (this.state.reportType === "audits_per_month_table") {
      await this._getAuditCountsPerMonth();
    }
    if (this.state.reportType === "dynamics_of_faults_per_month_graph") {
      await this._getChartData();
      this._renderChart();
    }
  }

  async _onRestaurantChange(ev) {
    this.state.currentRestaurant = ev.target.value;
    this.state.currentRestaurantNetwork = "all";
    if (this.state.reportType === "audits_per_month_table") {
      await this._getAuditCountsPerMonth();
    }
    if (this.state.reportType === "dynamics_of_faults_per_month_graph") {
      await this._getChartData();
      this._renderChart();
    }
  }

  async _onYearChange(ev) {
    this.state.currentYear = ev.target.value;
    switch (this.state.reportType) {
      case "audits_per_month_table":
        await this._getAuditCountsPerMonth();
        break;
      case "dynamics_of_faults_per_month_graph":
        await this._getChartData();
        this._renderChart();
        break;
      case "restaurant_rating":
        await this._getRestaurantRatingData();
        break;
      case "relative_restaurant_rating":
        await this._getRelativeRestaurantRatingData();
        break;
    }
  }

  async _getChartData() {
    let counts = await this.env.services.rpc({
      model: "restaurant_management.fault_registry",
      method: "get_fault_counts_per_month",
      args: [parseInt(this.state.currentYear)],
      kwargs: {
        check_list_category_id:
          this.state.currentCheckListCategory === "all"
            ? null
            : parseInt(this.state.currentCheckListCategory),
        restaurant_id:
          this.state.currentRestaurant === "all"
            ? null
            : parseInt(this.state.currentRestaurant),
        restaurant_network_id:
          this.state.currentRestaurantNetwork === "all"
            ? null
            : parseInt(this.state.currentRestaurantNetwork),
      },
    });
    this.state.faultCountPerMonth = counts.fault_counts;
    this.state.faultCountPerMonthPerAudit = counts.fault_per_audit;

    return counts;
  }

  _renderChart() {
    if (this.chart) {
      this.chart.destroy();
    }
    this.chart = new Chart(this.graphCanvasRef.el, this._getChartConfig());
  }

  _getChartConfig() {
    const data = {
      labels: this.months,
      datasets: [
        {
          label: "Количество Ошибок",
          data: this.state.faultCountPerMonth,
          borderColor: "rgb(255, 99, 132)",
          backgroundColor: "rgb(255, 99, 132, 0.5)",
          yAxisID: "y1",
        },
        {
          label: "Количество Ошибок на Единицу Проверки",
          data: this.state.faultCountPerMonthPerAudit,
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
        maintainAspectRatio: false,
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
              ticks: {
                min: 0, // minimum value
              },
            },
            {
              id: "y2",
              type: "linear",
              display: true,
              position: "right",
              ticks: {
                min: 0, // minimum value
              },

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

  getMonths() {
    let monthObj = moment().localeData().months();
    if (Array.isArray(monthObj)) {
      return monthObj.map((r) => r.toUpperCase());
    }
    return monthObj.standalone.map((r) => r.toUpperCase());
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
