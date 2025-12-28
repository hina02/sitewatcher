IMAGE_NAME := sitewatcher
TAG := latest
KUBECTL := kubectl
NAMESPACE := default

.PHONY: help build rebuild deploy restart dev logs-worker logs-main pf-grafana pf-worker clean

# ヘルプコマンド (make と打つと一覧が出ます)
help:
	@echo "======================================================================"
	@echo "  SiteWatcher Makefile"
	@echo "======================================================================"
	@echo "  make build       : Dockerイメージをビルド"
	@echo "  make rebuild     : キャッシュ無効化して完全リビルド (コード変更時推奨)"
	@echo "  make deploy      : K8sマニフェストを適用"
	@echo "  make restart     : Podを再起動してイメージを再取得"
	@echo "  make dev         : [推奨] リビルド -> デプロイ -> 再起動 を一括実行"
	@echo "  make job         : テスト用のジョブを投入 (Googleへのアクセス)"
	@echo "----------------------------------------------------------------------"
	@echo "  make logs-worker : Workerのログを表示 (-f)"
	@echo "  make logs-main   : Main APIのログを表示 (-f)"
	@echo "----------------------------------------------------------------------"
	@echo "  make pf-grafana  : Grafanaへのポートフォワード (localhost:3000)"
	@echo "  make pf-prom     : Prometheusへのポートフォワード (localhost:9090)"
	@echo "  make pf-worker   : Workerメトリクスへのポートフォワード (localhost:8001)"
	@echo "======================================================================"

# --- ビルド関連 ---
build:
	docker build -t $(IMAGE_NAME):$(TAG) .

rebuild:
	docker build --no-cache -t $(IMAGE_NAME):$(TAG) .

# --- デプロイ関連 ---
deploy:
	$(KUBECTL) apply -f manifest/

restart:
	$(KUBECTL) rollout restart deployment/main deployment/worker
	@echo "Restart triggered. Pods will be recreated shortly."

# --- 開発セット (一番よく使うやつ) ---
dev: rebuild deploy restart
	@echo "Deployment updated. Check logs with 'make logs-worker'"

# --- 運用・確認系 ---
job:
	curl -X POST "http://localhost:8000/jobs?url=https://www.google.com"

logs-worker:
	$(KUBECTL) logs -f -l app=worker

logs-main:
	$(KUBECTL) logs -f -l app=main

# --- ポートフォワード系 ---
pf-grafana:
	$(KUBECTL) port-forward svc/monitoring-grafana 3000:80 -n monitoring

pf-prom:
	$(KUBECTL) port-forward svc/prometheus-monitoring-kube-prometheus-prometheus 9090:9090 -n monitoring

pf-worker:
	$(KUBECTL) port-forward svc/worker-svc 8001:8001

# --- お掃除 ---
clean:
	$(KUBECTL) delete -f manifest/