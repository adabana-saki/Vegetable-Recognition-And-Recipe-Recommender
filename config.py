import os
from datetime import timedelta

class Config:
    """アプリケーション設定"""

    # Flask基本設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'

    # データベース設定
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///vegetable_app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # セッション設定
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # アップロード設定
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # Stripe設定（本番環境では環境変数から取得）
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY') or 'pk_test_...'
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY') or 'sk_test_...'
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET') or 'whsec_...'

    # 価格設定（円）
    PRICING = {
        'monthly': {
            'price': 980,  # 月額980円
            'stripe_price_id': 'price_monthly_...',  # Stripeで作成した価格ID
            'name': '月額プラン',
            'features': ['無制限利用', '広告なし', 'レシピ保存機能', '優先サポート']
        },
        'yearly': {
            'price': 9800,  # 年額9,800円（2ヶ月分お得）
            'stripe_price_id': 'price_yearly_...',  # Stripeで作成した価格ID
            'name': '年額プラン',
            'features': ['無制限利用', '広告なし', 'レシピ保存機能', '優先サポート', '2ヶ月分お得']
        }
    }

    # 無料ユーザーの制限
    FREE_USER_DAILY_LIMIT = 5

    # アフィリエイト設定
    AFFILIATE_LINKS = {
        'amazon': {
            'enabled': True,
            'tag': 'your-amazon-tag-20',  # Amazonアソシエイトタグ
            'base_url': 'https://www.amazon.co.jp/s?k={keyword}&tag={tag}'
        },
        'rakuten': {
            'enabled': True,
            'affiliate_id': 'your-rakuten-id',  # 楽天アフィリエイトID
            'base_url': 'https://search.rakuten.co.jp/search/mall/{keyword}/'
        }
    }
