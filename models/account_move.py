# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from datetime import timedelta
from odoo.exceptions import UserError
import logging

class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.move_type in ["out_invoice","out_refund"] and self.invoice_line_ids:
            if self.partner_id.property_product_pricelist and self.amount_residual > 0:
                self.verificar_estado_cliente(self.invoice_date,self.partner_id)
            self.verificar_productos_diferentes(self.journal_id,self.invoice_line_ids)
        return res

    def verificar_productos_diferentes(self,journal_id,invoice_line_ids):
        productos_diferentes = []
        for linea in invoice_line_ids:
            if linea.product_id.product_tmpl_id.diario_id.id != journal_id.id:
                productos_diferentes.append(linea.product_id.name)
        if len(productos_diferentes) > 0:
            raise UserError(_('El diario de los siguientes productos '+ str(productos_diferentes) +' debe de ser el mismo que el de la factura'))
        else:
            return True

    def verificar_estado_cliente(self,fecha_factura,partner_id):
        dias_retraso = 0
        facturas_ids = self.env['account.move'].search([('move_type','=','out_invoice'),('state','=','posted'),('partner_id','=',partner_id.id),('amount_residual','>',0)])
        estado_tarifa_ids = self.env['camaracomercio.config.estado'].search([('tarifa_id','=',partner_id.property_product_pricelist.id),('estado','=', partner_id.estado),('bloquear_cliente','=',True)])
        if facturas_ids and estado_tarifa_ids:
            for factura in facturas_ids:
                if factura.invoice_payment_term_id:
                    dias_vencimiento = factura.invoice_payment_term_id.line_ids[0].days
                    fecha_vencimiento = factura.invoice_date + timedelta(days=dias_vencimiento)
                    fecha_hoy = fields.Date.today()
                    dias_retraso = (fecha_hoy - fecha_vencimiento).days + 1
                    for estado_tarifa in estado_tarifa_ids:
                        if dias_retraso >= estado_tarifa.dias:
                            raise UserError(_('Usuario bloqueado, existen facturas con dias dias de retraso mayor igual a '+ str(estado_tarifa.dias)))
        return True