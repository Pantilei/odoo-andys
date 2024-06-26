/** @odoo-module **/

import AbstractFieldOwl from "web.AbstractFieldOwl";
import fieldRegistryOwl from "web.field_registry_owl";
import { Markup } from "web.utils";

const { useState, onWillUpdateProps, onMounted, useRef } = owl.hooks;

export default class JsonToTopFaults extends AbstractFieldOwl {
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

JsonToTopFaults.template = "JsonToTopFaults";
JsonToTopFaults.components = {};

fieldRegistryOwl.add("json_to_top_faults", JsonToTopFaults);
