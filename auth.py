from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """ユーザー登録"""
    if current_user.is_authenticated:
        return redirect(url_for('upload_file'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        # バリデーション
        if not username or not email or not password:
            flash('すべての項目を入力してください。', 'danger')
            return render_template('register.html')

        if password != password_confirm:
            flash('パスワードが一致しません。', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('パスワードは6文字以上にしてください。', 'danger')
            return render_template('register.html')

        # 既存ユーザーチェック
        if User.query.filter_by(username=username).first():
            flash('そのユーザー名は既に使用されています。', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('そのメールアドレスは既に登録されています。', 'danger')
            return render_template('register.html')

        # 新規ユーザー作成
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('登録が完了しました。ログインしてください。', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """ログイン"""
    if current_user.is_authenticated:
        return redirect(url_for('upload_file'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'ようこそ、{user.username}さん！', 'success')
            return redirect(next_page if next_page else url_for('upload_file'))
        else:
            flash('メールアドレスまたはパスワードが正しくありません。', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """ログアウト"""
    logout_user()
    flash('ログアウトしました。', 'info')
    return redirect(url_for('upload_file'))


@auth_bp.route('/profile')
@login_required
def profile():
    """プロフィールページ"""
    # 保存されたレシピ数を取得
    saved_recipes_count = len(current_user.saved_recipes)

    # サブスクリプション情報
    subscription_info = {
        'is_premium': current_user.is_premium,
        'end_date': current_user.subscription_end_date,
        'remaining_uses': current_user.get_remaining_uses()
    }

    return render_template('profile.html',
                         user=current_user,
                         saved_recipes_count=saved_recipes_count,
                         subscription_info=subscription_info)


@auth_bp.route('/saved-recipes')
@login_required
def saved_recipes():
    """保存されたレシピ一覧"""
    recipes = current_user.saved_recipes
    return render_template('saved_recipes.html', recipes=recipes)
