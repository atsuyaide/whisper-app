# Whisper音声文字起こしアプリケーション v2

OpenAI Whisperを使用したリアルタイム音声文字起こしアプリケーションです。標準モデルに加えて、ファインチューニング済みカスタムモデルもサポートしています。

## 📁 プロジェクト構造

```
whisper-app-v2/
├── backend/          # FastAPI バックエンドサーバー
│   ├── app/         # メインアプリケーション
│   ├── tests/       # テストコード
│   ├── models/      # Whisperモデルファイル
│   ├── demo/        # デモスクリプト
│   ├── docs/        # ドキュメント
│   └── compose.yaml # Docker Compose設定
├── frontend/        # React フロントエンド（予定）
│   ├── src/         # ソースコード
│   └── public/      # 静的ファイル
└── README.md        # このファイル
```

## 🚀 機能

### ✅ 実装済み

- **音声文字起こし API**: WAV/MP3ファイルのアップロード→文字起こし
- **WebSocketストリーミング**: リアルタイム音声文字起こし
- **カスタムモデル対応**: ファインチューニング済みモデルの自動検出・読み込み
- **モデル管理**: 利用可能モデルの一覧・状態確認・事前ロード
- **階層的アーキテクチャ**: 依存性注入によるテスタブルな設計
- **包括的テスト**: ユニット・統合・APIテストカバレッジ

### 🔄 開発中

- **React フロントエンド**: 音声アップロード・再生・結果表示UI
- **Docker環境**: 開発・本番環境の整備

## 🛠️ 技術スタック

### バックエンド
- **FastAPI**: 高性能Web API フレームワーク
- **OpenAI Whisper**: 音声認識エンジン
- **WebSocket**: リアルタイム通信
- **pytest**: テストフレームワーク
- **ruff/mypy**: コード品質・型チェック

### フロントエンド（予定）
- **React**: UI フレームワーク
- **TypeScript**: 型安全な開発
- **Vite**: 高速ビルドツール

## 📚 ドキュメント

- [カスタムモデル使用方法](backend/docs/CUSTOM_MODELS.md)
- [開発ガイドライン](CLAUDE.md)

## 🏃‍♂️ クイックスタート

### バックエンド起動

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### テスト実行

```bash
cd backend
pytest
```

### デモ実行

```bash
cd backend/demo
python streaming.py test_audio.wav --model base --language ja
```

## 📝 TODO

- [ ] React フロントエンド開発
- [ ] Docker環境構築
- [ ] CI/CD パイプライン設定
