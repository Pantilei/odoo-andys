/** @odoo-module **/

import AbstractFieldOwl from "web.AbstractFieldOwl";
import fieldRegistryOwl from "web.field_registry_owl";
import { Markup } from "web.utils";

const { useState, onWillUpdateProps, onMounted, useRef } = owl.hooks;

export default class JsonToRestaurantRating extends AbstractFieldOwl {
  constructor(...args) {
    super(...args);
  }

  setup() {
    super.setup();
    console.log("THIS: ", this);

    this.state = useState({
      fieldValue: JSON.parse(this.value),
    });

    this.topFaultsWithComments = JSON.parse(this.value);
    this.Markup = Markup;
    onWillUpdateProps(async (nextProps) => {
      this.state.fieldValue = JSON.parse(this.value);
    });

    onMounted(() => {});
  }
}

JsonToRestaurantRating.template = "JsonToRestaurantRating";
JsonToRestaurantRating.components = {};

fieldRegistryOwl.add("json_to_restaurant_rating", JsonToRestaurantRating);
