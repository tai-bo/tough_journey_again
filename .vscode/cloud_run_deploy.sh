docker buildx build \
  --platform linux/amd64 \
  -f packages/sv-input/Dockerfile \
  -t us-central1-docker.pkg.dev/tai-pr-dev/tai-pr-docker/sv-input:latest \
  --push \
  .

gcloud run deploy sv-input \
--image us-central1-docker.pkg.dev/tai-pr-dev/tai-pr-docker/sv-input:latest \
--port 9080 \
--use-http2 \
--allow-unauthenticated \
--no-invoker-iam-check \
--set-env-vars GOOGLE_CLOUD_PROJECT=tai-pr-dev \
--set-env-vars TAI_IS_LOCAL=0 \
--set-env-vars RESTATE_IDENTITY_KEY=publickeyv1_2U9tpRcJH8AJpBB7zm5CTfP77gYLGnF31onfwKBjEUhc \
--cpu=1 \
--memory=512Mi \
--concurrency=1 \
--min-instances=0 \
--max-instances=1 \
--region=us-central1 \
--timeout=180 \
--service-account=tai-pr-dev-sa-cloud-run@tai-pr-dev.iam.gserviceaccount.com
<!-- --no-allow-unauthenticated \ -->
<!-- --startup-probe="tcpSocket.port=9080,initialDelaySeconds=5" -->


restate deployments register https://sv-input-1053905202146.us-central1.run.app -e dev

restate deployments register https://sv-agent-1053905202146.us-central1.run.app -e dev

restate deployments register https://sv-vector-db-1053905202146.us-central1.run.app -e dev

restate deployments register https://vo-user-1053905202146.us-central1.run.app -e dev

