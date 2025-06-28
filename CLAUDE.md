# CLAUDE 開発ガイドライン

---

## 1. コミュニケーション

### 1.1 通知ポリシー

- 音声通知コマンド: `paplay /usr/share/sounds/freedesktop/stereo/complete.oga`
- 以下のタイミングで通知を行う
  - タスクの完了時
  - ユーザーの確認が必要なコマンドを実行する直前

### 1.2 会話ガイドライン

- 常に日本語で会話する

---

## 2. 開発ワークフロー

### 2.1 開発哲学

#### 2.1.1 テスト駆動開発 (TDD)

- 原則として TDD で進める
- t‑wada 氏のテストフレームワークを使用する
- 漸進的な開発を重視し、機能ごとに小さなテストケースを作成

**TDD の基本サイクル: RED → GREEN → REFACTOR**

1. 期待される入出力に基づき、まずテストを作成する。
2. 実装コードは書かず、テストのみを用意する。
3. テストを実行し、失敗を確認する。
4. テストが正しいことを確認できた段階でコミットする。
5. その後、テストをパスさせる実装を行う。
6. 実装中はテストを変更せず、コードを修正し続ける。
7. すべてのテストが通過するまで繰り返す。
8. テストが通過したらコミットする。

#### 2.1.2 コード品質

- コメントは必要最低限（日本語）

### 2.2 バージョン管理

#### 2.2.1 Git 運用

- コミットは小さく意味のある単位で行う
- ブランチ命名規則: `feature/*`, `bugfix/*`, `hotfix/*`

#### 2.2.2 リリース & バージョニング

- Semantic Versioning (MAJOR.MINOR.PATCH) を採用
- 変更点は `CHANGELOG.md` に記載
- GitHub Releases でタグを発行し、同バージョンの Docker イメージを公開

### 2.3 Python

#### 2.3.1 依存関係管理

- `pyproject.toml` と `requirements.lock` をペアで管理
- `requirements.lock` は `uv pip compile --all` で生成
- ロックファイル更新は必ず PR に含める

#### 2.3.2 仮想環境

- `uv venv` で環境を構築
- 必ず uv の仮想環境を使用する

#### 2.3.3 コード品質

- すべての関数・メソッドに Type Hint を付与
- `ruff` でフォーマットおよび静的解析を実施
- `mypy` で型チェックを行う
- `pytest` でユニットテストを実行
- `pytest-randomly` でテスト実行順序をランダム化
- `pre-commit` でコミット前に自動フォーマットと静的解析を実施

### 2.4 TypeScript

#### 2.4.1 依存関係管理

- パッケージマネージャは **pnpm*- を推奨（高速・省ディスク）
- `package.json` と `pnpm-lock.yaml` を必ずコミット
- Monorepo ではワークスペース機能を活用し、ライブラリ間の依存を明示
- 依存追加・更新は `pnpm add` / `pnpm up` を使用し、CI で `pnpm install --frozen-lockfile` を実行

#### 2.4.2 ビルド & トランスパイル

- `tsconfig.json` は `strict: true` を基本とし、ターゲットは ES2022 以降
- バンドルは **esbuild*- または**Vite*- を使用し、開発・本番の設定を分離
- 型エラーを `noEmit` でブロックし、型が通過しないコードをリリースしない

#### 2.4.3 コード品質

- **ESLint**（`@typescript-eslint`）で静的解析を実施
- **Prettier*- でコードフォーマットを自動化
- `eslint --max-warnings 0` を CI に組み込み、警告ゼロを維持
- **Husky + lint‑staged*- でコミット前に `eslint --fix` と `prettier --write` を実行

#### 2.4.4 テスト

- ユニットテストは **Vitest*- を使用
- DOM 操作用には **@testing-library/react*- を採用
- カバレッジ 80% 以上を維持し、CI で `vitest run --coverage` を必須実行
- E2E テストは **Playwright*- を推奨し、TypeScript で記述

---

## 3. セキュリティ

### 3.1 Secrets 管理

- `.env.example` をリポジトリに置き、実 `.env` は Git 管理外とする
- GitHub Secret Scanning を有効化し、漏洩時はキーローテーションを迅速に実施
- Dependabot などで脆弱性を定期チェック

---

## 4. Docker & デプロイ

### 4.1 Docker 方針

- すべての Docker イメージに `HEALTHCHECK` を設定

### 4.2 Docker ベストプラクティス

- マルチステージビルドでイメージを軽量化
- 開発用と本番用でビルドステージを分離
- `latest` タグを避け、バージョンタグ（例: `v1.2.3`）を明示
