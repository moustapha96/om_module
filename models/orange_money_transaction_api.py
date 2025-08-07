from odoo import models, fields, api

from odoo.exceptions import ValidationError
import logging
import base64
from datetime import datetime
import json
import requests

_logger = logging.getLogger(__name__)

class OrangeMoneyApiTransaction(models.Model):
    _name = 'orange.money.api.transaction'
    _description = 'Orange Money API Transactions'

    amount_unit = fields.Char(string='Unité de montant')
    amount_value = fields.Float(string='Valeur du montant')
    channel = fields.Char(string='Canal')
    created_at = fields.Datetime(string='Créé le')
    customer_msisdn = fields.Char(string='MSISDN du client')
    customer_id = fields.Char(string='ID du client')
    customer_id_type = fields.Char(string='Type d\'ID du client')
    customer_wallet_type = fields.Char(string='Type de portefeuille du client')
    metadata = fields.Text(string='Métadonnées')
    partner_id = fields.Char(string='ID du partenaire')
    partner_id_type = fields.Char(string='Type d\'ID du partenaire')
    partner_wallet_type = fields.Char(string='Type de portefeuille du partenaire')
    receive_notification = fields.Boolean(string='Recevoir une notification')
    reference = fields.Char(string='Référence')
    request_date = fields.Datetime(string='Date de la demande')
    status = fields.Char(string='Statut')
    status_reason = fields.Char(string='Raison du statut')
    transaction_id = fields.Char(string='ID de transaction', index=True)  # Index pour améliorer les performances de recherche
    type = fields.Char(string='Type')
    updated_at = fields.Datetime(string='Dernière modification')
    success_redirect_url = fields.Char(string='URL de redirection en cas de succès')
    cancel_redirect_url = fields.Char(string='URL de redirection en cas d\'annulation')
    order_id = fields.Char(string='ID de commande')
    success_url = fields.Char(string='URL de succès')
    description = fields.Char(string='Description')


    def fetch_all_transactions(self):
        """Récupérer toutes les transactions depuis l'API Orange Money"""
        try:
            config = self.env['orange.money.config'].search([('is_active', '=', True)], limit=1)
            if not config:
                raise Exception("Aucune configuration Orange Money active trouvée.")

            token = config._get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                f"{config.base_url}/api/eWallet/v1/transactions",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                transactions_data = response.json()
                for transaction_data in transactions_data:
                    amount = transaction_data.get('amount', {})
                    customer = transaction_data.get('customer', {})
                    partner = transaction_data.get('partner', {})
                    metadata = transaction_data.get('metadata', {})

                    # Fonction pour parser les dates
                    def parse_datetime(dt_str):
                        if dt_str:
                            return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                        return None

                    transaction_values = {
                        'amount_unit': amount.get('unit'),
                        'amount_value': amount.get('value'),
                        'channel': transaction_data.get('channel'),
                        'created_at': parse_datetime(transaction_data.get('createdAt')),
                        'customer_msisdn': customer.get('id'),
                        'customer_id': customer.get('id'),
                        'customer_id_type': customer.get('idType'),
                        'customer_wallet_type': customer.get('walletType'),
                        'metadata': json.dumps(metadata),
                        'partner_id': partner.get('id'),
                        'partner_id_type': partner.get('idType'),
                        'partner_wallet_type': partner.get('walletType'),
                        'receive_notification': transaction_data.get('receiveNotification', False),
                        'reference': transaction_data.get('reference'),
                        'request_date': parse_datetime(transaction_data.get('requestDate')),
                        'status': transaction_data.get('status'),
                        'status_reason': transaction_data.get('statusReason'),
                        'transaction_id': transaction_data.get('transactionId'),
                        'type': transaction_data.get('type'),
                        'updated_at': parse_datetime(transaction_data.get('updatedAt')),
                        'success_redirect_url': metadata.get('successRedirectUrl'),
                        'cancel_redirect_url': metadata.get('cancelRedirectUrl'),
                        'order_id': metadata.get('transaction_id'),
                        'success_url': metadata.get('success_url'),
                        'description': metadata.get('description')
                    }

                    existing_transaction = self.env['orange.money.api.transaction'].search([
                        ('transaction_id', '=', transaction_data.get('transactionId'))
                    ], limit=1)

                    if existing_transaction:
                        existing_transaction.write(transaction_values)
                    else:
                        self.env['orange.money.api.transaction'].create(transaction_values)

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Succès',
                        'message': 'Les transactions ont été récupérées avec succès.',
                        'type': 'success',
                    }
                }
            else:
                raise Exception(f"Erreur API Orange Money: {response.status_code} - {response.text}")
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des transactions: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Erreur',
                    'message': f'Erreur lors de la récupération des transactions: {str(e)}',
                    'type': 'danger',
                }
            }



    def action_fetch_transactions(self):
        """Action pour récupérer toutes les transactions depuis l'API Orange Money"""
        return self.fetch_all_transactions()