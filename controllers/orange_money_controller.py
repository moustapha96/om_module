
# from odoo import http, fields
# from odoo.http import request, Response
# import requests
# import hmac
# import hashlib
# import json
# import logging
# import werkzeug
# from datetime import datetime
# import base64

# _logger = logging.getLogger(__name__)

# class OrangeMoneyController(http.Controller):
#     @http.route('/api/payment/orange/initiate', type='http', auth='public', cors='*', methods=['POST'], csrf=False)
#     def initiate_orange_payment(self, **kwargs):
#         """Initier un paiement Orange Money"""
#         try:
#             # Validation des paramètres requis
#             data = json.loads(request.httprequest.data)
#             transaction_id = data.get('transaction_id')
#             order_id = data.get('order_id')
#             partner_id = data.get('partner_id')
#             customer_msisdn = data.get('phoneNumber') # Renommé de phoneNumber
#             amount = data.get('amount')
#             description = data.get('description', 'Payment via Orange Money')
#             currency = data.get('currency', 'XOF')
#             reference = data.get('reference')
#             success_url = data.get('success_url')

#             _logger.info(f"Received initiate_orange_payment request with data: {data}")

            
#             # Validation des champs obligatoires
#             if not all([transaction_id, order_id, partner_id, customer_msisdn, amount]):
#                 return self._make_response({'message': "Missing required fields: transaction_id, order_id, partner_id, customer_msisdn, amount"}, 400)
            
#             # Récupérer la configuration Orange Money active
#             config = request.env['orange.money.config'].sudo().search([('is_active', '=', True)], limit=1)
#             if not config:
#                 return self._make_response({'error': 'Orange Money configuration not found', 'success': False}, 400)
            
#             # Vérifier l'existence de l'order et du partner
#             order = request.env['sale.order'].sudo().browse(int(order_id)) if order_id else None
#             partner = request.env['res.partner'].sudo().browse(int(partner_id)) if partner_id else None
            
#             if not order:
#                 return self._make_response({'message': "La commande n'existe pas"}, 400)
#             if not partner:
#                 return self._make_response({'message': "Le partenaire n'existe pas"}, 400)
            
#             # Vérifier si la transaction Orange Money existe déjà
#             existing_tx = request.env['orange.money.transaction'].sudo().search([('transaction_id', '=', transaction_id)], limit=1)
#             if existing_tx:
#                 return self._make_response({
#                     'success': True,
#                     'transaction_id': existing_tx.transaction_id,
#                     'pay_token': existing_tx.pay_token,
#                     'payment_url': existing_tx.payment_url,
#                     'status': existing_tx.status or 'INITIATED',
#                     'order_id': existing_tx.order_id.id if existing_tx.order_id else False,
#                     'partner_id': existing_tx.partner_id.id,
#                     'reference': existing_tx.reference,
#                     'success_url': success_url,
#                     'deep_link': existing_tx.deep_link,
#                     'deep_link_om': existing_tx.deep_link_om,
#                     'deep_link_maxit': existing_tx.deep_link_maxit,
#                     'short_link': existing_tx.short_link,
#                     'qr_code_base64': existing_tx.qr_code_base64,
#                     'qr_id': existing_tx.qr_id,
#                     'validity_seconds': existing_tx.validity_seconds,
#                     'valid_from': existing_tx.valid_from.isoformat() if existing_tx.valid_from else None,
#                     'valid_until': existing_tx.valid_until.isoformat() if existing_tx.valid_until else None,
#                     'existe': True
#                 }, 200)
            
#             # Créer l'ordre de paiement Orange Money via la méthode du modèle de configuration
#             try:
#                 success_url_new =  f"https://dev.ccbmshop.com/om-paiement?transaction={transaction_id}"

#                 cancel_url = None
#                 if order.type_sale == "order":
#                     cancel_url = f"https://dev.ccbmshop.com/commandes/{order.id}/détails"
#                 elif order.type_sale == "creditorder":
#                     cancel_url = f"https://dev.ccbmshop.com/credit-commandes/{order.id}/détails"


#                 payment_data_from_config = config.create_payment_order(
#                     amount=amount,
#                     currency=currency,
#                     order_id=order_id,
#                     transaction_id=transaction_id,
#                     customer_msisdn=customer_msisdn,
#                     description=description,
#                     reference=reference,
#                     success_url=success_url or success_url_new,
#                     cancel_url=cancel_url
#                 )
                
            
#                 if payment_data_from_config and payment_data_from_config.get('success'):
#                     # Créer la transaction dans Odoo
#                     orange_transaction = request.env['orange.money.transaction'].sudo().create({
#                         'success_url': success_url,
#                         'cancel_url': cancel_url,
#                         'pay_token': payment_data_from_config.get('pay_token'),
#                         'transaction_id': transaction_id,
#                         'amount': amount,
#                         'currency': currency,
#                         'status': 'INITIATED',
#                         'customer_msisdn': customer_msisdn,
#                         'merchant_code': config.merchant_code,
#                         'reference': reference,
#                         'description': description,
#                         'payment_url': payment_data_from_config.get('payment_url'),
#                         'qr_code_url': payment_data_from_config.get('deep_link'), # Utiliser deep_link pour qr_code_url
#                         'qr_code_base64': payment_data_from_config.get('qr_code_base64'),
#                         'qr_id': payment_data_from_config.get('qr_id'),
#                         'deep_link': payment_data_from_config.get('deep_link'),
#                         'deep_link_om': payment_data_from_config.get('deep_link_om'),
#                         'deep_link_maxit': payment_data_from_config.get('deep_link_maxit'),
#                         'short_link': payment_data_from_config.get('short_link'),
#                         'validity_seconds': payment_data_from_config.get('validity_seconds'),
#                         'valid_from': payment_data_from_config.get('valid_from'),
#                         'valid_until': payment_data_from_config.get('valid_until'),
#                         'orange_response': payment_data_from_config.get('orange_response'),
#                         'metadata': payment_data_from_config.get('metadata'),
#                         'order_id': order.id, # Correction: doit être l'ID de la commande Odoo
#                         'partner_id': partner.id,
#                         'orange_id': payment_data_from_config.get('qr_id'),
#                         'qr_code_url': payment_data_from_config.get('deep_link'),
#                         'callback_url': payment_data_from_config.get('callback_url'),
#                     })
                    
#                     # api_transaction_model = self.env['orange.money.api.transaction']
#                     # api_transaction_model.fetch_all_transactions()
#                     # _logger.info(f"Orange Money payment order created successfully: {orange_transaction.transaction_id}")
                    
