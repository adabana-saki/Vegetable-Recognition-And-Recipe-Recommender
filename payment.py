from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Payment
from config import Config
import stripe
import os

payment_bp = Blueprint('payment', __name__)

# Stripe設定
stripe.api_key = Config.STRIPE_SECRET_KEY


@payment_bp.route('/pricing')
def pricing():
    """価格表示ページ"""
    return render_template('pricing.html', pricing=Config.PRICING)


@payment_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Stripe Checkoutセッションを作成"""
    plan_type = request.form.get('plan_type')  # 'monthly' or 'yearly'

    if plan_type not in Config.PRICING:
        flash('無効なプランです。', 'danger')
        return redirect(url_for('payment.pricing'))

    plan = Config.PRICING[plan_type]

    try:
        # Stripeチェックアウトセッションを作成
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'jpy',
                        'product_data': {
                            'name': f'野菜認識アプリ - {plan["name"]}',
                            'description': ', '.join(plan['features']),
                        },
                        'unit_amount': plan['price'],
                        'recurring': {
                            'interval': 'month' if plan_type == 'monthly' else 'year',
                        },
                    },
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=url_for('payment.payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('payment.payment_cancel', _external=True),
            metadata={
                'user_id': current_user.id,
                'plan_type': plan_type
            }
        )

        return redirect(checkout_session.url, code=303)

    except Exception as e:
        flash(f'エラーが発生しました: {str(e)}', 'danger')
        return redirect(url_for('payment.pricing'))


@payment_bp.route('/payment-success')
@login_required
def payment_success():
    """支払い成功ページ"""
    session_id = request.args.get('session_id')

    if session_id:
        try:
            # Stripeセッション情報を取得
            session = stripe.checkout.Session.retrieve(session_id)

            # 支払い記録を作成
            plan_type = session.metadata.get('plan_type', 'monthly')
            payment = Payment(
                user_id=current_user.id,
                amount=Config.PRICING[plan_type]['price'],
                currency='JPY',
                stripe_session_id=session_id,
                subscription_type=plan_type,
                status='completed'
            )
            db.session.add(payment)

            # ユーザーをプレミアムにアップグレード
            months = 12 if plan_type == 'yearly' else 1
            current_user.upgrade_to_premium(months)

            db.session.commit()

            flash('お支払いが完了しました。プレミアム会員になりました！', 'success')
        except Exception as e:
            flash(f'エラーが発生しました: {str(e)}', 'danger')

    return render_template('payment_success.html')


@payment_bp.route('/payment-cancel')
def payment_cancel():
    """支払いキャンセルページ"""
    flash('お支払いがキャンセルされました。', 'info')
    return render_template('payment_cancel.html')


@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Stripe Webhookエンドポイント"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, Config.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400

    # イベント処理
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # 支払い完了処理（既にpayment_successで処理済み）
        pass
    elif event['type'] == 'customer.subscription.deleted':
        # サブスクリプションキャンセル時の処理
        subscription = event['data']['object']
        # ユーザーのプレミアムステータスを更新
        # （実装が必要な場合）
        pass

    return jsonify({'status': 'success'}), 200
