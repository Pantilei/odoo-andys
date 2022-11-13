/** @odoo-module **/

import AbstractFieldOwl from "web.AbstractFieldOwl";
import fieldRegistryOwl from "web.field_registry_owl";

const { useState, onWillUpdateProps, onMounted, useRef } = owl.hooks;

export default class JsonAuditReports extends AbstractFieldOwl {
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

JsonAuditReports.template = "JsonAuditReports";
JsonAuditReports.components = {};

fieldRegistryOwl.add("json_to_audit_tables", JsonAuditReports);
