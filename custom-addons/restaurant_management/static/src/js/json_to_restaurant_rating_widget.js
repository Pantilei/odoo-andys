/** @odoo-module **/

import AbstractFieldOwl from "web.AbstractFieldOwl";
import fieldRegistryOwl from "web.field_registry_owl";

const { useState, onWillUpdateProps, onMounted, useRef } = owl.hooks;

export default class JsonToRestaurantRating extends AbstractFieldOwl {
  constructor(...args) {
    super(...args);
  }

  setup() {
    super.setup();
    const value = JSON.parse(this.value);
    this.state = useState({
      fieldValue: value,
      mediumIndex: Math.round(
        value["grouped_restaurant_rating_per_audit"].length / 2
      ),
      highlightRestaurantId: value.restaurant_id || false,
    });

    this.topFaultsWithComments = JSON.parse(this.value);
    onWillUpdateProps(async (nextProps) => {
      const value = JSON.parse(this.value);
      this.state.fieldValue = value;
      this.state.mediumIndex = Math.round(
        value["grouped_restaurant_rating_per_audit"].length / 2
      );
      this.state.highlightRestaurantId = value.restaurant_id || false;
    });

    onMounted(() => {});
  }
}

JsonToRestaurantRating.template = "JsonToRestaurantRating";
JsonToRestaurantRating.components = {};

fieldRegistryOwl.add("json_to_restaurant_rating", JsonToRestaurantRating);
