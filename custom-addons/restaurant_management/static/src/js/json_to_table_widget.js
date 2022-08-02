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
    console.log("THIS: ", this);

    this.topFaultsWithComments = JSON.parse(this.value);
    this.Markup = Markup;
    onWillUpdateProps(async (nextProps) => {});

    onMounted(() => {});
  }
}

JsonToTopFaults.template = "JsonToTopFaults";
JsonToTopFaults.components = {};

fieldRegistryOwl.add("json_to_top_faults", JsonToTopFaults);
