# Backend Repo — Phase 3: Migration

**Repo:** Backend (AngaCloud FastAPI orchestrator) | **Branch:** `gcp-migration` | **Region:** `europe-west1`
**Prerequisite:** `INFRA_SETUP_CHECKLIST.md` complete, and `PIPELINE_MIGRATION_CHECKLIST.md` at least through Step 5 (pipeline image pushed) so `/process` can be tested.

---

## 1. Dependency swap

- [ ] Remove from `requirements.txt`: `azure-cosmos`, `azure-storage-blob`, `azure-identity`.
- [ ] Add: `google-cloud-firestore`, `google-cloud-storage`, `firebase-admin`, `google-cloud-aiplatform`.

---

## 2. Rewrite data interactions

- [ ] Replace every Cosmos DB call with the `google-cloud-firestore` client, targeting the collection structure set up in Infra: `users/{user_id}/farms/{farm_id}/seasons/{season_id}/observations/{observation_id}`.
- [ ] Replace every Azure Blob call with `google-cloud-storage`, targeting the four `angastack-*` buckets.

---

## 3. Multisource Ingestion Endpoints

Refactor the ingestion layer into two distinct endpoints to support both mobile photos and drone survey uploads:
- [ ] Build `POST /observation/mobile`: 
  - [ ] Write raw plant JPEG image to `angastack-raw-images/{user_id}/{farm_id}/{season_id}/{observation_id}/filename`
  - [ ] Execute zero-shot vision inference via Vertex AI (`google-cloud-aiplatform / Gemini 1.5 Flash`) using strict JSON schemas to identify diseases, pests, growth stages, or nutrient deficiencies.
  - [ ] Write observation metadata and Vertex AI inference payload directly to Firestore at `users/{user_id}/farms/{farm_id}/seasons/{season_id}/observations/{observation_id}` with `status: "complete"`
  - [ ] Immediately dispatch trigger to the AngAi service for action card generation

- [ ] Build `POST /observation/drone`: 
  - [ ] Write drone survey images to `angastack-raw-images/{user_id}/{farm_id}/{season_id}/{observation_id}/filename`
  - [ ] Create the Observation document in Firestore with `status: "processing"`
  - [ ] Trigger a Cloud Run Jobs execution of `angacloud-pipeline-job`, passing `USER_ID, FARM_ID, SEASON_ID, OBSERVATION_ID` as environment variable overrides.

---

## 4. `/farms` and `/seasons` endpoint

- [ ] Read/write `users/{user_id}/farms/{farm_id}` and `users/{user_id}/farms/{farm_id}/seasons/{season_id}` documents in Firestore instead of Cosmos DB.

---

## 5. Job Dispatch Mechanism

- [ ] On drone processing request: create an observation document in Firestore at `users/{user_id}/farms/{farm_id}/seasons/{season_id}/observations/{observation_id}` with `status: "processing"`
- [ ] Trigger a Cloud Run Jobs execution of `angacloud-pipeline-job`, passing `USER_ID`, `FARM_ID`, `SEASON_ID`, `OBSERVATION_ID` as environment variable overrides for that specific run (this replaces the old Azure Container Instances SDK call).
  - Use the Cloud Run Admin API client library (`google-cloud-run`) or a direct REST call to `jobs.run` — either works; pick whichever your team is more comfortable maintaining.
- [ ] This is a one-way trigger — the backend does **not** wait for the job to finish. Job completion is picked up separately (see Step 8, `/status`, and the AI trigger below).

---

## 6. `/status` endpoint

- [ ] Read observation `status` directly from the Firestore observation document at `users/{user_id}/farms/{farm_id}/seasons/{season_id}/observations/{observation_id}` (the pipeline itself sets drone status to `complete`/`failed` per the Pipeline checklist, mobile sets it instantly) and return it to the frontend for polling.

---

## 7. `/gallery` and `/farms` map-layer endpoints — Signed URLs

