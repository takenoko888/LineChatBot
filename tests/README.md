# テストファイル整理構造

## 📁 フォルダー構造

```
tests/
├── active/          # 現在使用中の重要なテスト
├── specific/        # 特定機能のテスト
├── legacy/          # 古い・重複テスト（アーカイブ）
└── results/         # テスト実行結果
```

## 🎯 active/ - 現在使用中の重要なテスト

### `chat_fix_test.py`
- **目的**: 雑談機能修正の検証
- **内容**: AI判定・パターン検出・フォールバック処理
- **実行**: `python tests/active/chat_fix_test.py`

### `koyeb_notification_fix_test.py`
- **目的**: Koyeb環境での通知機能修正検証
- **内容**: データ永続化・設定管理・CRUD操作・KeepAlive
- **実行**: `python tests/active/koyeb_notification_fix_test.py`

### `simple_test.py`
- **目的**: 基本機能の簡易テスト
- **内容**: 環境変数設定込みの基本動作確認
- **実行**: `python tests/active/simple_test.py`

### `comprehensive_test_suite.py`
- **目的**: 包括的な機能テスト
- **内容**: 全機能の統合テスト
- **実行**: `python tests/active/comprehensive_test_suite.py`

## 🔧 specific/ - 特定機能のテスト

### `test_auto_task_system.py`
- **目的**: 自動実行・モニタリング機能テスト
- **内容**: タスク作成・実行・削除・スケジューリング

### `test_search_url_display.py`
- **目的**: 検索結果URL表示機能テスト
- **内容**: URL表示・クリック可能リンク・ドメイン名表示

### `test_koyeb_optimization.py`
- **目的**: Koyeb環境最適化テスト
- **内容**: リソース効率・メモリ使用量・応答時間

## 📦 legacy/ - アーカイブテスト

古い・重複・使用しなくなったテストファイルを保管。
必要に応じて参照可能だが、通常の開発では使用しない。

## 📊 results/ - テスト結果

テスト実行結果の JSONファイルとテキストファイルを保管。
- `*_results.json`: 構造化テスト結果
- `test_results.txt`: テキスト形式の結果

## 🚀 推奨使用方法

### 開発時の基本テスト
```bash
python tests/active/simple_test.py
```

### 機能修正後の検証
```bash
python tests/active/chat_fix_test.py          # 雑談機能
python tests/active/koyeb_notification_fix_test.py  # 通知機能
```

### 包括的テスト（リリース前）
```bash
python tests/active/comprehensive_test_suite.py
```

### 特定機能のテスト
```bash
python tests/specific/test_auto_task_system.py  # 自動タスク機能
python tests/specific/test_search_url_display.py  # 検索機能
```

## 📝 テストファイル管理ルール

1. **新しいテスト**: `active/` または `specific/` に追加
2. **重要な修正**: `active/` のテストを更新
3. **古いテスト**: `legacy/` に移動
4. **結果ファイル**: `results/` に保存
5. **重複テスト**: 削除または `legacy/` に移動

## 🔄 定期メンテナンス

- 月1回: `legacy/` フォルダーの不要ファイル削除
- リリース前: `active/` の全テスト実行
- 機能追加時: 対応する `specific/` テスト作成 