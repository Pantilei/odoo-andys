/** @odoo-module **/

import core from "web.core";
import AbstractAction from "web.AbstractAction";
import Dialog from "web.Dialog";
import rpc from "web.rpc";
import { _lt } from "@web/core/l10n/translation";
import { ComponentWrapper, WidgetAdapterMixin } from "web.OwlCompatibility";

const MONTHS_NUM = Array.from(Array(12).keys());
const MONTHS = [
  "ЯНВ",
  "ФЕВ",
  "МАРТ",
  "АПР",
  "МАЙ",
  "ИЮНЬ",
  "ИЮЛЬ",
  "АВГ",
  "СЕН",
  "ОКТ",
  "НОЯБРЬ",
  "ДЕК",
];

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
    this.months = MONTHS;
    this.state = useState({
      report_type: "audits_per_month_table",
      report_data: {},
    });

    onWillStart(async () => {
      await this._updateReportData();
    });

    onMounted(() => {});
    console.log("THIS:", this);
  }

  async _updateReportData() {
    let data = await this.env.services.rpc({
      model: "restaurant_management.fault_registry",
      method: "get_report_data",
      args: [this.state.report_type],
    });

    Object.assign(this.state.report_data, data);

    return data;
  }

  _onReportTypeChange(ev) {
    console.log(ev.target.value);
    console.log(this.state);
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
