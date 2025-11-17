from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """ユーザーモデル"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # プレミアム会員関連
    is_premium = db.Column(db.Boolean, default=False)
    subscription_end_date = db.Column(db.DateTime, nullable=True)
    stripe_customer_id = db.Column(db.String(255), nullable=True)

    # 利用制限関連（無料ユーザー：1日5回まで）
    daily_usage_count = db.Column(db.Integer, default=0)
    last_usage_date = db.Column(db.Date, nullable=True)

    # その他
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # リレーションシップ
    saved_recipes = db.relationship('SavedRecipe', backref='user', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """パスワードをハッシュ化して保存"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """パスワードを検証"""
        return check_password_hash(self.password_hash, password)

    def can_use_service(self):
        """サービスを利用できるかチェック"""
        if self.is_premium:
            # プレミアムユーザーは期限をチェック
            if self.subscription_end_date and self.subscription_end_date > datetime.utcnow():
                return True
            else:
                # 期限切れの場合、プレミアムをfalseに
                self.is_premium = False
                db.session.commit()
                return self._check_free_usage()
        else:
            return self._check_free_usage()

    def _check_free_usage(self):
        """無料ユーザーの利用制限チェック"""
        today = datetime.utcnow().date()

        # 日付が変わっていたらカウントをリセット
        if self.last_usage_date != today:
            self.daily_usage_count = 0
            self.last_usage_date = today
            db.session.commit()

        # 1日5回まで
        return self.daily_usage_count < 5

    def increment_usage(self):
        """利用回数をインクリメント"""
        if not self.is_premium:
            today = datetime.utcnow().date()
            if self.last_usage_date != today:
                self.daily_usage_count = 1
                self.last_usage_date = today
            else:
                self.daily_usage_count += 1
            db.session.commit()

    def get_remaining_uses(self):
        """残り利用可能回数を取得"""
        if self.is_premium:
            return float('inf')  # 無制限
        else:
            today = datetime.utcnow().date()
            if self.last_usage_date != today:
                return 5
            return max(0, 5 - self.daily_usage_count)

    def upgrade_to_premium(self, months=1):
        """プレミアム会員にアップグレード"""
        self.is_premium = True
        if self.subscription_end_date and self.subscription_end_date > datetime.utcnow():
            # 既存の期限に追加
            self.subscription_end_date += timedelta(days=30 * months)
        else:
            # 新規または期限切れ
            self.subscription_end_date = datetime.utcnow() + timedelta(days=30 * months)
        db.session.commit()


class SavedRecipe(db.Model):
    """保存されたレシピ（お気に入り）"""
    __tablename__ = 'saved_recipes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipe_id = db.Column(db.String(50), nullable=False)
    recipe_title = db.Column(db.String(255))
    recipe_image_url = db.Column(db.String(500))
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 重複保存を防ぐためのユニーク制約
    __table_args__ = (db.UniqueConstraint('user_id', 'recipe_id', name='unique_user_recipe'),)


class Payment(db.Model):
    """支払い履歴"""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # 金額
    currency = db.Column(db.String(3), default='JPY')  # 通貨
    stripe_payment_id = db.Column(db.String(255))
    stripe_session_id = db.Column(db.String(255))
    subscription_type = db.Column(db.String(50))  # 'monthly' or 'yearly'
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.id}: {self.amount} {self.currency} - {self.status}>'