- [ ] Generate short-lived GCS Signed URLs for `mosaic/index-map` objects in `angastack-mosaics` and `angastack-index-maps` rather than making the buckets public. This lets AngaView render rasters securely
- [ ] ⚠️ **Requires the `Service Account Token Creator` role granted to `angacloud-backend-sa` on itself** — this was added to the Infra checklist specifically for this step. If signed-URL generation throws a permissions error at runtime, this is almost certainly why — go back and confirm that IAM binding exists.
- [ ] Set a short expiry (e.g. 15–60 minutes) on generated URLs — long enough for a page load, short enough that a leaked URL isn't a standing liability.

---

## 8. New endpoint: AI trigger

- [ ] Add `POST /process/ai-trigger` (or `/trigger-angai`, pick one name and use it consistently).
- [ ] This endpoint either:
  - (a) is called by something polling job status and detecting `complete`, or
  - (b) is called directly once you wire up a Firestore-triggered Cloud Function later (out of scope for V1 — polling is fine for now).
- [ ] On trigger, dispatch an HTTP request to the AngAi Cloud Run service URL (from the AI repo's Phase 4 deployment) with the `job_id` payload with the `observation_id`, `user_id`, `farm_id`, and `season_id` payload.
- [ ] Note: this endpoint doesn't need to wait for AngAi's response — fire-and-forget is fine, since AngAi writes its own output to Firestore and the frontend reads from there directly.

---

## 9. Authentication middleware

- [ ] Replace Microsoft Entra ID JWT verification with `firebase-admin`'s token verification (`firebase_admin.auth.verify_id_token(token)`).
- [ ] Initialise the Firebase Admin SDK once at app startup using the `angacloud-backend-sa` credentials (on Cloud Run, this happens automatically via the attached service account — no key file needed).

---

## 10. Dockerize and push

- [ ] Update the Dockerfile: remove Azure SDK installs, confirm `google-cloud-firestore`, `google-cloud-storage`, and `firebase-admin` are picked up from `requirements.txt`.
- [ ] Build and push:
  ```bash
  docker build -t europe-west1-docker.pkg.dev/angastack-platform/angastack-registry/backend:v1 .
  docker push europe-west1-docker.pkg.dev/angastack-platform/angastack-registry/backend:v1
  ```

---

## 11. Deploy to Cloud Run

- [ ] Console: **Cloud Run → Deploy container → Service**.
  - Container image URL: browse to `angastack-registry → backend → v1`.
  - Service name: `angacloud-backend`.
  - Region: `europe-west1`.
  - Authentication: **Allow unauthenticated invocations** (the API itself enforces auth via Firebase token verification in-app — this setting just controls whether Cloud Run's own layer blocks requests before they reach your code).
  - Service account: `angacloud-backend-sa`.
  - Under **Container, Variables & Secrets**: add any env vars the app needs (e.g. `GCP_PROJECT=angastack-platform`, `ANGAI_SERVICE_URL` once Phase 4 is deployed).
- [ ] CLI:
  ```bash
  gcloud run deploy angacloud-backend \
    --image=europe-west1-docker.pkg.dev/angastack-platform/angastack-registry/backend:v1 \
    --region=europe-west1 \
    --service-account=angacloud-backend-sa@angastack-platform.iam.gserviceaccount.com \
    --allow-unauthenticated
  ```
- [ ] Record the resulting Cloud Run service URL — the Frontend repo needs this for its API base URL.

---

## Phase 3 completion checkpoint

- [ ] All endpoints (`/observation/mobile`, `/observation/drone`, `/seasons`, `/status`, `/gallery`) run against Firestore/GCS instead of Cosmos DB/Azure Blob.
- [ ] `POST /observations/mobile` processes photos via Vertex AI (Gemini 1.5 Flash) and writes results to Firestore.
- [ ] `POST /observations/drone` successfully triggers a Cloud Run Jobs execution with the right env var overrides (`USER_ID`, `FARM_ID`, `SEASON_ID`, `OBSERVATION_ID`)
- [ ] Signed URLs work for map rendering (test this explicitly — it's the step most likely to fail silently on IAM).
- [ ] `POST /process/ai-trigger` exists and successfully calls the AngAi service once Phase 4 is deployed.
- [ ] Firebase Admin SDK correctly verifies tokens issued by the frontend's Firebase Auth.