#                     return self._make_response({
#                         'success': True,
#                         'success_url': orange_transaction.success_url,
#                         'cancel_url': orange_transaction.cancel_url,
#                         'transaction_id': orange_transaction.transaction_id,
#                         'pay_token': orange_transaction.pay_token,
#                         'payment_url': orange_transaction.payment_url,
#                         'status': 'INITIATED',
#                         'order_id': orange_transaction.order_id.id if orange_transaction.order_id else False,
#                         'partner_id': orange_transaction.partner_id.id,
#                         'reference': reference,
#                         'deep_link': orange_transaction.deep_link,
#                         'deep_link_om': orange_transaction.deep_link_om,
#                         'deep_link_maxit': orange_transaction.deep_link_maxit,
#                         'short_link': orange_transaction.short_link,
#                         'qr_code_base64': orange_transaction.qr_code_base64,
#                         'qr_id': orange_transaction.qr_id,
#                         'validity_seconds': orange_transaction.validity_seconds,
#                         'valid_from': orange_transaction.valid_from.isoformat() if orange_transaction.valid_from else None,
#                         'valid_until': orange_transaction.valid_until.isoformat() if orange_transaction.valid_until else None,
#                     }, 200)
#                 else:
#                     return self._make_response({'error': payment_data_from_config.get('message', 'Failed to create Orange Money payment order')}, 400)
#             except Exception as e:
#                 _logger.error(f"Error creating Orange Money payment order: {str(e)}")
#                 return self._make_response({'error': str(e)}, 400)
#         except Exception as e:
#             _logger.error(f"Error initiating Orange Money payment: {str(e)}")
#             return self._make_response({'error': str(e)}, 400)


#     @http.route('/api/payment/orange/status/<string:transaction_id>', type='http', auth='public', cors='*', methods=['GET'])
#     def get_orange_payment_status(self, transaction_id, **kwargs):
#         """
#         Vérifie le statut d'un paiement Orange Money en temps réel et retourne les informations de la transaction.
#         """
#         try:
#             if not transaction_id:
#                 return self._make_response({'success': False, 'error': 'Transaction ID is required'}, 400)

#             transaction = request.env['orange.money.transaction'].sudo().search([('transaction_id', '=', transaction_id)], limit=1)

#             if not transaction:
#                 return self._make_response({'success': False, 'error': 'Transaction not found'}, 404)

#             config = request.env['orange.money.config'].sudo().search([('is_active', '=', True)], limit=1)
#             if not config:
#                 return self._make_response({'success': False, 'error': 'Orange Money configuration not found'}, 400)

#             if not transaction.transactionId:
#                 return self._build_transaction_response(transaction)
            
#             api_response = config.get_transaction_status(transaction.transactionId)

#             if not api_response or not api_response.get('success'):
#                 _logger.warning(f"Impossible de récupérer le statut réel pour {transaction.transactionId}, retour Odoo.")
#                 # Retourner le statut local si l'API Orange n'a pas répondu correctement
#                 return self._build_transaction_response(transaction)

#             # Mettre à jour la transaction si le statut a changé
#             new_status = api_response.get('transaction_status')
#             if new_status and new_status != transaction.status:
#                 transaction.write({
#                     'status': new_status,
#                     'updated_at': fields.Datetime.now(),
#                     'orange_response': json.dumps(api_response.get('orange_response', {})),
#                 })

#             return self._build_transaction_response(transaction)

#         except Exception as e:
#             _logger.error(f"[Orange Money] Erreur get_orange_payment_status : {str(e)}")
#             return self._make_response({'success': False, 'error': str(e)}, 400)


#     @http.route('/api/payment/orange/token/<string:pay_token>', type='http', auth='public', cors='*', methods=['GET'])
#     def get_orange_payment_by_token(self, pay_token, **kwargs):
#         """Récupérer les détails d'un paiement Orange Money par son pay_token"""
#         try:
#             # Récupérer la configuration Orange Money active
#             config = request.env['orange.money.config'].sudo().search([('is_active', '=', True)], limit=1)
#             if not config:
#                 return self._make_response({'error': 'Configuration not found'}, 400)
            
#             # Utiliser la nouvelle méthode du modèle pour récupérer le statut par pay_token
#             payment_data = config.get_payment_status_by_token(pay_token)
            
#             if payment_data:
#                 # Rechercher la transaction correspondante dans Odoo
#                 transaction = request.env['orange.money.transaction'].sudo().search([('pay_token', '=', pay_token)], limit=1)
#                 result = {
#                     'success': True,
#                     'payment': payment_data
#                 }
#                 if transaction:
#                     # Mettre à jour la transaction avec les nouvelles données
#                     status = payment_data.get('status', '').upper()
#                     odoo_status = self._map_orange_status_to_odoo(status)
#                     if odoo_status and odoo_status != transaction.status:
#                         transaction.write({
#                             'status': odoo_status,
#                             'orange_response': json.dumps(payment_data),
#                             'webhook_data': json.dumps(payment_data),
#                         })
#                     result['transaction'] = {
#                         'id': transaction.id,
#                         'transaction_id': transaction.transaction_id,
#                         'status': transaction.status,
#                         'reference': transaction.reference,
#                         'pay_token': transaction.pay_token,
#                         'payment_url': transaction.payment_url,
#                         'deep_link': transaction.deep_link,
#                         'deep_link_om': transaction.deep_link_om,
#                         'deep_link_maxit': transaction.deep_link_maxit,
#                         'short_link': transaction.short_link,
#                         'qr_code_base64': transaction.qr_code_base64,
#                         'qr_id': transaction.qr_id,
#                         'validity_seconds': transaction.validity_seconds,
#                         'valid_from': transaction.valid_from.isoformat() if transaction.valid_from else None,
#                         'valid_until': transaction.valid_until.isoformat() if transaction.valid_until else None,
#                     }
#                 return self._make_response(result, 200)
#             else:
#                 return self._make_response({'error': 'Payment not found'}, 404)
#         except Exception as e:
#             _logger.error(f"Error getting Orange Money payment by token: {str(e)}")
#             return self._make_response({'error': f'Internal error: {str(e)}', 'success': False}, 400)


#     @http.route('/orange/payment/cancel', type='http', auth='public', csrf=False, methods=['GET', 'POST'])
#     def orange_payment_cancel(self, **kwargs):
#         """Gérer les callbacks d'annulation Orange Money"""
#         try:
#             _logger.info(f"Orange Money cancel callback received: {kwargs}")
            
