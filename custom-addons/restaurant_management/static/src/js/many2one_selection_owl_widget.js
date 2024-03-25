/** @odoo-module **/

import AbstractFieldOwl from "web.AbstractFieldOwl";
import fieldRegistryOwl from "web.field_registry_owl";

const { Component } = owl;
const { useState, onWillUpdateProps } = owl.hooks;

export default class SelectionOwl extends AbstractFieldOwl {
  constructor(...args) {
    super(...args);
  }

  setup() {
    super.setup();
    console.log("THIS: ", this);
  }

  async willUpdateProps(nextProps) {
    await super.willUpdateProps(nextProps);
    console.log("nextProps:", nextProps);
  }
}

SelectionOwl.template = "Many2oneSelectionOwl";
SelectionOwl.components = {};

fieldRegistryOwl.add("many2one_selection_owl", SelectionOwl);
