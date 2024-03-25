/** @odoo-module **/

import ListRenderer from "web.ListRenderer";
import core from "web.core";

var _t = core._t;

ListRenderer.include({
  _renderGroupRow: function (group, groupLevel) {
    var cells = [];

    const groupBy = this.state.groupedBy[groupLevel];
    const groupByFieldName = groupBy.split(":")[0];
    const groupByField = group.fields[groupByFieldName];
    const name =
      groupByField.type === "boolean"
        ? group.value === undefined
          ? _t("Undefined")
          : group.value
        : group.value === undefined || group.value === false
        ? _t("Undefined")
        : group.value;
    let textValue = name + " (" + group.count + ")";
    if (this.state.context.hide_grouped_count) {
      textValue = name;
    }
    var $th = $("<th>")
      .addClass("o_group_name")
      .attr("tabindex", -1)
      .text(textValue);
    var $arrow = $("<span>")
      .css("padding-left", 2 + groupLevel * 20 + "px")
      .css("padding-right", "5px")
      .addClass("fa");
    if (group.count > 0) {
      $arrow
        .toggleClass("fa-caret-right", !group.isOpen)
        .toggleClass("fa-caret-down", group.isOpen);
    }
    $th.prepend($arrow);
    cells.push($th);

    var aggregateKeys = Object.keys(group.aggregateValues);
    var aggregateValues = _.mapObject(group.aggregateValues, function (value) {
      return { value: value };
    });
    var aggregateCells = this._renderAggregateCells(aggregateValues);
    var firstAggregateIndex = _.findIndex(this.columns, function (column) {
      return (
        column.tag === "field" && _.contains(aggregateKeys, column.attrs.name)
      );
    });
    var colspanBeforeAggregate;
    if (firstAggregateIndex !== -1) {
      // if there are aggregates, the first $th goes until the first
      // aggregate then all cells between aggregates are rendered
      colspanBeforeAggregate = firstAggregateIndex;
      var lastAggregateIndex = _.findLastIndex(this.columns, function (column) {
        return (
          column.tag === "field" && _.contains(aggregateKeys, column.attrs.name)
        );
      });
      cells = cells.concat(
        aggregateCells.slice(firstAggregateIndex, lastAggregateIndex + 1)
      );
      var colSpan = this.columns.length - 1 - lastAggregateIndex;
      if (colSpan > 0) {
        cells.push($("<th>").attr("colspan", colSpan));
      }
    } else {
      var colN = this.columns.length;
      colspanBeforeAggregate = colN > 1 ? colN - 1 : 1;
      if (colN > 1) {
        cells.push($("<th>"));
      }
    }
    if (this.hasSelectors) {
      colspanBeforeAggregate += 1;
    }
    $th.attr("colspan", colspanBeforeAggregate);

    if (
      group.isOpen &&
      !group.groupedBy.length &&
      group.count > group.data.length
    ) {
      const lastCell = cells[cells.length - 1][0];
      this._renderGroupPager(group, lastCell);
    }
    if (group.isOpen && this.groupbys[groupBy]) {
      var $buttons = this._renderGroupButtons(group, this.groupbys[groupBy]);
      if ($buttons.length) {
        var $buttonSection = $("<div>", {
          class: "o_group_buttons",
        }).append($buttons);
        $th.append($buttonSection);
      }
    }
    return $("<tr>")
      .addClass("o_group_header")
      .toggleClass("o_group_open", group.isOpen)
      .toggleClass("o_group_has_content", group.count > 0)
      .data("group", group)
      .append(cells);
  },
});