#             pay_token = kwargs.get('pay_token')
            
#             if pay_token:
#                 transaction = request.env['orange.money.transaction'].sudo().search([
#                     ('pay_token', '=', pay_token)
#                 ], limit=1)
                
#                 if transaction:
#                     transaction.write({
#                         'status': 'CANCELLED',
#                         'orange_response': json.dumps(kwargs)
#                     })
#             return request.redirect('/payment/cancelled')
#         except Exception as e:
#             _logger.error(f"Error in Orange Money cancel callback: {str(e)}")
#             return request.redirect('/payment/cancelled')


#     # def _process_orange_webhook(self, webhook_data):
#     #     """
#     #     Traiter les données du webhook Orange Money
#     #     """
#     #     try:
#     #         _logger.info(f"Traitement webhook Orange Money : {webhook_data}")

#     #         reference = webhook_data.get('reference')
#     #         transaction_id = webhook_data.get('transactionId')
#     #         status = webhook_data.get('status', '').upper()

#     #         if not reference and not transaction_id:
#     #             _logger.error("Webhook Orange : Aucun identifiant de transaction (reference ou transactionId)")
#     #             return {'error': 'Missing reference or transactionId', 'success': False}

#     #         # Recherche de la transaction par reference ou transactionId
#     #         transaction = request.env['orange.money.transaction'].sudo().search([
#     #             '|',
#     #             ('reference', '=', reference),
#     #             ('transaction_id', '=', transaction_id)
#     #         ], limit=1)

#     #         if not transaction:
#     #             _logger.warning(f"Aucune transaction trouvée pour reference={reference} ou transactionId={transaction_id}")
#     #             return {'error': 'Transaction not found', 'success': False}

#     #         # Mapping du statut Orange vers Odoo
#     #         new_status = self._map_orange_status_to_odoo(status)

#     #         if new_status and new_status != transaction.status:
#     #             _logger.info(f"Mise à jour du statut pour la transaction {transaction.id} vers {new_status}")

#     #             update_vals = {
#     #                 'status': new_status,
#     #                 'updated_at': fields.Datetime.now(),
#     #                 'webhook_data': json.dumps(webhook_data),
#     #                 'payment_method': webhook_data.get('paymentMethod'),
#     #                 'channel': webhook_data.get('channel'),
#     #                 'amount': webhook_data.get('amount', {}).get('value'),
#     #                 'customer_msisdn': webhook_data.get('customer', {}).get('id'),
#     #             }

#     #             transaction.write(update_vals)

#     #             # Déclencher les actions associées
#     #             if new_status == 'SUCCESS':
#     #                 self._handle_payment_completed(transaction, webhook_data)
#     #             elif new_status == 'FAILED':
#     #                 self._handle_payment_failed(transaction, webhook_data)

#     #             return {
#     #                 'success': True,
#     #                 'transaction_updated': True,
#     #                 'transaction_id': transaction.transaction_id
#     #             }

#     #         _logger.info(f"Aucune mise à jour requise pour la transaction {transaction.id}")

#     #         return {
#     #             'success': True,
#     #             'transaction_updated': False,
#     #             'transaction_id': transaction.transaction_id
#     #         }

#     #     except Exception as e:
#     #         _logger.error(f"Erreur traitement webhook Orange Money : {str(e)}")
#     #         return {'error': str(e), 'success': False}


#     def _map_orange_status_to_odoo(self, orange_status):
#         """Mapper les statuts Orange Money vers les statuts Odoo"""
#         status_mapping = {
#             'SUCCESS': 'SUCCESS',
#             'SUCCEEDED': 'SUCCESS',
#             'FAILED': 'FAILED',
#             'PENDING': 'PENDING',
#             'PROCESSING': 'PENDING',
#             'EXPIRED': 'FAILED', # Mapping EXPIRED to FAILED for Odoo status
#             'CANCELLED': 'CANCELLED',
#             'CANCELED': 'CANCELLED',
#             'REJECTED': 'REJECTED', # Added REJECTED
#         }
#         return status_mapping.get(orange_status.upper(), 'PENDING')

#     # def _handle_payment_completed(self, transaction, payment_data):
#     #     """Gérer un paiement complété"""
#     #     try:
#     #         order = transaction.order_id
#     #         resultat = self._create_payment_transaction(transaction)
#     #         if resultat:
#     #             _logger.info(f"Payment completed for Orange Money transaction {transaction.reference} (transaction_id: {transaction.transaction_id})")
#     #         return resultat
#     #     except Exception as e:
#     #         _logger.error(f"Error handling completed Orange Money payment: {str(e)}")

#     # def _handle_payment_failed(self, transaction, payment_data):
#     #     """Gérer un paiement échoué"""
#     #     try:
#     #         _logger.warning(f"Orange Money payment failed for transaction {transaction.reference} (transaction_id: {transaction.transaction_id})")
#     #     except Exception as e:
#     #         _logger.error(f"Error handling failed Orange Money payment: {str(e)}")

#     def _refresh_transaction_status(self, transaction):
#         """Rafraîchir le statut d'une transaction depuis l'API Orange Money"""
#         try:
#             _logger.info(f"Refreshing status for Orange Money transaction {transaction.id}")
#             config = request.env['orange.money.config'].sudo().search([('is_active', '=', True)], limit=1)
#             if not config:
#                 return False
            
#             # Utiliser la méthode du modèle pour récupérer le statut par transaction_id
#             payment_data = config.get_transaction_status(transaction.transaction_id)
            
#             if payment_data:
#                 orange_status = payment_data.get('status', '').upper()
#                 new_status = self._map_orange_status_to_odoo(orange_status)
                
#                 if new_status != transaction.status:
#                     _logger.info(f"Updating status of Orange Money transaction {transaction.id} from {transaction.status} to {new_status}")
#                     transaction.write({
#                         'status': new_status,
#                         'updated_at': fields.Datetime.now(),
#                         'orange_response': json.dumps(payment_data),
#                         'qr_id': payment_data.get('qrId'),
#                         'deep_link': payment_data.get('deepLink'),
#                         'deep_link_om': payment_data.get('deepLinks', {}).get('OM'),
#                         'deep_link_maxit': payment_data.get('deepLinks', {}).get('MAXIT'),
#                         'short_link': payment_data.get('shortLink'),
#                         'validity_seconds': payment_data.get('validity'),
#                         'valid_from': payment_data.get('validFor', {}).get('startDateTime'),
#                         'valid_until': payment_data.get('validFor', {}).get('endDateTime'),
#                     })
#                 return True
#             return False
#         except Exception as e:
#             _logger.error(f"Error refreshing Orange Money transaction status: {str(e)}")
#             return False

