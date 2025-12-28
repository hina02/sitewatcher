# Site Watcher. 
Redis, Arq, Sentry, Prometheusの練習テーマ. 
URL死活監視とレスポンスタイム計測を行い、結果を非同期で処理する。

## 機能要件
### 監視リクエスト受付 (API)
- POST /checks エンドポイントを持つ。
- 入力: {"url": "https://example.com"}
- 出力: {"job_id": "uuid...", "status": "queued"}
- 処理: リクエストを受け取ったら即座にArqのキューに入れ、Job IDを返して終了する（ノンブロッキング）。
### 監視タスク実行 (Worker)
- キューからタスクを取り出し、実際にそのURLへHTTPリクエストを送る (httpx 推奨)。
- 成功時: ステータスコードと応答時間(ms)をログに出力する（今回はDBレスで簡略化するため、ログ＝「処理完了」とみなします）。
- 失敗時: 
    - 404/500エラー: エラーとして扱う（Sentry通知テスト用）。
    - タイムアウト: 例外を発生させる（Sentry通知テスト用）。
### 状態確認 (API)
- GET /checks/{job_id}
- Arqの標準機能を使って、そのジョブが queued, in_progress, complete, failed のどれかを確認する。
### ヘルスチェック (API)
- GET /health
- K8sのLiveness Probe用。単に {"status": "ok"} を返す。
