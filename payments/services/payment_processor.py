"""
Payment Processor Service
Handles payment processing logic and integration with WiFi billing system
"""

import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User

from ..models import PaymentTransaction, STKPushRequest, PaymentCallback
from billing.models import WifiUser, WifiPlan
from .kcb_client import kcb_client, KCBBuniError

logger = logging.getLogger(__name__)


class PaymentProcessor:
    """
    Handles payment processing workflow:
    1. Create payment transaction
    2. Initiate STK Push
    3. Handle callback responses
    4. Update user accounts
    """
    
    def __init__(self):
        self.kcb_client = kcb_client
    
    def create_payment_transaction(self, user: WifiUser, plan: WifiPlan, 
                                 phone_number: str, payment_method: str = 'kcb_buni',
                                 processed_by: User = None) -> PaymentTransaction:
        """
        Create a new payment transaction record
        
        Args:
            user: WiFi user making the payment
            plan: WiFi plan being purchased
            phone_number: Payment phone number
            payment_method: Payment method used
            processed_by: Admin user processing (if applicable)
            
        Returns:
            PaymentTransaction: Created transaction record
        """
        logger.info(f"Creating payment transaction for user {user.phone_number}, plan: {plan.name}")
        
        # Create transaction record
        transaction_record = PaymentTransaction.objects.create(
            user=user,
            plan=plan,
            amount=plan.price,
            phone_number=phone_number,
            payment_method=payment_method,
            processed_by=processed_by,
            status='pending'
        )
        
        logger.info(f"Payment transaction created: {transaction_record.transaction_id}")
        return transaction_record
    
    def initiate_stk_payment(self, payment_transaction: PaymentTransaction) -> Dict[str, Any]:
        """
        Initiate STK Push payment for a transaction
        
        Args:
            payment_transaction: Payment transaction to process
            
        Returns:
            Dict containing STK push result
        """
        logger.info(f"Initiating STK payment for transaction: {payment_transaction.transaction_id}")
        
        try:
            # Update transaction status to processing
            payment_transaction.status = 'processing'
            payment_transaction.save()
            
            # Initiate STK Push
            stk_response = self.kcb_client.initiate_stk_push(
                phone_number=payment_transaction.phone_number,
                amount=float(payment_transaction.amount),
                invoice_number=payment_transaction.transaction_id,
                account_reference=payment_transaction.user.mikrotik_username
            )
            
            # Create STK Push request record
            stk_request = STKPushRequest.objects.create(
                transaction=payment_transaction,
                checkout_request_id=stk_response.get('CheckoutRequestID', ''),
                merchant_request_id=stk_response.get('MerchantRequestID', ''),
                phone_number=payment_transaction.phone_number,
                amount=payment_transaction.amount,
                status='sent',
                provider_response=stk_response
            )
            
            # Update transaction with provider response
            payment_transaction.provider_response = stk_response
            payment_transaction.save()
            
            logger.info(f"STK Push initiated successfully for transaction: {payment_transaction.transaction_id}")
            
            return {
                'success': True,
                'transaction_id': payment_transaction.transaction_id,
                'checkout_request_id': stk_response.get('CheckoutRequestID'),
                'message': 'Payment request sent to your phone. Please enter your M-Pesa PIN to complete the payment.',
                'stk_request_id': str(stk_request.id)
            }
            
        except KCBBuniError as e:
            logger.error(f"STK Push failed for transaction {payment_transaction.transaction_id}: {str(e)}")
            
            # Update transaction status
            payment_transaction.status = 'failed'
            payment_transaction.failure_reason = str(e)
            payment_transaction.save()
            
            return {
                'success': False,
                'transaction_id': payment_transaction.transaction_id,
                'message': f'Payment initiation failed: {str(e)}',
                'error_code': e.error_code
            }
        
        except Exception as e:
            logger.error(f"Unexpected error initiating STK Push: {str(e)}")
            
            payment_transaction.status = 'failed'
            payment_transaction.failure_reason = f'System error: {str(e)}'
            payment_transaction.save()
            
            return {
                'success': False,
                'transaction_id': payment_transaction.transaction_id,
                'message': 'Payment system error. Please try again later.'
            }
    
    def process_wifi_plan_purchase(self, user: WifiUser, plan: WifiPlan, 
                                 phone_number: str, processed_by: User = None) -> Dict[str, Any]:
        """
        Complete workflow for WiFi plan purchase
        
        Args:
            user: WiFi user purchasing plan
            plan: WiFi plan to purchase
            phone_number: Payment phone number
            processed_by: Admin user (if processed by admin)
            
        Returns:
            Dict containing purchase result
        """
        logger.info(f"Processing WiFi plan purchase: User {user.phone_number}, Plan: {plan.name}")
        
        try:
            with transaction.atomic():
                # Create payment transaction
                payment_transaction = self.create_payment_transaction(
                    user=user,
                    plan=plan,
                    phone_number=phone_number,
                    processed_by=processed_by
                )
                
                # Initiate STK Push payment
                stk_result = self.initiate_stk_payment(payment_transaction)
                
                if stk_result['success']:
                    return {
                        'success': True,
                        'transaction_id': payment_transaction.transaction_id,
                        'checkout_request_id': stk_result.get('checkout_request_id'),
                        'message': stk_result['message'],
                        'payment_status': 'processing',
                        'next_steps': 'Complete payment on your phone to activate your WiFi plan.'
                    }
                else:
                    return stk_result
                    
        except Exception as e:
            logger.error(f"Error processing WiFi plan purchase: {str(e)}")
            return {
                'success': False,
                'message': f'Purchase processing failed: {str(e)}'
            }
    
    def handle_payment_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process payment callback from KCB Buni
        
        Args:
            callback_data: Raw callback data from KCB Buni
            
        Returns:
            Dict containing processing result
        """
        logger.info("Processing payment callback from KCB Buni")
        
        try:
            # Validate callback data
            is_valid, error_message = self.kcb_client.validate_callback_data(callback_data)
            if not is_valid:
                logger.error(f"Invalid callback data: {error_message}")
                return {'success': False, 'message': error_message}
            
            # Parse callback data
            parsed_data = self.kcb_client.parse_callback_data(callback_data)
            checkout_request_id = parsed_data['checkout_request_id']
            result_code = parsed_data['result_code']
            
            logger.info(f"Processing callback for CheckoutRequestID: {checkout_request_id}, ResultCode: {result_code}")
            
            # Find STK Push request
            try:
                stk_request = STKPushRequest.objects.get(checkout_request_id=checkout_request_id)
                payment_transaction = stk_request.transaction
            except STKPushRequest.DoesNotExist:
                logger.error(f"STK Push request not found for CheckoutRequestID: {checkout_request_id}")
                return {'success': False, 'message': 'Transaction not found'}
            
            # Create callback record
            PaymentCallback.objects.create(
                transaction=payment_transaction,
                callback_type='payment_confirmation',
                callback_data=callback_data
            )
            
            # Process payment result
            with transaction.atomic():
                # Update STK request
                stk_request.result_code = str(result_code)
                stk_request.result_desc = parsed_data['result_desc']
                stk_request.callback_response = callback_data
                
                if result_code == 0:  # Success
                    stk_request.status = 'accepted'
                    payment_transaction.status = 'completed'
                    payment_transaction.completed_at = timezone.now()
                    payment_transaction.external_transaction_id = parsed_data['callback_metadata'].get('mpesa_receipt_id', '')
                    
                    # Activate user's WiFi plan
                    self._activate_wifi_plan(payment_transaction)
                    
                    logger.info(f"Payment completed successfully for transaction: {payment_transaction.transaction_id}")
                    
                else:  # Failed or cancelled
                    if result_code == 1032:  # User cancelled
                        stk_request.status = 'cancelled'
                        payment_transaction.status = 'cancelled'
                        payment_transaction.failure_reason = 'User cancelled payment'
                    else:  # Other failure
                        stk_request.status = 'failed'
                        payment_transaction.status = 'failed'
                        payment_transaction.failure_reason = parsed_data['result_desc']
                    
                    logger.info(f"Payment failed/cancelled for transaction: {payment_transaction.transaction_id}")
                
                stk_request.save()
                payment_transaction.save()
            
            return {
                'success': True,
                'transaction_id': payment_transaction.transaction_id,
                'status': payment_transaction.status,
                'message': 'Callback processed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error processing payment callback: {str(e)}")
            return {
                'success': False,
                'message': f'Callback processing failed: {str(e)}'
            }
    
    def _activate_wifi_plan(self, payment_transaction: PaymentTransaction):
        """
        Activate WiFi plan for user after successful payment
        
        Args:
            payment_transaction: Completed payment transaction
        """
        user = payment_transaction.user
        plan = payment_transaction.plan
        
        logger.info(f"Activating WiFi plan for user: {user.phone_number}")
        
        try:
            # Calculate plan expiry
            if plan.duration_minutes:
                expiry_time = timezone.now() + timezone.timedelta(minutes=plan.duration_minutes)
            else:
                # Default to 30 days if no duration specified
                expiry_time = timezone.now() + timezone.timedelta(days=30)
            
            # Update user account
            user.current_plan = plan
            user.plan_activated_at = timezone.now()
            user.plan_expires_at = expiry_time
            user.status = 'active'
            
            # Reset data usage if plan has data limit
            if plan.data_limit_mb:
                user.data_used_mb = 0
            
            user.save()
            
            logger.info(f"WiFi plan activated for user: {user.phone_number}, expires at: {expiry_time}")
            
            # TODO: Integrate with MikroTik to enable user access
            # This would call your MikroTik integration to:
            # - Create/update user in MikroTik
            # - Set bandwidth limits
            # - Enable access
            
        except Exception as e:
            logger.error(f"Error activating WiFi plan: {str(e)}")
            raise
    
    def query_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Query current payment status for a transaction
        
        Args:
            transaction_id: Transaction ID to query
            
        Returns:
            Dict containing payment status
        """
        try:
            payment_transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
            
            result = {
                'transaction_id': transaction_id,
                'status': payment_transaction.status,
                'amount': float(payment_transaction.amount),
                'plan': payment_transaction.plan.name,
                'created_at': payment_transaction.created_at.isoformat(),
                'user_phone': payment_transaction.user.phone_number
            }
            
            if payment_transaction.completed_at:
                result['completed_at'] = payment_transaction.completed_at.isoformat()
            
            if payment_transaction.failure_reason:
                result['failure_reason'] = payment_transaction.failure_reason
            
            # If payment is still processing, try to query KCB Buni for status
            if payment_transaction.status == 'processing' and hasattr(payment_transaction, 'stk_request'):
                try:
                    stk_status = self.kcb_client.query_stk_status(
                        payment_transaction.stk_request.checkout_request_id
                    )
                    result['stk_status'] = stk_status
                except KCBBuniError as e:
                    logger.warning(f"Failed to query STK status: {str(e)}")
            
            return {
                'success': True,
                'data': result
            }
            
        except PaymentTransaction.DoesNotExist:
            return {
                'success': False,
                'message': 'Transaction not found'
            }
        except Exception as e:
            logger.error(f"Error querying payment status: {str(e)}")
            return {
                'success': False,
                'message': f'Status query failed: {str(e)}'
            }
    
    def retry_failed_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Retry a failed payment transaction
        
        Args:
            transaction_id: Transaction ID to retry
            
        Returns:
            Dict containing retry result
        """
        try:
            payment_transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
            
            if not payment_transaction.can_retry:
                return {
                    'success': False,
                    'message': f'Transaction cannot be retried. Current status: {payment_transaction.status}'
                }
            
            # Reset transaction status
            payment_transaction.status = 'pending'
            payment_transaction.failure_reason = ''
            payment_transaction.save()
            
            # Retry STK Push
            return self.initiate_stk_payment(payment_transaction)
            
        except PaymentTransaction.DoesNotExist:
            return {
                'success': False,
                'message': 'Transaction not found'
            }
        except Exception as e:
            logger.error(f"Error retrying payment: {str(e)}")
            return {
                'success': False,
                'message': f'Payment retry failed: {str(e)}'
            }


# Singleton instance
payment_processor = PaymentProcessor()