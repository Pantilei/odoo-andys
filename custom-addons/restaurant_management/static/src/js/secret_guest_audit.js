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
    selector: ".o_forms_main",
    events: {
      "click .o_submit_button": "_onSubmit",
      "change .js_check_list": "_onCheckListCheck",
      "change .js_check_list_with_note": "_onCheckListCheckWithNote",
      // "submit .user_form,.check_list_form": "_onSubmitValidate"
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

    _onCheckListCheck: function (event) {
      if (event.target.value === "no") {
        $(event.target).parent().parent().next().removeClass("d-none");
      } else {
        $(event.target).parent().parent().next().addClass("d-none");
      }
    },

    _onCheckListCheckWithNote: function (event) {
      console.log(event.target.value);
    },

    _onSubmit: function (event) {
      let forms = this.$el.find(".form_with_validation");
      [...forms].forEach((form) => {
        if (form.checkValidity() === false) {
          event.preventDefault();
          event.stopPropagation();
          // $(this).submit();
        }
        $(form).addClass("was-validated");
      });
      // if (this.$form.valid()) {
      //   var formData = new FormData(this.$form[0]);
      //   let dataToSend = {};
      //   formData.forEach(function (value, key) {
      //     dataToSend[key] = value;
      //   });

      //   return this._rpc({
      //     route: window.location.pathname + "/handle",
      //     params: dataToSend,
      //   }).then((r) => {
      //     if (r.success) {
      //       window.location.href =
      //         window.location.pathname + `/thank-you?lang=${lang}`;
      //     } else {
      //       console.log(r.message);
      //     }
      //   });
      // }
    },
  });

  return publicWidget.registry.SecretGuestAudit;
});
