/** @odoo-module **/

import AbstractFieldOwl from "web.AbstractFieldOwl";
import fieldRegistryOwl from "web.field_registry_owl";

const { useState, onWillUpdateProps, onMounted, useRef } = owl.hooks;

export default class TopViolationsList extends AbstractFieldOwl {
  constructor(...args) {
    super(...args);
  }

  setup() {
    super.setup();

    this.state = useState({
      fieldValue: JSON.parse(this.value),
    });
    onWillUpdateProps(async (nextProps) => {
      this.state.fieldValue = JSON.parse(this.value);
    });

    onMounted(() => {});
  }
}

TopViolationsList.template = "TopViolationsList";
TopViolationsList.components = {};

fieldRegistryOwl.add("top_violations_list_widget", TopViolationsList);
