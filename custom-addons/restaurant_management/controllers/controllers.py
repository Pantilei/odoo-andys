# -*- coding: utf-8 -*-
# from odoo import http


# class FaultControl(http.Controller):
#     @http.route('/fault_control/fault_control/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fault_control/fault_control/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fault_control.listing', {
#             'root': '/fault_control/fault_control',
#             'objects': http.request.env['fault_control.fault_control'].search([]),
#         })

#     @http.route('/fault_control/fault_control/objects/<model("fault_control.fault_control"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fault_control.object', {
#             'object': obj
#         })
