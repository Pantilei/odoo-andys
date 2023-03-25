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
        FilePond.registerPlugin(
          FilePondPluginImagePreview,
          FilePondPluginFileValidateSize,
          FilePondPluginFileValidateType
        );
        self.ponds = [...document.querySelectorAll(".file_upload_input")].map(
          function (element) {
            let access_token = window.location.pathname.replace("/audits/", "");
            return FilePond.create(element, {
              server: {
                process: `/audits/${access_token}/file-upload`,
                revert: `/audits/${access_token}/file-remove`,
              },
              allowMultiple: true,
              allowFileEncode: true,
              required: true,
              labelIdle: _(
                `Load files. <span class="filepond--label-action">Browse</span>.`
              ),
              maxFileSize: "100MB",
              labelMaxFileSizeExceeded: _t("File is too large"),
              labelMaxFileSize: _t(`Maximum file size is 100MB`),
              acceptedFileTypes: ["image/png", "image/jpeg", "video/mp4"],
            });
          }
        );
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
      let comment_section = $(event.target).parent().parent().next();
      console.log("comment_section: ", comment_section);
      if (comment_section.hasClass("comment_optional")) {
        if (["no", "1", "2", "3", "4"].includes(event.target.value)) {
          comment_section.removeClass("d-none");
          comment_section.find("textarea").attr({ required: true });
        } else {
          comment_section.find("textarea").removeAttr("required");
          comment_section.addClass("d-none");
        }
      }
    },

    _onSubmit: function (event) {
      event.preventDefault();
      event.stopPropagation();

      let forms = this.$el.find(".form_with_validation");
      let are_valid_forms = [...forms].map(function (form) {
        $(form).addClass("was-validated");
        console.log($(form).serializeArray());

        return form.checkValidity() == true;
      });
      console.log(are_valid_forms);
      if (!are_valid_forms.every((valid_form) => valid_form)) {
        return;
      }

      let dataToSend = {};
      [...forms].forEach((form) => {
        $(form)
          .serializeArray()
          .forEach(function (input) {
            let name = input["name"];
            let value = input["value"];
            if (name in dataToSend) {
              if (Array.isArray(dataToSend[name])) {
                dataToSend[name].push(value);
              } else {
                dataToSend[name] = [dataToSend[name], value];
              }
            } else {
              dataToSend[name] = value;
            }
          });
      });
      console.log("dataToSend: ", dataToSend);

      this._rpc({
        route: window.location.pathname + "/handle",
        params: dataToSend,
      }).then((r) => {
        if (r.success) {
          window.location.href = window.location.pathname + `/thank-you`;
        } else {
          console.log(r.message);
        }
      });
    },
  });

  return publicWidget.registry.SecretGuestAudit;
});
