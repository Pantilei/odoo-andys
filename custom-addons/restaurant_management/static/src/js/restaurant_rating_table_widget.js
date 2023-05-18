/** @odoo-module **/

import AbstractFieldOwl from "web.AbstractFieldOwl";
import fieldRegistryOwl from "web.field_registry_owl";

const { useState, onWillUpdateProps, onMounted, useRef } = owl.hooks;

export default class RestaurantRatingTable extends AbstractFieldOwl {
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

RestaurantRatingTable.template = "RestaurantRatingTable";
RestaurantRatingTable.components = {};

fieldRegistryOwl.add("restaurant_rating_table_widget", RestaurantRatingTable);
