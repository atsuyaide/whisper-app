# CLAUDE 開発ガイドライン

```xml
<?xml version="1.0" encoding="UTF-8"?>
<guide>
  <title>CLAUDE 開発ガイドライン</title>

  <!-- ============================= 1. コミュニケーション ============================= -->
  <section id="1" title="コミュニケーション">

    <!-- ---------- 1.1 通知ポリシー ---------- -->
    <section id="1.1" title="通知ポリシー">
      <list>
        <item>音声通知コマンド: <code>paplay /usr/share/sounds/freedesktop/stereo/complete.oga</code></item>
        <item>
          以下のタイミングで通知を行う
          <list>
            <item>タスクの完了時</item>
            <item>ユーザーの確認が必要なコマンドを実行する直前</item>
          </list>
        </item>
      </list>
    </section>

    <!-- ---------- 1.2 会話ガイドライン ---------- -->
    <section id="1.2" title="会話ガイドライン">
      <list>
        <item>常に日本語で会話する</item>
      </list>
    </section>
  </section>

  <!-- ============================= 2. 開発ワークフロー ============================= -->
  <section id="2" title="開発ワークフロー">

    <!-- ---------- 2.1 開発哲学 ---------- -->
    <section id="2.1" title="開発哲学">

      <!-- 2.1.1 テスト駆動開発 (TDD) -->
      <section id="2.1.1" title="テスト駆動開発 (TDD)">
        <list>
          <item>原則として TDD で進める</item>
          <item>t-wada 氏のテストフレームワークを使用する</item>
          <item>漸進的な開発を重視し、機能ごとに小さなテストケースを作成</item>
        </list>

        <strong>TDD の基本サイクル: RED → GREEN → REFACTOR</strong>

        <steps>
          <step index="1">期待される入出力に基づき、まずテストを作成する。</step>
          <step index="2">実装コードは書かず、テストのみを用意する。</step>
          <step index="3">テストを実行し、失敗を確認する。</step>
          <step index="4">テストが正しいことを確認できた段階でコミットする。</step>
          <step index="5">その後、テストをパスさせる実装を行う。</step>
          <step index="6">実装中はテストを変更せず、コードを修正し続ける。</step>
          <step index="7">すべてのテストが通過するまで繰り返す。</step>
          <step index="8">テストが通過したらコミットする。</step>
        </steps>
      </section>

      <!-- 2.1.2 コード品質 -->
      <section id="2.1.2" title="コード品質">
        <list>
          <item>コメントは必要最低限（日本語）</item>
        </list>
      </section>
    </section>

    <!-- ---------- 2.2 バージョン管理 ---------- -->
    <section id="2.2" title="バージョン管理">

      <!-- 2.2.1 Git 運用 -->
      <section id="2.2.1" title="Git 運用">
        <list>
          <item>コミットは小さく意味のある単位で行う</item>
          <item>ブランチ命名規則: <code>feature/*</code>, <code>bugfix/*</code>, <code>hotfix/*</code></item>
        </list>
      </section>

      <!-- 2.2.2 リリース & バージョニング -->
      <section id="2.2.2" title="リリース &amp; バージョニング">
        <list>
          <item>Semantic Versioning (MAJOR.MINOR.PATCH) を採用</item>
          <item>変更点は <code>CHANGELOG.md</code> に記載</item>
          <item>GitHub Releases でタグを発行し、同バージョンの Docker イメージを公開</item>
        </list>
      </section>
    </section>

    <!-- ---------- 2.3 Python ---------- -->
    <section id="2.3" title="Python">

      <!-- 2.3.1 依存関係管理 -->
      <section id="2.3.1" title="依存関係管理">
        <list>
          <item><code>pyproject.toml</code> と <code>requirements.lock</code> をペアで管理</item>
          <item><code>requirements.lock</code> は <code>uv pip compile --all</code> で生成</item>
          <item>ロックファイル更新は必ず PR に含める</item>
        </list>
      </section>

      <!-- 2.3.2 仮想環境 -->
      <section id="2.3.2" title="仮想環境">
        <list>
          <item><code>uv venv</code> で環境を構築</item>
          <item>必ず uv の仮想環境を使用する</item>
        </list>
      </section>

      <!-- 2.3.3 コード品質 -->
      <section id="2.3.3" title="コード品質">
        <list>
          <item>すべての関数・メソッドに Type Hint を付与</item>
          <item><code>ruff</code> でフォーマットおよび静的解析を実施</item>
          <item><code>mypy</code> で型チェックを行う</item>
          <item><code>pytest</code> でユニットテストを実行</item>
          <item><code>pytest-randomly</code> でテスト実行順序をランダム化</item>
          <item><code>pre-commit</code> でコミット前に自動フォーマットと静的解析を実施</item>
        </list>
      </section>
    </section>

    <!-- ---------- 2.4 TypeScript ---------- -->
    <section id="2.4" title="TypeScript">

      <!-- 2.4.1 依存関係管理 -->
      <section id="2.4.1" title="依存関係管理">
        <list>
          <item>パッケージマネージャは <code>pnpm</code> を推奨（高速・省ディスク）</item>
          <item><code>package.json</code> と <code>pnpm-lock.yaml</code> を必ずコミット</item>
          <item>Monorepo ではワークスペース機能を活用し、ライブラリ間の依存を明示</item>
          <item>依存追加・更新は <code>pnpm add</code> / <code>pnpm up</code> を使用し、CI で <code>pnpm install --frozen-lockfile</code> を実行</item>
        </list>
      </section>

      <!-- 2.4.2 ビルド & トランスパイル -->
      <section id="2.4.2" title="ビルド &amp; トランスパイル">
        <list>
          <item><code>tsconfig.json</code> は <code>strict: true</code> を基本とし、ターゲットは ES2022 以降</item>
          <item>バンドルは <code>esbuild</code> または <code>Vite</code> を使用し、開発・本番の設定を分離</item>
          <item>型エラーを <code>noEmit</code> でブロックし、型が通過しないコードをリリースしない</item>
        </list>
      </section>

      <!-- 2.4.3 コード品質 -->
      <section id="2.4.3" title="コード品質">
        <list>
          <item><code>ESLint</code>（<code>@typescript-eslint</code>）で静的解析を実施</item>
          <item><code>Prettier</code> でコードフォーマットを自動化</item>
          <item><code>eslint --max-warnings 0</code> を CI に組み込み、警告ゼロを維持</item>
          <item><code>Husky + lint-staged</code> でコミット前に <code>eslint --fix</code> と <code>prettier --write</code> を実行</item>
        </list>
      </section>

      <!-- 2.4.4 テスト -->
      <section id="2.4.4" title="テスト">
        <list>
          <item>ユニットテストは <code>Vitest</code> を使用</item>
          <item>DOM 操作用には <code>@testing-library/react</code> を採用</item>
          <item>カバレッジ 80% 以上を維持し、CI で <code>vitest run --coverage</code> を必須実行</item>
          <item>E2E テストは <code>Playwright</code> を推奨し、TypeScript で記述</item>
        </list>
      </section>
    </section>
  </section>

  <!-- ============================= 3. セキュリティ ============================= -->
  <section id="3" title="セキュリティ">

    <!-- 3.1 Secrets 管理 -->
    <section id="3.1" title="Secrets 管理">
      <list>
        <item><code>.env.example</code> をリポジトリに置き、実 <code>.env</code> は Git 管理外とする</item>
        <item>GitHub Secret Scanning を有効化し、漏洩時はキーローテーションを迅速に実施</item>
        <item>Dependabot などで脆弱性を定期チェック</item>
      </list>
    </section>
  </section>

  <!-- ============================= 4. Docker & デプロイ ============================= -->
  <section id="4" title="Docker &amp; デプロイ">

    <!-- 4.1 Docker 方針 -->
    <section id="4.1" title="Docker 方針">
      <list>
        <item>すべての Docker イメージに <code>HEALTHCHECK</code> を設定</item>
      </list>
    </section>

    <!-- 4.2 Docker ベストプラクティス -->
    <section id="4.2" title="Docker ベストプラクティス">
      <list>
        <item>マルチステージビルドでイメージを軽量化</item>
        <item>開発用と本番用でビルドステージを分離</item>
        <item><code>latest</code> タグを避け、バージョンタグ（例: <code>v1.2.3</code>）を明示</item>
      </list>
    </section>
  </section>
</guide>
```
