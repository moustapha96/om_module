from odoo import models, fields, api
import json
from odoo.exceptions import ValidationError
import logging
import base64
from datetime import datetime
import json

_logger = logging.getLogger(__name__)


import requests





class OrangeMoneyTransaction(models.Model):
    _name = 'orange.money.transaction'
    _description = 'Transaction Orange Money'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'created_at desc'
    _rec_name = 'reference'

    # Identifiants selon la documentation Orange Money
    transaction_id = fields.Char(
        string="Transaction ID",
        required=True,
        index=True,
        help="Identifiant unique de la transaction Orange Money",
        tracking=True
    )
    
    orange_id = fields.Char(
        string="Orange ID",
        help="Identifiant Orange Money (qrId)"
    )
    
    reference = fields.Char(
        string="Référence",
        required=True,
        index=True,
        help="Référence externe de la transaction (max 50 caractères)",
        tracking=True
    )
    
    callback_url = fields.Char(
        string='URL de notification',
        required=False,
        default='https://orbitcity.odoo.com/orange/webhook',
        help="URL pour les notifications webhook"
    )
    
    # Type de transaction selon la documentation
    transaction_type = fields.Selection([
        ('CASHIN', 'Cash In'),
        ('MERCHANT_PAYMENT', 'Paiement Marchand'),
        ('WEB_PAYMENT', 'Paiement Web'),
        ('QR_PAYMENT', 'Paiement QR Code')
    ], string='Type de transaction', default='MERCHANT_PAYMENT', required=True)


    # Informations de paiement
    amount = fields.Float(
        string="Montant",
        required=True,
        digits=(16, 2),
        help="Montant de la transaction",
        tracking=True
    )
    
    currency = fields.Selection([
        ('XOF', 'Franc CFA (XOF)'),
    ], string='Devise', default='XOF', required=True)
    
    # Informations client selon la documentation
    customer_msisdn = fields.Char(
        string="MSISDN Client",
        help="Numéro de téléphone du client (format: 771234567)"
    )
    
    # Informations partenaire/marchand
  

    merchant_code = fields.Char(
        string="Code Marchand",
        help="Code marchand à 6 chiffres"
    )

    # Statut selon la documentation Orange Money
    status = fields.Selection([
        ('INITIATED', 'Initié'),
        ('PRE_INITIATED', 'Pré-initié'),
        ('PENDING', 'En attente'),
        ('ACCEPTED', 'Accepté'),
        ('SUCCESS', 'Succès'),
        ('FAILED', 'Échoué'),
        ('CANCELLED', 'Annulé'),
        ('REJECTED', 'Rejeté')
    ], string='Statut', default='INITIATED', required=True, index=True, tracking=True)

    # Canal de paiement
    channel = fields.Selection([
        ('API', 'API'),
        ('USSD', 'USSD'),
        ('WEB', 'Web'),
        ('MOBILE', 'Mobile'),
        ('QRCODE', 'QR Code'),
        ('MAXIT', 'Maxit')
    ], string='Canal', default='API')
    

    # Méthode de paiement
    payment_method = fields.Selection([
        ('QRCODE', 'QR Code'),
        ('USSD', 'USSD'),
        ('WEB', 'Web'),
        ('MOBILE_APP', 'Application Mobile')
    ], string='Méthode de paiement', default='QRCODE')

    description = fields.Text(
        string="Description",
        help="Description de la transaction"
    )
    
    status_reason = fields.Char(
        string="Raison du statut",
        help="Raison détaillée du statut actuel"
    )

    # QR Code et liens
    qr_code_url = fields.Char(
        string="URL QR Code",
        help="URL du QR code pour le paiement"
    )
    
    qr_code_base64 = fields.Text(
        string="QR Code Base64",
        help="QR Code en format Base64"
    )
    
    qr_id = fields.Char(
        string="QR ID",
        help="Identifiant du QR code"
    )
    
    deep_link = fields.Char(
        string="Deep Link",
        help="Lien profond pour ouvrir l'application"
    )
    
    deep_link_om = fields.Char(
        string="Deep Link OM",
        help="Lien profond Orange Money"
    )
    
    deep_link_maxit = fields.Char(
        string="Deep Link Maxit",
        help="Lien profond Maxit"
    )
    
    short_link = fields.Char(
        string="Lien court",
        help="Lien court pour le paiement"
    )
    
    # Validité
    validity_seconds = fields.Integer(
        string="Validité (secondes)",
        default=3600,
        help="Durée de validité en secondes"
    )
    
    valid_from = fields.Datetime(
        string="Valide à partir de",
        help="Date de début de validité"
    )
    
    valid_until = fields.Datetime(
        string="Valide jusqu'à",
        help="Date de fin de validité"
    )

    # Métadonnées
    metadata = fields.Text(
        string="Métadonnées",
        help="Métadonnées JSON"
    )

    # Champs pour la facture
    url_facture = fields.Char(
        string="URL de la facture",
        help="URL vers le fichier PDF de la facture générée"
    )
    
    facture_pdf = fields.Binary(
        string="Facture PDF",
        help="Fichier PDF de la facture"
    )
    
    facture_filename = fields.Char(
        string="Nom du fichier facture",
        help="Nom du fichier PDF de la facture"
    )
    
    facture_generated_at = fields.Datetime(
        string="Date de génération de la facture",
        help="Date à laquelle la facture a été générée"
    )
    
    facture_size = fields.Integer(
        string="Taille de la facture",
        help="Taille du fichier PDF de la facture en octets"
    )

    # Réponses API
    orange_response = fields.Text(
        string="Réponse Orange Money",
        help="Réponse complète de l'API Orange Money"
    )
    
    webhook_data = fields.Text(
        string="Données Webhook",
        help="Dernières données reçues via webhook"
    )

    # Relations Odoo
    order_id = fields.Many2one(
        'sale.order',
        string="Commande liée",
        help="Commande de vente associée à cette transaction",
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string="Client",
        help="Client associé à cette transaction",
        tracking=True
    )

    # Dates selon la documentation
    created_at = fields.Datetime(
        string="Date de création",
        default=fields.Datetime.now,
        required=True,
        readonly=True
    )
    
    updated_at = fields.Datetime(
        string="Dernière mise à jour",
        default=fields.Datetime.now,
        readonly=True
    )
    
    completed_at = fields.Datetime(
        string="Date de completion",
        readonly=True,
        help="Date à laquelle la transaction a été complétée",
        tracking=True
    )

    # Champs calculés
    status_color = fields.Integer(
        string="Couleur du statut",
        compute='_compute_status_color',
        store=False
    )
    
    formatted_amount = fields.Char(
        string="Montant formaté",
        compute='_compute_formatted_amount',
        store=False
    )
    
    has_qr_code = fields.Boolean(
        string="A un QR Code",
        compute='_compute_has_qr_code',
        store=False
    )
    pay_token = fields.Char(
        string="Pay Token",
        help="Token de paiement unique pour la transaction"
    )
  
    payment_url = fields.Char(
        string="URL de Paiement",
        help="URL de paiement pour la transaction"
    )

    success_url = fields.Char(
        string='URL de succès',
        required=True,
        default='https://www.ccbmshop.sn/',
        help="URL de redirection en cas de paiement réussi"
    )
    
    cancel_url = fields.Char(
        string='URL d\'annulation',
        required=False,
        default='https://www.ccbmshop.sn/',
        help="URL de redirection en cas d'annulation"
    )


    customer_id = fields.Char(string='ID du client',  required=False, index=True)

    customer_id_type = fields.Char(string='Type d\'ID du client',  required=False, index=True)

    partnerId = fields.Char(string='ID du partenaire',  required=False, index=True)

    partnerId_type = fields.Char(string='Type d\'ID du partenaire',  required=False, index=True)

    transactionId = fields.Char(string='ID de transaction Orange Money', required=False, index=True)


    @api.depends('status')
    def _compute_status_color(self):
        """Calculer la couleur selon le statut Orange Money"""
        color_map = {
            'INITIATED': 4,      # Bleu
            'PRE_INITIATED': 4,  # Bleu
            'PENDING': 4,        # Bleu
            'ACCEPTED': 9,       # Violet
            'SUCCESS': 10,       # Vert
            'FAILED': 1,         # Rouge
            'CANCELLED': 3,      # Jaune
            'REJECTED': 1,       # Rouge
        }
        for record in self:
            record.status_color = color_map.get(record.status, 0)

    @api.depends('amount', 'currency')
    def _compute_formatted_amount(self):
        """Formater le montant avec la devise"""
        for record in self:
            if record.currency == 'XOF':
                record.formatted_amount = f"{record.amount:,.0f} FCFA"
            else:
                record.formatted_amount = f"{record.amount:,.2f} {record.currency}"


    @api.depends('qr_code_base64', 'qr_code_url', 'deep_link')
    def _compute_has_qr_code(self):
        """Vérifier si la transaction a un QR code"""
        for record in self:
            record.has_qr_code = bool(record.qr_code_base64 or record.qr_code_url or record.deep_link)



    @api.model
    def create(self, vals):
        """Surcharger la méthode create pour appeler une fonction personnalisée après la création"""
        record = super(OrangeMoneyTransaction, self).create(vals)
        self.fetch_all_transactions()
        return record


    def write(self, vals):
        """Surcharger la méthode write pour appeler une fonction personnalisée après la mise à jour"""
        result = super(OrangeMoneyTransaction, self).write(vals)
        self.fetch_all_transactions()
        return result





    def write(self, vals):
        """Surcharger write pour mettre à jour la date de modification"""
        if 'status' in vals:
            vals['updated_at'] = fields.Datetime.now()
            
            # Si le statut passe à 'SUCCESS', enregistrer la date
            if vals.get('status') == 'SUCCESS' and self.status != 'SUCCESS':
                vals['completed_at'] = fields.Datetime.now()
                # Poster un message dans le chatter
                self.message_post(
                    body=f"Transaction complétée avec succès. Montant: {self.formatted_amount}",
                    message_type='notification'
                )
        
        return super().write(vals)


    @api.model
    def create(self, vals):
        """Surcharger create pour ajouter des validations"""
        # Vérifier l'unicité du transaction_id
        if vals.get('transaction_id'):
            existing = self.search([('transaction_id', '=', vals['transaction_id'])])
            if existing:
                raise ValidationError(f"Une transaction avec l'ID '{vals['transaction_id']}' existe déjà.")
        
        config = self.env['orange.money.config'].sudo().search([('is_active', '=', True)], limit=1)
        if config:
            vals['merchant_code'] = config.merchant_code

        record = super().create(vals)
        
        # Poster un message de création
        record.message_post(
            body=f"Transaction Orange Money créée pour un montant de {record.formatted_amount}",
            message_type='notification'
        )
        
        return record


    def action_refresh_status(self):
        """Action pour rafraîchir le statut depuis Orange Money"""
        try:
            config = self.env['orange.money.config'].search([('is_active', '=', True)], limit=1)
            if not config:
                raise ValidationError("Aucune configuration Orange Money active trouvée.")

            # Utilisez l'ID de la transaction correct
            transaction_id = self.transactionId
            if not transaction_id:
                raise ValidationError("L'ID de transaction est requis pour vérifier le statut.")
            
            status_data = config.get_transaction_status(transaction_id)

            if status_data:
                status = status_data.get('status', '').upper()

                if status and status != self.status:
                    old_status = self.status
                    self.write({
                        'status': status,
                        'orange_response': json.dumps(status_data),
                        'status_reason': status_data.get('statusReason', ''),
                    })

                    # Poster un message de changement de statut
                    self.message_post(
                        body=f"Statut mis à jour de '{old_status}' vers '{status}'",
                        message_type='notification'
                    )

                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Statut mis à jour',
                            'message': f'Le statut a été mis à jour: {status}',
                            'type': 'success',
                        }
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Aucun changement',
                            'message': f'Le statut est déjà à jour: {self.status}',
                            'type': 'info',
                        }
                    }
            else:
                raise ValidationError("Impossible de récupérer les données de statut Orange Money")

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Erreur',
                    'message': f'Erreur lors de la mise à jour: {str(e)}',
                    'type': 'danger',
                }
            }


    def action_view_order(self):
        """Action pour ouvrir la commande associée"""
        self.ensure_one()
        if self.order_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Commande',
                'res_model': 'sale.order',
                'res_id': self.order_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Aucune commande',
                    'message': 'Aucune commande associée à cette transaction.',
                    'type': 'warning',
                }
            }
    
    def action_view_partner(self):
        """Action pour ouvrir le partner associé"""
        self.ensure_one()
        if self.partner_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Client',
                'res_model': 'res.partner',
                'res_id': self.partner_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Aucun client',
                    'message': 'Aucune client associée à cette transaction.',
                    'type': 'warning',
                }
            }

    _sql_constraints = [
        ('transaction_id_unique', 'UNIQUE(transaction_id)', 'L\'ID de transaction doit être unique.'),
    ]


    @api.model
    def check_status(self, transactionId=None):
        """Vérifier le statut d'une transaction en fonction de l'ID de transaction"""
        try:

            transactionId = transactionId or self.transaction_id

            config = self.env['orange.money.config'].sudo().search([('is_active', '=', True)], limit=1)
            if not config:
                return self._make_response({'success': False, 'error': 'Orange Money configuration not found'}, 400)

            if not transactionId:
                return None

            api_response = config.get_transaction_status(transactionId)

            if not api_response:
                _logger.error(f"Aucune transaction API trouvée avec l'order_id: {transactionId}")
                return None

            self.write({'status': api_response.status, 'webhook_data': api_response.metadata})

            # Renvoyer le statut de la transaction API
            return api_response.status

        except Exception as e:
            _logger.error(f"Erreur lors de la vérification du statut: {str(e)}")
            return None
        
    

    def action_check_status(self):
        """Vérifier le statut d'une transaction en fonction de l'ID de transaction"""
        try:
           
            transactionId = self.transactionId or self.transaction_id

            config = self.env['orange.money.config'].sudo().search([('is_active', '=', True)], limit=1)
            if not config:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Erreur',
                        'message': f'Merci de configurer Orange Money dans les paramètres.',
                        'type': 'danger',
                    }
                }
            
            api_response = config.get_transaction_status(transactionId)

            if not api_response:
                _logger.error(f"Aucune transaction API trouvée avec l'order_id: {transactionId}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Erreur',
                        'message': f'Aucune transaction trouvée avec l\'ID: {transactionId}',
                        'type': 'danger',
                    }
                }
            
            # Renvoyer le statut de la transaction API et afficher une notification de succès
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Succès',
                    'message': f'Le statut de la transaction a été vérifié \n Statut: {self.status}',
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la vérification du statut: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Erreur',
                    'message': f'Erreur lors de la vérification du statut: {str(e)}',
                    'type': 'danger',
                }
            }
   

    def _generate_invoice_pdf(self):
        """Générer la facture PDF pour la transaction"""
        try:
            _logger.info(f"Génération de la facture PDF pour la transaction {self.transaction_id}")
            # Créer le contenu HTML de la facture
            html_content = self._get_invoice_html_content()
            # Générer le PDF à partir du HTML
            pdf_content = self._html_to_pdf(html_content)
            if pdf_content:
                # Générer le nom du fichier
                filename = f"facture_orange_{self.transaction_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                # Encoder le PDF en base64
                pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                # Créer un attachement
                attachment = self.env['ir.attachment'].create({
                    'name': filename,
                    'type': 'binary',
                    'datas': pdf_base64,
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/pdf',
                    'public': True,  # Rendre accessible publiquement
                })
                # Construire l'URL d'accès
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                url_facture = f"{base_url}/web/content/{attachment.id}?download=true"
                # Mettre à jour les champs de la transaction
                self.write({
                    'facture_pdf': pdf_base64,
                    'facture_filename': filename,
                    'url_facture': url_facture,
                    'facture_generated_at': fields.Datetime.now(),
                    'facture_size': len(pdf_content)
                })
                # Enregistrer automatiquement les informations
                self._auto_save_invoice_info()
                _logger.info(f"Facture PDF générée avec succès: {url_facture}")
                return url_facture
            else:
                _logger.error("Erreur lors de la génération du PDF")
                return False
        except Exception as e:
            _logger.error(f"Erreur lors de la génération de la facture PDF: {str(e)}")
            return False

    def _get_invoice_html_content(self):
        """Générer le contenu HTML de la facture avec le logo CCBM"""
        # Récupérer les informations de l'entreprise
        company = self.env.company
        # Formatage de la date
        date_facture = self.completed_at.strftime('%d/%m/%Y %H:%M:%S') if self.completed_at else datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8"/>
            <title>Facture Orange Money - {self.reference}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #2879b9; padding-bottom: 20px; }}
                .company-section {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; }}
                .company-info {{ flex: 1; text-align: left; }}
                .company-logo {{ flex: 0 0 200px; text-align: right; }}
                .company-logo img {{ max-width: 180px; max-height: 120px; object-fit: contain; }}
                .invoice-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .transaction-details {{ margin-bottom: 20px; }}
                .table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                .table th, .table td {{ border: 1px solid #dee2e6; padding: 8px; text-align: left; }}
                .table th {{ background-color: #2879b9; color: white; }}
                .total {{ font-size: 18px; font-weight: bold; text-align: right; margin-top: 20px; }}
                .footer {{ margin-top: 40px; text-align: center; font-size: 12px; color: #6c757d; }}
                .status-success {{ color: #28a745; font-weight: bold; }}
                .ccbm-branding {{ color: #2879b9; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header"
                style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #2879b9; padding-bottom: 20px; margin-bottom: 30px;">
                <div style="text-align: left;">
                    <h2 class="ccbm-branding" style="margin: 0;">FACTURE DE PAIEMENT</h2>
                    <h3 style="margin: 5px 0 0;">Référence: {self.reference}</h3>
                </div>
                <div class="company-logo" style="text-align: right;">
                    <img src="https://ccbmshop.sn/logo.png" alt="CCBM Shop Logo"
                        style="max-width: 180px; max-height: 120px; object-fit: contain;" onerror="this.style.display='none'" />
                </div>
            </div>

            <div class="company-section" style="display: flex; justify-content: space-between; align-items: center; gap: 20px;">
                <div class="company-info">
                    <h3 class="ccbm-branding">CCBM SHOP</h3>
                    <p><strong>Adresse:</strong> {company.street or 'Dakar, Sénégal'}</p>
                    <p><strong>Ville:</strong> {company.city or 'Dakar'}, {company.country_id.name or 'Sénégal'}</p>
                    <p><strong>Téléphone:</strong> {company.phone or '70 922 17 75 | 70 843 04 36'}</p>
                    <p><strong>Email:</strong> {company.email or 'shop@ccbm.sn'}</p>
                    <p><strong>Site Web:</strong> www.ccbmshop.sn</p>
                </div>
            </div>
            <div class="invoice-info">
                <h3>Informations de la facture</h3>
                <p><strong>Numéro de facture:</strong> ORANGE-{self.id:06d}</p>
                <p><strong>Date de paiement:</strong> {date_facture}</p>
                <p><strong>Statut:</strong> <span class="status-success">PAYÉ</span></p>
                <p><strong>Mode de paiement:</strong> Orange Money</p>
            </div>
            <div class="transaction-details">
                <h3>Détails de la transaction</h3>
                <table class="table">
                    <tr>
                        <th>Transaction ID</th>
                        <td>{self.transaction_id}</td>
                    </tr>
                    <tr>
                        <th>Orange ID</th>
                        <td>{self.orange_id}</td>
                    </tr>
                    <tr>
                        <th>Téléphone</th>
                        <td>{self.customer_msisdn or 'N/A'}</td>
                    </tr>
                    <tr>
                        <th>Description</th>
                        <td>{self.description or 'Paiement via Orange Money'}</td>
                    </tr>
        """
        # Ajouter les détails de la commande si elle existe
        if self.order_id:
            html_content += f"""
                    <tr>
                        <th>Commande liée</th>
                        <td>{self.order_id.name}</td>
                    </tr>
            """
        # Ajouter les détails du client si il existe
        if self.partner_id:
            html_content += f"""
                    <tr>
                        <th>Client</th>
                        <td>{self.partner_id.name}</td>
                    </tr>
                    <tr>
                        <th>Email Client</th>
                        <td>{self.partner_id.email or 'N/A'}</td>
                    </tr>
            """
        html_content += f"""
                </table>
            </div>
            <div class="total">
                <p>MONTANT TOTAL PAYÉ: <span class="ccbm-branding">{self.formatted_amount}</span></p>
            </div>
            <div class="footer">
                <p><strong class="ccbm-branding">CCBM SHOP</strong> </p>
                <p style="margin-top: 15px;">
                    <strong>Contacts:</strong> 70 922 17 75 | 70 843 04 36<br>
                    <strong>Email:</strong> contact@ccbm.sn | <strong>Web:</strong> www.ccbmshop.sn
                </p>
            </div>
        </body>
        </html>
        """
        return html_content

    def _html_to_pdf(self, html_content):
        """Convertir le HTML en PDF"""
        try:
            # Utiliser wkhtmltopdf via Odoo
            return self.env['ir.actions.report']._run_wkhtmltopdf(
                [html_content],
                landscape=False,
                specific_paperformat_args={
                    'data-report-margin-top': 10,
                    'data-report-margin-bottom': 10,
                    'data-report-margin-left': 10,
                    'data-report-margin-right': 10,
                    'data-report-page-size': 'A4',
                }
            )
        except Exception as e:
            _logger.error(f"Erreur lors de la conversion HTML vers PDF: {str(e)}")
            return False

    def _auto_save_invoice_info(self):
        """Enregistrer automatiquement les informations après génération de la facture"""
        try:
            _logger.info(f"Enregistrement automatique des informations pour la transaction {self.transaction_id}")
            # Créer un enregistrement dans un modèle de log ou historique
            invoice_log_data = {
                'transaction_id': self.transaction_id,
                'orange_id': self.orange_id,
                'reference': self.reference,
                'amount': self.amount,
                'currency': self.currency,
                'phone': self.customer_msisdn,
                'partner_name': self.partner_id.name if self.partner_id else 'N/A',
                'order_name': self.order_id.name if self.order_id else 'N/A',
                'facture_url': self.url_facture,
                'facture_filename': self.facture_filename,
                'facture_size': self.facture_size,
                'generated_at': self.facture_generated_at,
                'status': 'completed'
            }
            # Enregistrer dans les logs système
            _logger.info(f"Facture générée et enregistrée: {json.dumps(invoice_log_data, default=str)}")
            # Optionnel: Envoyer une notification ou email
            self._send_invoice_notification()
            return True
        except Exception as e:
            _logger.error(f"Erreur lors de l'enregistrement automatique: {str(e)}")
            return False

    def _send_invoice_notification(self):
        """Envoyer une notification après génération de la facture"""
        try:
            if self.partner_id and self.partner_id.email:
                # Créer le message email
                body_html = f"""
                    <p>Bonjour {self.partner_id.name},</p>
                    <p>Votre paiement Orange Money a été traité avec succès.</p>
                    <p><strong>Détails:</strong></p>
                    <ul>
                        <li>Transaction ID: {self.transaction_id}</li>
                        <li>Montant: {self.formatted_amount}</li>
                        <li>Date: {self.completed_at.strftime('%d/%m/%Y %H:%M:%S') if self.completed_at else 'N/A'}</li>
                    </ul>
                    <p>Vous pouvez télécharger votre facture <a href="{self.url_facture}">ici</a>.</p>
                    <p>Merci pour votre confiance,<br>L'équipe CCBM SHOP</p>
                """
                sujet = f'Facture Orange Money - {self.reference}'
                # Envoyer l'email
                mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
                email_from = mail_server.smtp_user
                if not email_from:
                    email_from = 'ccbmtech@ccbm.sn'
                additional_email = 'shop@ccbm.sn'
                email_to = f'{self.partner_id.email}, {additional_email}'
                email_values = {
                    'email_from': email_from,
                    'email_to': email_to,
                    'subject': sujet,
                    'body_html': body_html,
                    'state': 'outgoing',
                }
                mail_mail = self.env['mail.mail'].sudo().create(email_values)
                try:
                    mail_mail.send()
                    return True
                except Exception as e:
                    return False
            return False
        except Exception as e:
            _logger.error(f"Erreur lors de l'envoi de la notification: {str(e)}")
            return False
        

    def action_download_invoice(self):
        """Action pour télécharger la facture PDF"""
        if self.facture_pdf:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content?model={self._name}&id={self.id}&field=facture_pdf&filename_field=facture_filename&download=true',
                'target': 'self',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Aucune facture',
                    'message': 'Aucune facture disponible pour cette transaction.',
                    'type': 'warning',
                }
            }

    def action_view_invoice_url(self):
        """Action pour ouvrir l'URL de la facture"""
        if self.url_facture:
            return {
                'type': 'ir.actions.act_url',
                'url': self.url_facture,
                'target': 'new',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Aucune facture',
                    'message': 'Aucune URL de facture disponible pour cette transaction.',
                    'type': 'warning',
                }
            }

    def action_regenerate_invoice(self):
        """Action pour régénérer la facture manuellement"""
        if self.status == 'SUCCESS':
            try:
                url_facture = self._generate_invoice_pdf()
                if url_facture:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Facture régénérée',
                            'message': f'La facture a été régénérée avec succès: {url_facture}',
                            'type': 'success',
                        }
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Erreur',
                            'message': 'Erreur lors de la régénération de la facture.',
                            'type': 'danger',
                        }
                    }
            except Exception as e:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Erreur',
                        'message': f'Erreur lors de la régénération: {str(e)}',
                        'type': 'danger',
                    }
                }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Transaction non complétée',
                    'message': 'La facture ne peut être générée que pour les transactions complétées.',
                    'type': 'warning',
                }
            }

    def action_view_payment_link(self):
        """Action pour ouvrir le lien de paiement"""
        if self.payment_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.payment_url,
                'target': 'new',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Aucun lien de paiement',
                    'message': 'Aucun lien de paiement disponible pour cette transaction.',
                    'type': 'warning',
                }
            }
   