#     def _make_response(self, data, status):
#         return request.make_response(
#             json.dumps(data),
#             status=status,
#             headers={'Content-Type': 'application/json'}
#         )

#     def _order_to_dict(self, order):
#         if not order:
#             return None
#         return {
#             'id': order.id,
#             'type_sale': order.type_sale,
#             'name': order.name,
#             'partner_id': order.partner_id.id,
#             'type_sale': order.type_sale,
#             'currency_id': order.currency_id.id,
#             'company_id': order.company_id.id,
#             'state': order.state,
#             'amount_total': order.amount_total,
#             'invoice_status': order.invoice_status,
#             'amount_total': order.amount_total,
#             'advance_payment_status': order.advance_payment_status
#         }

#     def _create_payment_transaction(self, transaction):
#         """Créer un paiement et une facture pour une transaction Orange Money réussie"""
#         try:
#             order = transaction.order_id
#             partner = transaction.partner_id
#             company = partner.company_id or request.env['res.company'].sudo().search([('id', '=', 1)], limit=1)
            
#             # Rechercher un journal de vente
#             journal = request.env['account.journal'].sudo().search([
#                 ('type', '=', 'sale'),
#                 ('company_id', '=', company.id)
#             ], limit=1)
#             if not journal:
#                 _logger.error("Aucun journal de vente trouvé pour la compagnie.")
#                 return False
            
#             payment_method = request.env['account.payment.method'].sudo().search([('payment_type', '=', 'inbound')], limit=1)
#             payment_method_line = request.env['account.payment.method.line'].sudo().search([
#                 ('payment_method_id', '=', payment_method.id),
#                 ('journal_id', '=', journal.id)
#             ], limit=1)
#             if not payment_method_line:
#                 _logger.error("Aucune méthode de paiement trouvée.")
#                 return False
            
#             # Confirmer la commande si elle n'est pas déjà confirmée
#             if order and order.state not in ['sale', 'done']:
#                 order.action_confirm()
            
#             # Créer les lignes de facture
#             invoice_lines = []
#             for line in order.order_line:
#                 invoice_lines.append((0, 0, {
#                     'name': line.name,
#                     'quantity': line.product_uom_qty,
#                     'price_unit': line.price_unit,
#                     'product_id': line.product_id.id,
#                     'tax_ids': [(6, 0, line.tax_id.ids)],
#                     'sale_line_ids': [(6, 0, line.ids)], # Link to sale order line
#                 }))
            
#             # Créer la facture
#             invoice = request.env['account.move'].sudo().create({
#                 'partner_id': partner.id,
#                 'move_type': 'out_invoice',
#                 'invoice_date': transaction.created_at,
#                 'invoice_date_due': transaction.completed_at,
#                 'currency_id': partner.currency_id.id or order.currency_id.id or journal.currency_id.id,
#                 'journal_id': journal.id,
#                 'invoice_line_ids': invoice_lines,
#                 'invoice_origin': order.name,
#                 'company_id': company.id,
#             })
            
#             # Valider la facture
#             invoice.action_post()
            
#             # Relier la facture à la commande (si ce n'est pas déjà fait par action_post)
#             if invoice.id not in order.invoice_ids.ids:
#                 order.write({'invoice_ids': [(4, invoice.id)]})
            
#             # Créer le paiement
#             payment = request.env['account.payment'].sudo().create({
#                 'payment_type': 'inbound',
#                 'partner_type': 'customer',
#                 'partner_id': partner.id,
#                 'amount': transaction.amount,
#                 'journal_id': journal.id,
#                 'currency_id': partner.currency_id.id or order.currency_id.id or journal.currency_id.id,
#                 'payment_method_line_id': payment_method_line.id,
#                 'ref': order.name,
#                 'destination_account_id': partner.property_account_receivable_id.id,
#             })
            
#             # Valider le paiement
#             payment.action_post()
            
#             _logger.info(f"Paiement et facture créés avec succès pour la transaction Orange Money {transaction.transaction_id}")
#             return True
#         except Exception as e:
#             _logger.error(f"Erreur lors de la création du paiement Orange Money: {str(e)}")
#             return False



#     # Route pour récupérer les transactions d'un partenaire
#     @http.route('/api/payment/orange/partner/<int:partner_id>/transactions', type='http', auth='public', cors='*', methods=['GET'])
#     def get_partner_orange_transactions(self, partner_id):
#         try:
#             partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)])
#             if not partner:
#                 return self._make_response({'success': False, 'error': 'Partner not found'}, 404)
            
#             resultats = []
#             transactions = request.env['orange.money.transaction'].sudo().search([('partner_id', '=', partner_id)])
            
#             for transaction in transactions:
#                 # Convertir les données binaires en base64
#                 facture_pdf_base64 = None
#                 if transaction.facture_pdf:
#                     facture_pdf_base64 = base64.b64encode(transaction.facture_pdf).decode('utf-8')
                
#                 resultats.append({
#                     'transaction_id': transaction.transaction_id,
#                     'pay_token': transaction.pay_token,
#                     'reference': transaction.reference,
#                     'status': transaction.status,
#                     'amount': transaction.amount,
#                     'currency': transaction.currency,
#                     'customer_msisdn': transaction.customer_msisdn,
#                     'description': transaction.description,
#                     'payment_url': transaction.payment_url,
#                     'order_id': transaction.order_id.id if transaction.order_id else None,
#                     'order': self._order_to_dict(transaction.order_id),
#                     'partner_id': transaction.partner_id.id,
#                     'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
#                     'updated_at': transaction.updated_at.isoformat() if transaction.updated_at else None,
#                     'completed_at': transaction.completed_at.isoformat() if transaction.completed_at else None,
#                     'url_facture': transaction.url_facture,
#                     'facture_pdf_base64': facture_pdf_base64,
#                     'facture_filename': transaction.facture_filename,
#                     'deep_link': transaction.deep_link,
#                     'deep_link_om': transaction.deep_link_om,
#                     'deep_link_maxit': transaction.deep_link_maxit,
#                     'short_link': transaction.short_link,
#                     'qr_code_base64': transaction.qr_code_base64,
#                     'qr_id': transaction.qr_id,
#                     'validity_seconds': transaction.validity_seconds,
#                     'valid_from': transaction.valid_from.isoformat() if transaction.valid_from else None,
#                     'valid_until': transaction.valid_until.isoformat() if transaction.valid_until else None,
#                 })
#             return self._make_response(resultats, 200)
#         except Exception as e:
#             _logger.error(f"Error getting partner Orange Money transactions: {str(e)}")
#             return self._make_response({'success': False, 'error': str(e)}, 400)
        


