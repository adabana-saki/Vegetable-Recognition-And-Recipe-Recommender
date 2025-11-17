# マネタイズ機能 実装ガイド

## 概要

野菜認識アプリに包括的なマネタイズ機能を実装しました。このドキュメントでは、実装された機能と使用方法について説明します。

## 実装された主要機能

### 1. ユーザー認証システム

- **新規登録**: `/auth/register`
- **ログイン**: `/auth/login`
- **ログアウト**: `/auth/logout`
- **プロフィール**: `/auth/profile`

### 2. プレミアム会員制度（Freemiumモデル）

#### 無料会員
- 1日5回まで野菜認識を利用可能
- 基本的なレシピ推薦機能
- 広告表示あり

#### プレミアム会員
- **月額プラン**: ¥980/月
- **年額プラン**: ¥9,800/年（2ヶ月分お得）

特典:
- 無制限で利用可能
- 広告なし
- レシピ保存機能（お気に入り）
- 優先サポート

### 3. 決済システム（Stripe統合）

- クレジットカード決済に対応
- サブスクリプション管理
- 支払い履歴の記録
- Webhook対応で自動更新

### 4. レシピ保存機能

- お気に入りレシピの保存
- 保存したレシピ一覧の閲覧
- ワンクリックで保存/解除

### 5. アフィリエイトマーケティング

- Amazon アソシエイト統合
- 楽天アフィリエイト統合
- レシピページに食材購入リンクを表示

## データベース構造

### Userテーブル
```python
- id: ユーザーID（主キー）
- username: ユーザー名
- email: メールアドレス
- password_hash: パスワード（ハッシュ化）
- is_premium: プレミアム会員フラグ
- subscription_end_date: サブスクリプション終了日
- daily_usage_count: 1日の利用回数
- last_usage_date: 最終利用日
```

### SavedRecipeテーブル
```python
- id: レコードID
- user_id: ユーザーID（外部キー）
- recipe_id: レシピID
- recipe_title: レシピタイトル
- recipe_image_url: レシピ画像URL
- saved_at: 保存日時
```

### Paymentテーブル
```python
- id: 支払いID
- user_id: ユーザーID（外部キー）
- amount: 金額
- currency: 通貨
- stripe_payment_id: Stripe決済ID
- subscription_type: サブスクリプションタイプ
- status: ステータス
- payment_date: 支払い日時
```

## セットアップ手順

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成し、以下を設定:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///vegetable_app.db

# Stripe設定
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# アフィリエイト設定
AMAZON_AFFILIATE_TAG=your-amazon-tag-20
RAKUTEN_AFFILIATE_ID=your-rakuten-id
```

### 3. データベース初期化

```bash
# アプリケーション実行時に自動作成されます
python app.py

# または、手動で初期化
flask init-db
```

### 4. Stripe設定

1. [Stripe Dashboard](https://dashboard.stripe.com/)でアカウント作成
2. APIキーを取得（テストモード/本番モード）
3. 商品と価格を作成
4. Webhookエンドポイントを設定: `https://yourdomain.com/payment/webhook`

必要なWebhookイベント:
- `checkout.session.completed`
- `customer.subscription.deleted`

### 5. アフィリエイト設定

#### Amazon アソシエイト
1. [Amazonアソシエイト](https://affiliate.amazon.co.jp/)に登録
2. アソシエイトタグを取得
3. `config.py`に設定

#### 楽天アフィリエイト
1. [楽天アフィリエイト](https://affiliate.rakuten.co.jp/)に登録
2. アフィリエイトIDを取得
3. `config.py`に設定

## 使用方法

### アプリケーション起動

```bash
python app.py
```

ブラウザで `http://localhost:5000` にアクセス

### 主要なエンドポイント

- `/` - ホームページ（野菜アップロード）
- `/auth/register` - 新規登録
- `/auth/login` - ログイン
- `/auth/profile` - プロフィール
- `/auth/saved-recipes` - 保存したレシピ
- `/payment/pricing` - 料金プラン
- `/predict` - 野菜認識とレシピ推薦
- `/predict/recipe` - レシピ詳細

## 収益化戦略

### 1. サブスクリプション収益

**想定月間収益** (100人のプレミアム会員の場合):
- 月額会員 (60人 × ¥980) = ¥58,800
- 年額会員 (40人 × ¥9,800 ÷ 12) = ¥32,666
- **合計: 約¥91,000/月**

### 2. アフィリエイト収益

**想定収益** (月間1,000アクティブユーザーの場合):
- クリック率: 5% (50クリック)
- コンバージョン率: 2% (1購入)
- 平均購入額: ¥3,000
- アフィリエイト報酬率: 3%
- **月間収益: 約¥90/購入 × 月間購入数**

### 3. 広告収益（将来的に追加可能）

- Google AdSense統合
- レシピページに適切な広告配置
- **想定RPM: ¥200-500**

## カスタマイズ

### 料金プランの変更

`config.py`の`PRICING`辞書を編集:

```python
PRICING = {
    'monthly': {
        'price': 980,  # 月額価格
        'name': '月額プラン',
        'features': [...]
    },
    'yearly': {
        'price': 9800,  # 年額価格
        'name': '年額プラン',
        'features': [...]
    }
}
```

### 利用制限の変更

`config.py`で無料ユーザーの制限を変更:

```python
FREE_USER_DAILY_LIMIT = 5  # 1日の利用回数
```

### アフィリエイトリンクの変更

`app.py`の`generate_affiliate_links()`関数を編集:

```python
def generate_affiliate_links(ingredients):
    # カスタムロジックを実装
    pass
```

## セキュリティ考慮事項

1. **本番環境では必ず変更**:
   - `SECRET_KEY`を強力なランダム文字列に
   - `DEBUG=False`に設定
   - HTTPSを使用

2. **データベース**:
   - 本番環境ではPostgreSQLやMySQLを推奨
   - 定期的なバックアップ

3. **Stripe**:
   - 本番環境では本番モードのAPIキーを使用
   - Webhookシークレットを適切に管理

4. **パスワード**:
   - Werkzeugでハッシュ化済み
   - 最低6文字以上を要求

## トラブルシューティング

### データベースエラー

```bash
# データベースを削除して再作成
rm vegetable_app.db
python app.py
```

### Stripe決済エラー

1. APIキーが正しいか確認
2. Stripeダッシュボードでログを確認
3. Webhookエンドポイントが正しく設定されているか確認

### アフィリエイトリンクが表示されない

1. `config.py`で`enabled: True`になっているか確認
2. アフィリエイトIDが正しく設定されているか確認

## 今後の拡張機能案

1. **ソーシャルログイン**
   - Google/Facebook/Twitter認証

2. **紹介プログラム**
   - 友達紹介で割引やクレジット付与

3. **企業向けプラン**
   - 飲食店や料理教室向けのAPIアクセス
   - 月額¥5,000-¥10,000

4. **広告プラットフォーム統合**
   - Google AdSense
   - アフィリエイトネットワーク拡大

5. **プレミアムコンテンツ**
   - 専門家によるレシピ
   - 栄養情報とカロリー計算

6. **分析ダッシュボード**
   - ユーザー行動分析
   - 収益レポート

## ライセンスとコンプライアンス

- 特定商取引法に基づく表記を追加
- プライバシーポリシーの作成
- 利用規約の作成
- Cookie使用の同意取得

## サポート

問題が発生した場合は、Issueを作成してください。

---

実装日: 2025年
バージョン: 1.0.0
