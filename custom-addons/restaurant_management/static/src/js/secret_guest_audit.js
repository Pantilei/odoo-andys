odoo.define("restaurant_management.secret_guest_audit", function (require) {
  "use strict";

  var publicWidget = require("web.public.widget");
  var time = require("web.time");
  var core = require("web.core");
  var Dialog = require("web.Dialog");
  var dom = require("web.dom");
  var utils = require("web.utils");

  var _t = core._t;

  
  publicWidget.registry.SecretGuestAudit = publicWidget.Widget.extend({
    selector: ".o_form_main",
    events: {
      // "click .o_submit_button": "_onSubmit",
    },
    custom_events: {},

    //--------------------------------------------------------------------------
    // Widget
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    start: function () {
      var self = this;
      return this._super.apply(this, arguments).then(function () {
        // self.$form = self.$("#review_form");
        // const queryParams = self._getQueryParams();
        // const lang = queryParams.lang;

        // self.$form.validate({
        //   // Specify validation rules
        //   rules: {
        //     name: "required",
        //     phone: "required",
        //     email_from: {
        //       required: false,
        //       email: true,
        //     },
        //     description: {
        //       required: true,
        //       minlength: 5,
        //     },
        //   },
        //   // Specify validation error messages
        //   messages: self._validationMessagesTranslations(lang),
        // });
      });
    },

    // -------------------------------------------------------------------------
    // Private
    // -------------------------------------------------------------------------

    _getQueryParams: function () {
      const params = new Proxy(new URLSearchParams(window.location.search), {
        get: (searchParams, prop) => searchParams.get(prop),
      });
      return params;
    },

    // Handlers
    // -------------------------------------------------------------------------

    _onSubmit: function (event) {
      event.preventDefault();
      const queryParams = this._getQueryParams();
      const lang = queryParams.lang;
      if (this.$form.valid()) {
        var formData = new FormData(this.$form[0]);
        let dataToSend = {};
        formData.forEach(function (value, key) {
          dataToSend[key] = value;
        });

        return this._rpc({
          route: window.location.pathname + "/handle",
          params: dataToSend,
        }).then((r) => {
          if (r.success) {
            window.location.href =
              window.location.pathname + `/thank-you?lang=${lang}`;
          } else {
            console.log(r.message);
          }
        });
      }
    },
  });

  return publicWidget.registry.SecretGuestAudit;
});