#     def _build_transaction_response(self, transaction):
#         """Construit la réponse JSON complète pour une transaction"""
#         return self._make_response({
#             'success': True, 
#             'transaction_id': transaction.transaction_id,
#             'transactionId': transaction.transactionId,
#             'reference': transaction.reference,
#             'status': transaction.status or 'INITIATED',
#             'amount': transaction.amount,
#             'currency': transaction.currency,
#             'customer_msisdn': transaction.customer_msisdn,
#             'description': transaction.description,
#             'order_id': transaction.order_id.id,
#             'order': self._order_to_dict(transaction.order_id),
#             'partner_id': transaction.partner_id.id,
#             'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
#             'updated_at': transaction.updated_at.isoformat() if transaction.updated_at else None,
#             'channel': transaction.channel,
#             'type': transaction.transaction_type,
#             'metadata': json.loads(transaction.metadata) if transaction.metadata else None,
#             'success_url': transaction.success_url,
        
#         }, 200)


from odoo import http, fields
from odoo.http import request, Response
import requests
import hmac
import hashlib
import json
import logging
import werkzeug
from datetime import datetime
import base64

_logger = logging.getLogger(__name__)

class OrangeMoneyController(http.Controller):
    @http.route('/api/payment/orange/initiate', type='http', auth='public', cors='*', methods=['POST'], csrf=False)
    def initiate_orange_payment(self, **kwargs):
        """Initier un paiement Orange Money"""
        try:
            # Validation des paramètres requis
            data = json.loads(request.httprequest.data)
            transaction_id = data.get('transaction_id')
            order_id = data.get('order_id')
            partner_id = data.get('partner_id')
            customer_msisdn = data.get('phoneNumber') # Renommé de phoneNumber
            amount = data.get('amount')
            description = data.get('description', 'Payment via Orange Money')
            currency = data.get('currency', 'XOF')
            reference = data.get('reference')
            success_url = data.get('success_url')

            _logger.info(f"Received initiate_orange_payment request with data: {data}")

            
            # Validation des champs obligatoires
            if not all([transaction_id, order_id, partner_id, customer_msisdn, amount]):
                return self._make_response({'message': "Missing required fields: transaction_id, order_id, partner_id, customer_msisdn, amount"}, 400)
            
            # Récupérer la configuration Orange Money active
            config = request.env['orange.money.config'].sudo().search([('is_active', '=', True)], limit=1)
            if not config:
                return self._make_response({'error': 'Orange Money configuration not found', 'success': False}, 400)
            
            # Vérifier l'existence de l'order et du partner
            order = request.env['sale.order'].sudo().browse(int(order_id)) if order_id else None
            partner = request.env['res.partner'].sudo().browse(int(partner_id)) if partner_id else None
            
            if not order:
                return self._make_response({'message': "La commande n'existe pas"}, 400)
            if not partner:
                return self._make_response({'message': "Le partenaire n'existe pas"}, 400)
            
            # Vérifier si la transaction Orange Money existe déjà
            existing_tx = request.env['orange.money.transaction'].sudo().search([('transaction_id', '=', transaction_id)], limit=1)
            if existing_tx:
                return self._make_response({
                    'success': True,
                    'transaction_id': existing_tx.transaction_id,
                    'pay_token': existing_tx.pay_token,
                    'payment_url': existing_tx.payment_url,
                    'status': existing_tx.status or 'INITIATED',
                    'order_id': existing_tx.order_id.id if existing_tx.order_id else False,
                    'partner_id': existing_tx.partner_id.id,
                    'reference': existing_tx.reference,
                    'success_url': success_url,
                    'deep_link': existing_tx.deep_link,
                    'deep_link_om': existing_tx.deep_link_om,
                    'deep_link_maxit': existing_tx.deep_link_maxit,
                    'short_link': existing_tx.short_link,
                    'qr_code_base64': existing_tx.qr_code_base64,
                    'qr_id': existing_tx.qr_id,
                    'validity_seconds': existing_tx.validity_seconds,
                    'valid_from': existing_tx.valid_from.isoformat() if existing_tx.valid_from else None,
                    'valid_until': existing_tx.valid_until.isoformat() if existing_tx.valid_until else None,
                    'existe': True
                }, 200)
            
            # Créer l'ordre de paiement Orange Money via la méthode du modèle de configuration
            try:
                success_url_new =  f"https://dev.ccbmshop.com/om-paiement?transaction={transaction_id}"

                cancel_url = None
                if order.type_sale == "order":
                    cancel_url = f"https://dev.ccbmshop.com/commandes/{order.id}/détails"
                elif order.type_sale == "creditorder":
                    cancel_url = f"https://dev.ccbmshop.com/credit-commandes/{order.id}/détails"


                payment_data_from_config = config.create_payment_order(
                    amount=amount,
                    currency=currency,
                    order_id=order_id,
                    transaction_id=transaction_id,
                    customer_msisdn=customer_msisdn,
                    description=description,
                    reference=reference,
                    success_url=success_url or success_url_new,
                    cancel_url=cancel_url
                )
                
            
                if payment_data_from_config and payment_data_from_config.get('success'):
                    # Créer la transaction dans Odoo
                    orange_transaction = request.env['orange.money.transaction'].sudo().create({
                        'success_url': success_url,
                        'cancel_url': cancel_url,
                        'pay_token': payment_data_from_config.get('pay_token'),
                        'transaction_id': transaction_id,
                        'amount': amount,
                        'currency': currency,
                        'status': 'INITIATED',
                        'customer_msisdn': customer_msisdn,
                        'merchant_code': config.merchant_code,
                        'reference': reference,
                        'description': description,
                        'payment_url': payment_data_from_config.get('payment_url'),
                        'qr_code_url': payment_data_from_config.get('deep_link'), # Utiliser deep_link pour qr_code_url
                        'qr_code_base64': payment_data_from_config.get('qr_code_base64'),
                        'qr_id': payment_data_from_config.get('qr_id'),
                        'deep_link': payment_data_from_config.get('deep_link'),
                        'deep_link_om': payment_data_from_config.get('deep_link_om'),
                        'deep_link_maxit': payment_data_from_config.get('deep_link_maxit'),
                        'short_link': payment_data_from_config.get('short_link'),
                        'validity_seconds': payment_data_from_config.get('validity_seconds'),
                        'valid_from': payment_data_from_config.get('valid_from'),
                        'valid_until': payment_data_from_config.get('valid_until'),
                        'orange_response': payment_data_from_config.get('orange_response'),
                        'metadata': payment_data_from_config.get('metadata'),
                        'order_id': order.id, # Correction: doit être l'ID de la commande Odoo
                        'partner_id': partner.id,
                        'orange_id': payment_data_from_config.get('qr_id'),
                        'qr_code_url': payment_data_from_config.get('deep_link'),
                        'callback_url': payment_data_from_config.get('callback_url'),
                    })
                    
                    # api_transaction_model = self.env['orange.money.api.transaction']
                    # api_transaction_model.fetch_all_transactions()
                    # _logger.info(f"Orange Money payment order created successfully: {orange_transaction.transaction_id}")
                    
                    return self._make_response({
                        'success': True,
                        'success_url': orange_transaction.success_url,
                        'cancel_url': orange_transaction.cancel_url,
                        'transaction_id': orange_transaction.transaction_id,
                        'pay_token': orange_transaction.pay_token,
                        'payment_url': orange_transaction.payment_url,
                        'status': 'INITIATED',
                        'order_id': orange_transaction.order_id.id if orange_transaction.order_id else False,
                        'partner_id': orange_transaction.partner_id.id,
                        'reference': reference,
                        'deep_link': orange_transaction.deep_link,
                        'deep_link_om': orange_transaction.deep_link_om,
                        'deep_link_maxit': orange_transaction.deep_link_maxit,
                        'short_link': orange_transaction.short_link,
                        'qr_code_base64': orange_transaction.qr_code_base64,
                        'qr_id': orange_transaction.qr_id,
                        'validity_seconds': orange_transaction.validity_seconds,
                        'valid_from': orange_transaction.valid_from.isoformat() if orange_transaction.valid_from else None,
                        'valid_until': orange_transaction.valid_until.isoformat() if orange_transaction.valid_until else None,
                    }, 200)
                else:
                    return self._make_response({'error': payment_data_from_config.get('message', 'Failed to create Orange Money payment order')}, 400)
            except Exception as e:
                _logger.error(f"Error creating Orange Money payment order: {str(e)}")
                return self._make_response({'error': str(e)}, 400)
        except Exception as e:
            _logger.error(f"Error initiating Orange Money payment: {str(e)}")
            return self._make_response({'error': str(e)}, 400)



    @http.route('/api/payment/orange/token/<string:pay_token>', type='http', auth='public', cors='*', methods=['GET'])
    def get_orange_payment_by_token(self, pay_token, **kwargs):
        """Récupérer les détails d'un paiement Orange Money par son pay_token"""
        try:
            # Récupérer la configuration Orange Money active
            config = request.env['orange.money.config'].sudo().search([('is_active', '=', True)], limit=1)
            if not config:
                return self._make_response({'error': 'Configuration not found'}, 400)
            
            # Utiliser la nouvelle méthode du modèle pour récupérer le statut par pay_token
            payment_data = config.get_payment_status_by_token(pay_token)
            
            if payment_data:
                # Rechercher la transaction correspondante dans Odoo
                transaction = request.env['orange.money.transaction'].sudo().search([('pay_token', '=', pay_token)], limit=1)
                result = {
                    'success': True,
                    'payment': payment_data
                }
                if transaction:
                    # Mettre à jour la transaction avec les nouvelles données
                    status = payment_data.get('status', '').upper()
                    odoo_status = self._map_orange_status_to_odoo(status)
                    if odoo_status and odoo_status != transaction.status:
                        transaction.write({
                            'status': odoo_status,
                            'orange_response': json.dumps(payment_data),
                            'webhook_data': json.dumps(payment_data),
                        })
                    result['transaction'] = {
                        'id': transaction.id,
                        'transaction_id': transaction.transaction_id,
                        'status': transaction.status,
                        'reference': transaction.reference,
                        'pay_token': transaction.pay_token,
                        'payment_url': transaction.payment_url,
                        'deep_link': transaction.deep_link,
                        'deep_link_om': transaction.deep_link_om,
                        'deep_link_maxit': transaction.deep_link_maxit,
                        'short_link': transaction.short_link,
                        'qr_code_base64': transaction.qr_code_base64,
                        'qr_id': transaction.qr_id,
                        'validity_seconds': transaction.validity_seconds,
                        'valid_from': transaction.valid_from.isoformat() if transaction.valid_from else None,
                        'valid_until': transaction.valid_until.isoformat() if transaction.valid_until else None,
                    }
                return self._make_response(result, 200)
            else:
                return self._make_response({'error': 'Payment not found'}, 404)
        except Exception as e:
            _logger.error(f"Error getting Orange Money payment by token: {str(e)}")
            return self._make_response({'error': f'Internal error: {str(e)}', 'success': False}, 400)


    def _map_orange_status_to_odoo(self, orange_status):
        """Mapper les statuts Orange Money vers les statuts Odoo"""
        status_mapping = {
            'SUCCESS': 'SUCCESS',
            'SUCCEEDED': 'SUCCESS',
            'FAILED': 'FAILED',
            'PENDING': 'PENDING',
            'PROCESSING': 'PENDING',
            'EXPIRED': 'FAILED', # Mapping EXPIRED to FAILED for Odoo status
            'CANCELLED': 'CANCELLED',
            'CANCELED': 'CANCELLED',
            'REJECTED': 'REJECTED', # Added REJECTED
        }
        return status_mapping.get(orange_status.upper(), 'PENDING')

    
    def _make_response(self, data, status):
        return request.make_response(
            json.dumps(data),
            status=status,
            headers={'Content-Type': 'application/json'}
        )

    def _order_to_dict(self, order):
        if not order:
            return None
        return {
            'id': order.id,
            'type_sale': order.type_sale,
            'name': order.name,
            'partner_id': order.partner_id.id,
            'type_sale': order.type_sale,
            'currency_id': order.currency_id.id,
            'company_id': order.company_id.id,
            'state': order.state,
            'amount_total': order.amount_total,
            'invoice_status': order.invoice_status,
            'amount_total': order.amount_total,
            'advance_payment_status': order.advance_payment_status
        }




    # Route pour récupérer les transactions d'un partenaire
    @http.route('/api/payment/orange/partner/<int:partner_id>/transactions', type='http', auth='public', cors='*', methods=['GET'])
    def get_partner_orange_transactions(self, partner_id):
        try:
            partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)])
            if not partner:
                return self._make_response({'success': False, 'error': 'Partner not found'}, 404)
            
            resultats = []
            transactions = request.env['orange.money.transaction'].sudo().search([('partner_id', '=', partner_id)])
            
            for transaction in transactions:
                # Convertir les données binaires en base64
                facture_pdf_base64 = None
                if transaction.facture_pdf:
                    facture_pdf_base64 = base64.b64encode(transaction.facture_pdf).decode('utf-8')
                
                resultats.append({
                    'transaction_id': transaction.transaction_id,
                    'pay_token': transaction.pay_token,
                    'reference': transaction.reference,
                    'status': transaction.status,
                    'amount': transaction.amount,
                    'currency': transaction.currency,
                    'customer_msisdn': transaction.customer_msisdn,
                    'description': transaction.description,
                    'payment_url': transaction.payment_url,
                    'order_id': transaction.order_id.id if transaction.order_id else None,
                    'order': self._order_to_dict(transaction.order_id),
                    'partner_id': transaction.partner_id.id,
                    'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
                    'updated_at': transaction.updated_at.isoformat() if transaction.updated_at else None,
                    'completed_at': transaction.completed_at.isoformat() if transaction.completed_at else None,
                    'url_facture': transaction.url_facture,
                    'facture_pdf_base64': facture_pdf_base64,
                    'facture_filename': transaction.facture_filename,
                    'deep_link': transaction.deep_link,
                    'deep_link_om': transaction.deep_link_om,
                    'deep_link_maxit': transaction.deep_link_maxit,
                    'short_link': transaction.short_link,
                    'qr_code_base64': transaction.qr_code_base64,
                    'qr_id': transaction.qr_id,
                    'validity_seconds': transaction.validity_seconds,
                    'valid_from': transaction.valid_from.isoformat() if transaction.valid_from else None,
                    'valid_until': transaction.valid_until.isoformat() if transaction.valid_until else None,
                })
            return self._make_response(resultats, 200)
        except Exception as e:
            _logger.error(f"Error getting partner Orange Money transactions: {str(e)}")
            return self._make_response({'success': False, 'error': str(e)}, 400)
        


    def _build_transaction_response(self, transaction):
        """Construit la réponse JSON complète pour une transaction"""
        return self._make_response({
            'success': True, 
            'transaction_id': transaction.transaction_id,
            'transactionId': transaction.transactionId,
            'reference': transaction.reference,
            'status': transaction.status or 'INITIATED',
            'amount': transaction.amount,
            'currency': transaction.currency,
            'customer_msisdn': transaction.customer_msisdn,
            'description': transaction.description,
            'order_id': transaction.order_id.id,
            'order': self._order_to_dict(transaction.order_id),
            'partner_id': transaction.partner_id.id,
            'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
            'updated_at': transaction.updated_at.isoformat() if transaction.updated_at else None,
            'channel': transaction.channel,
            'type': transaction.transaction_type,
            'metadata': json.loads(transaction.metadata) if transaction.metadata else None,
            'success_url': transaction.success_url,
        
        }, 200)
    
    
    @http.route('/api/payment/orange/status/<string:transaction_id>', type='http', auth='public', cors='*', methods=['GET'])
    def get_orange_payment_status(self, transaction_id, **kwargs):
        """
        Vérifie le statut d'un paiement Orange Money en temps réel,
        met à jour la transaction si besoin, et déclenche la création
        du paiement et de la facture si succès.
        """
        try:
            if not transaction_id:
                return self._make_response({'success': False, 'error': 'Transaction ID is required'}, 400)

            transaction = request.env['orange.money.transaction'].sudo().search([('transaction_id', '=', transaction_id)], limit=1)
            if not transaction:
                return self._make_response({'success': False, 'error': 'Transaction not found'}, 404)

            config = request.env['orange.money.config'].sudo().search([('is_active', '=', True)], limit=1)
            if not config:
                return self._make_response({'success': False, 'error': 'Orange Money configuration not found'}, 400)

            if not transaction.transactionId:
                _logger.warning(f"[Orange Money] Transaction {transaction_id} has no transactionId, cannot fetch status")
                return self._build_transaction_response(transaction)

            # Appel API Orange Money pour obtenir le statut
            api_response = config.get_transaction_status(transaction.transactionId)
            if not api_response or not api_response.get('success'):
                _logger.warning(f"[Orange Money] Impossible de récupérer le statut réel pour {transaction.transactionId}")
                return self._build_transaction_response(transaction)
            
            _logger.info(f"[Orange Money] Statut récupéré pour {transaction.transactionId}: {api_response.get('transaction_status')}")
            _logger.info(f"API Response: {api_response}")
            
            # Mise à jour du statut si différent
            new_status = api_response.get('transaction_status')
            if new_status and new_status != transaction.status:
                transaction.write({
                    'status': new_status,
                    'updated_at': fields.Datetime.now(),
                    'orange_response': json.dumps(api_response.get('orange_response', {})),
                })

            # Créer paiement/facture uniquement si la transaction est réussie
            if transaction.status == 'SUCCESS':
                # resultat = self._create_payment_without_invoice(transaction)
                # if resultat:
                _logger.info(f"✅ Paiement créé pour la transaction {transaction_id}")
                return self._build_transaction_response(transaction)
                # else:
                #     _logger.error(f"Erreur lors de la création du paiement pour la transaction {transaction_id}")
                #     return self._make_response({'success': False, 'error': 'Erreur lors de la création du paiement'}, 400)
            _logger.info(f"Statut de la transaction {transaction_id} : {transaction.status}")
            return self._build_transaction_response(transaction)

        except Exception as e:
            _logger.exception(f"[Orange Money] Erreur dans get_orange_payment_status : {str(e)}")
            return self._make_response({'success': False, 'error': str(e)}, 400)


    

    def _create_payment_transaction(self, transaction):
        """Créer un paiement et une facture pour une transaction Orange Money réussie"""
        try:
            _logger.info(f"Début de la création du paiement et de la facture pour la transaction {transaction.transaction_id}")
            order = transaction.order_id
            partner = transaction.partner_id
            company = partner.company_id or request.env['res.company'].sudo().search([('id', '=', 1)], limit=1)
            _logger.info(f"Compagnie trouvée: {company.name}")

            journal = request.env['account.journal'].sudo().search([('code', '=', 'CSH1'), ('company_id', '=', company.id)], limit=1)
            if not journal:
                _logger.error("Aucun journal de vente trouvé pour la compagnie.")
                return False

            _logger.info(f"Journal trouvé: {journal.name}")

            payment_method = request.env['account.payment.method'].sudo().search([('payment_type', '=', 'inbound')], limit=1)
            if not payment_method:
                _logger.error("Aucune méthode de paiement trouvée.")
                return False

            _logger.info(f"Méthode de paiement trouvée: {payment_method.name}")

            payment_method_line = request.env['account.payment.method.line'].sudo().search([
                ('payment_method_id', '=', payment_method.id),
                ('journal_id', '=', journal.id)
            ], limit=1)
            if not payment_method_line:
                _logger.error("Aucune ligne de méthode de paiement trouvée.")
                return False

            _logger.info(f"Ligne de méthode de paiement trouvée: {payment_method_line.id}")

            if order and order.state not in ['sale', 'done']:
                _logger.info(f"Confirmation de la commande {order.name}")
                order.action_confirm()

            invoice_lines = []
            for line in order.order_line:
                invoice_lines.append((0, 0, {
                    'name': line.name,
                    'quantity': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'product_id': line.product_id.id,
                    'tax_ids': [(6, 0, line.tax_id.ids)],
                    'sale_line_ids': [(6, 0, line.ids)],
                }))

            # Déterminer la devise à utiliser pour la facture
            currency_id = partner.currency_id.id or order.currency_id.id or journal.currency_id.id
            if not currency_id:
                _logger.error("Aucune devise trouvée pour la facture.")
                return False

            # _logger.info(f"Création de la facture pour la commande {order.name}")
            invoice = request.env['account.move'].sudo().create({
                'partner_id': partner.id,
                'move_type': 'out_invoice',
                'invoice_date': transaction.created_at,
                'invoice_date_due': transaction.completed_at,
                'currency_id': currency_id,
                'journal_id': journal.id,
                'invoice_line_ids': invoice_lines,
                'invoice_origin': order.name,
                'company_id': company.id,
            })

            invoice.action_post()
            _logger.info(f"Facture créée et validée pour la commande {order.name}")

            if invoice.id not in order.invoice_ids.ids:
                order.write({'invoice_ids': [(4, invoice.id)]})

            if order.amount_residual > 0:
                _logger.info(f"Création du paiement pour la commande {order.name}")
                account_payment = request.env['account.payment'].sudo().create({
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'partner_id': partner.id,
                    'amount': transaction.amount,
                    'journal_id': journal.id,
                    'currency_id': currency_id,
                    'payment_method_line_id': payment_method_line.id,
                    'payment_method_id': payment_method.id,
                    'ref': order.name,
                    'sale_id': order.id,
                    'is_reconciled': True,
                    'destination_account_id': partner.property_account_receivable_id.id,
                })
                account_payment.action_post()
                _logger.info(f"Paiement créé et validé pour la commande {order.name}")
            else:
                _logger.warning(f"Le montant résiduel de la commande {order.name} est de 0, aucun paiement créé.")

            _logger.info(f"Paiement et facture créés avec succès pour la transaction Orange Money {transaction.transaction_id}")
            return True
        except Exception as e:
            _logger.error(f"Erreur lors de la création du paiement Orange Money: {str(e)}")
            return False
        
    def _create_payment_without_invoice(self, transaction):
        """Créer un paiement sans facture pour une transaction Orange Money réussie"""
        try:
            _logger.info(f"Début de la création du paiement et de la facture pour la transaction {transaction.transaction_id}")
            order = transaction.order_id
            partner = transaction.partner_id
            company = partner.company_id or request.env['res.company'].sudo().search([('id', '=', 1)], limit=1)
            _logger.info(f"Compagnie trouvée: {company.name}")

            journal = request.env['account.journal'].sudo().search([('code', '=', 'CSH1'), ('company_id', '=', company.id)], limit=1)
            if not journal:
                _logger.error("Aucun journal de vente trouvé pour la compagnie.")
                return False

            _logger.info(f"Journal trouvé: {journal.name}")

            payment_method = request.env['account.payment.method'].sudo().search([('payment_type', '=', 'inbound')], limit=1)
            if not payment_method:
                _logger.error("Aucune méthode de paiement trouvée.")
                return False

            _logger.info(f"Méthode de paiement trouvée: {payment_method.name}")

            payment_method_line = request.env['account.payment.method.line'].sudo().search([
                ('payment_method_id', '=', payment_method.id),
                ('journal_id', '=', journal.id)
            ], limit=1)
            if not payment_method_line:
                _logger.error("Aucune ligne de méthode de paiement trouvée.")
                return False

            _logger.info(f"Ligne de méthode de paiement trouvée: {payment_method_line.id}")

            if order and order.state not in ['sale', 'done']:
                _logger.info(f"Confirmation de la commande {order.name}")
                order.action_confirm()


            currency_id = partner.currency_id.id or order.currency_id.id or journal.currency_id.id
            if not currency_id:
                _logger.error("Aucune devise trouvée pour la facture.")
                return False


            if order.amount_residual > 0:
                _logger.info(f"Création du paiement pour la commande {order.name}")
                account_payment = request.env['account.payment'].sudo().create({
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'partner_id': partner.id,
                    'amount': transaction.amount,
                    'journal_id': journal.id,
                    'currency_id': currency_id,
                    'payment_method_line_id': payment_method_line.id,
                    'payment_method_id': payment_method.id,
                    'ref': order.name,
                    'sale_id': order.id,
                    'is_reconciled': True,
                    'destination_account_id': partner.property_account_receivable_id.id,
                })
                account_payment.action_post()
                _logger.info(f"Paiement créé et validé pour la commande {order.name}")
            else:
                _logger.warning(f"Le montant résiduel de la commande {order.name} est de 0, aucun paiement créé.")

            _logger.info(f"Paiement et facture créés avec succès pour la transaction Orange Money {transaction.transaction_id}")
            return True
        except Exception as e:
            _logger.error(f"Erreur lors de la création du paiement Orange Money: {str(e)}")
            return False


  