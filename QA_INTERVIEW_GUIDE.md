# Smart Retail Shelf Monitoring: QA and Quality Automation Interview Guide

This guide is based on the current repository, not only the README. Statements marked **Implemented** are present in the code. Statements marked **Not implemented in the current project** are proposals or gaps.

## 1. Project Understanding

### 30-second explanation

This is a computer-vision application for analyzing a retail shelf image. A React dashboard uploads a JPEG or PNG to a FastAPI endpoint. The backend validates and decodes the image, runs a preloaded Ultralytics YOLO model, converts detections into Pydantic objects, counts products, draws boxes, and returns JSON containing detections, inventory, metadata, and a Base64-encoded annotated image.

From a QA perspective, the important contract is: valid image in, deterministic response shape and safe error response out. The highest risks are model startup, image decoding, inference failures, response consistency, concurrency around the shared model, and frontend/backend communication.

### 1-minute explanation

The application has a FastAPI backend in `src/main.py` and `src/api/routes.py`, a React client in `frontend/src/main.jsx`, and services under `src/services/`. Startup calls `initialize_services()` in `src/api/dependencies.py`; that creates one `YOLOInferenceEngine`, warms it up, and injects a singleton `ShelfMonitoringService` into requests. `ShelfMonitoringService.process_image()` reads upload bytes, validates them with OpenCV, decodes them, calls `YOLOInferenceEngine.infer()`, annotates the image, summarizes counts with `InventoryCounter`, and formats an `InferenceResponse` with `ResponseFormatter`.

The current pytest suite has only three API tests: root, health, and invalid image upload. It does not currently prove the successful detection path, schema details, model behavior, service logic, frontend behavior, Docker behavior, load behavior, or security behavior.

### 2-minute explanation

The user selects an image in React. The dashboard sends a browser `fetch()` request to the configured detection API URL, with the file under the multipart field `image`. FastAPI receives it at `POST /api/v1/detect`. Dependency injection supplies the singleton shelf service. The service reads all bytes and accepts anything OpenCV can decode; it does not inspect extension or MIME type. OpenCV decodes with `cv2.IMREAD_COLOR`, so grayscale input becomes a color matrix. The YOLO engine calls `model.predict()` using configured confidence and IoU thresholds. A lock serializes model inference. Results are parsed into `BoundingBox` Pydantic models, then counted by class name. The formatter records image dimensions and rounded inference time, encodes the annotated image as JPEG Base64, and returns `InferenceResponse`.

The API also exposes `GET /`, `GET /health`, and `GET /model-info`. Middleware adds an `X-Correlation-ID` response header and logs method, path, and latency. `InvalidImageError` is mapped to 400 and unexpected exceptions to a generic 500 response. `ModelLoadError` is also mapped to 500, although model loading normally occurs during startup, before a request can be served. The application has no authentication, database, queue, background job, rate limiting, CI workflow, or specialized test fixtures in the current repository.

### Inputs, outputs, and major components

- Inputs: multipart upload field `image`; dashboard accepts `.jpg`, `.jpeg`, and `.png`; direct API validation is based on decodability, not filename.
- Processing: OpenCV decode, YOLO inference, detection parsing, annotation, counting, response formatting.
- Outputs: JSON response with `success`, `detections`, `inventory`, `annotated_image`, and optional `metadata`.
- Operational outputs: `/health`, `/model-info`, logs, `X-Correlation-ID`.
- Main modules: `frontend/src/main.jsx`, `frontend/src/styles.css`, `src/main.py`, `src/api/routes.py`, `src/api/dependencies.py`, `src/services/shelf_service.py`, `src/services/detection.py`, `src/services/counter.py`, `src/services/formatter.py`, `src/utils/image_proc.py`, `src/models/schemas.py`.

### What can go wrong

1. Model file or model dependencies fail during startup.
2. A missing, empty, malformed, or undecodable upload reaches the endpoint.
3. The model returns empty, malformed, out-of-range, or unexpected results.
4. Counting disagrees with detections.
5. Annotation or Base64 encoding fails.
6. Response validation fails or the frontend assumes missing fields exist.
7. The singleton model serializes concurrent requests and creates a latency queue.
8. Docker has a missing `.env`, incorrect network URL, slow image build, or unavailable model download.
9. The dashboard cannot connect, receives a non-200 response, or receives invalid JSON/Base64.
10. Oversized images consume excessive CPU or memory; there is no explicit upload-size limit.

## 2. Architecture and Test Map

| Component          | Responsibility                               | Possible failure                                          | Appropriate test                                       |
| ------------------ | -------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------ |
| React dashboard    | Upload, call API, display and export results | bad URL, timeout, missing response key, empty-table crash | Browser smoke/E2E; mocked fetch unit tests             |
| `main.py` lifespan | initialize services and shut down            | model load failure prevents startup                       | startup integration test                               |
| request middleware | correlation ID and latency log               | missing header/logging failure                            | API integration test                                   |
| `routes.py`        | HTTP endpoints and DI                        | wrong status, dependency failure, wrong contract          | API tests with TestClient                              |
| `dependencies.py`  | singleton detector/service                   | uninitialized state, stale global state                   | unit/integration tests; reset fixture                  |
| `shelf_service.py` | pipeline orchestration                       | wrong order, leaked decode errors, inference failure      | mocked unit test                                       |
| `image_proc.py`    | validate/decode/draw/encode                  | channel, dimension, encoding bugs                         | pure unit tests with generated images                  |
| `detection.py`     | model load, lock, inference, parse           | download failure, malformed boxes, slow inference         | mocked model unit tests plus one real-model smoke test |
| `counter.py`       | count and sort objects                       | wrong total, case or ordering issue                       | unit tests                                             |
| `formatter.py`     | metadata, Base64, Pydantic response          | wrong dimensions or invalid response                      | unit tests/schema tests                                |
| `schemas.py`       | structural validation                        | wrong types/ranges accepted or rejected                   | Pydantic validation tests                              |
| Docker files       | package and run backend/frontend             | port/network/env/model failures                           | build/start/network smoke tests                        |

Complete flow: User -> React -> `fetch` -> FastAPI route -> dependency injection -> `ShelfMonitoringService.process_image` -> `validate_image_bytes` -> `decode_image` -> `YOLOInferenceEngine.infer` -> `draw_boxes` -> `InventoryCounter.summarize` -> `ResponseFormatter.build_response` -> `InferenceResponse` -> JSON/Base64 -> React.

## 3. Current API Contract

### `GET /`

- Request: no body.
- Current success: 200 and a dictionary containing application name, version, docs path, and health path.
- Positive test: assert exact application name and the four advertised keys.
- Negative/boundary: wrong method gives framework 405; unknown path gives 404. There is no user input to validate.

### `GET /health`

- Request: no body; dependency `get_detector` supplies the initialized detector.
- Current success: 200 with `status: healthy`, uppercase `device`, model name, and `gpu_memory_mb` (number when CUDA is available, otherwise null).
- Failure: uninitialized detector raises `RuntimeError`; it is expected to become a generic 500 through the exception handler, subject to FastAPI exception propagation behavior.
- Test: assert status, device/model keys, and that the detector dependency is called or overridden in isolation.

### `GET /model-info`

- Request: no body; same detector dependency.
- Current success: 200 with model, framework, device, confidence threshold, and IoU threshold.
- Test configured threshold values and model name. Test uninitialized detector separately.

### `POST /api/v1/detect`

- Request: multipart/form-data with required field `image` of type `UploadFile`.
- Current success: 200 and an `InferenceResponse`: `success`, list of `BoundingBox`, `InventorySummary`, JPEG Base64 string, and `DetectionMetadata`.
- Valid image: OpenCV decodes it and inference runs.
- Invalid bytes: 400 with `{"success": false, "message": "Invalid image. Upload JPEG or PNG."}`.
- Missing field: normally 422 from FastAPI validation.
- Wrong HTTP method: 405. Unknown path: 404.
- Unsupported extension with valid image bytes: currently likely accepted by the direct API because extension/MIME is not checked. The dashboard UI filters extensions, but that is not backend enforcement.
- Model/inference/encoding failures: model load is intended as 500; unexpected failures are generic 500. There is no explicit 503 mapping and `InferenceError` is defined but not raised or handled.

### Test-case table

| ID     | Endpoint      | Scenario                 | Input                  | Expected status | Expected result                  | Priority |
| ------ | ------------- | ------------------------ | ---------------------- | --------------: | -------------------------------- | -------- |
| API-01 | `/`           | root works               | GET                    |             200 | application contract exists      | P0       |
| API-02 | `/health`     | healthy backend          | GET                    |             200 | healthy status and device/model  | P0       |
| API-03 | `/model-info` | model settings exposed   | GET                    |             200 | model/framework/thresholds       | P1       |
| API-04 | `/detect`     | valid JPEG               | multipart image        |             200 | schema-valid response            | P0       |
| API-05 | `/detect`     | valid PNG                | multipart image        |             200 | schema-valid response            | P0       |
| API-06 | `/detect`     | empty bytes              | empty upload           |             400 | invalid-image response           | P0       |
| API-07 | `/detect`     | corrupt bytes            | random bytes           |             400 | invalid-image response           | P0       |
| API-08 | `/detect`     | missing field            | no `image`             |             422 | validation error                 | P0       |
| API-09 | `/detect`     | wrong content            | text bytes             |             400 | invalid-image response           | P0       |
| API-10 | `/detect`     | zero detections          | mocked empty result    |             200 | empty detections, total 0        | P0       |
| API-11 | `/detect`     | multiple classes         | mocked boxes           |             200 | counts and total agree           | P1       |
| API-12 | `/detect`     | model exception          | mocked raise           |   500 currently | generic safe error               | P0       |
| API-13 | `/health`     | detector absent          | dependency override    |   500 currently | startup/config failure           | P1       |
| API-14 | any route     | wrong method             | e.g. POST `/health`    |             405 | method not allowed               | P1       |
| API-15 | unknown       | unknown path             | GET `/missing`         |             404 | not found                        | P1       |
| API-16 | `/detect`     | wrong multipart shape    | JSON or malformed form |             422 | request validation error         | P1       |
| API-17 | `/detect`     | valid bytes, `.txt` name | image content          |   200 currently | demonstrates missing MIME policy | P2       |
| API-18 | `/detect`     | huge image               | large generated image  |     unspecified | measure/reject safely            | P1       |

## 4. Existing Pytest Tests

`tests/test_api.py` currently contains module-level setup:

- `from fastapi.testclient import TestClient`: imports FastAPI's in-process HTTP client.
- `from src.main import app`: imports the application and its routes/handlers.
- `from src.api.dependencies import initialize_services`: imports manual service initialization.
- `initialize_services()`: loads the actual YOLO model and warms it up at test collection/import time. This makes tests slower and couples them to the model file/runtime.
- `client = TestClient(app)`: creates a client for HTTP-style tests without starting a real server.

`test_root_endpoint()` sends `GET /`, asserts 200, and asserts the exact application name. It is a positive API smoke test. If routing or the root payload breaks, it fails. Missing: all other fields, headers, wrong methods, unknown paths, and startup behavior.

`test_health_endpoint()` sends `GET /`, actually the code sends `GET "/health"`, asserts 200, parses JSON, and asserts `status == "healthy"`. It verifies the initialized detector can service health. If dependency initialization, detector loading, or the route breaks, it fails. Missing: device/model/gpu fields, uninitialized state, model-info, latency, and correlation ID.

`test_invalid_image_upload()` posts to `/api/v1/detect` with a multipart field named `image`, filename `test.txt`, bytes `b"not_an_image"`, and MIME `text/plain`. It asserts 400. It is a negative API integration test for decode rejection and the `InvalidImageError` handler. It does not prove the filename/MIME is rejected: the bytes are invalid, so OpenCV rejection is the reason for 400. Missing: valid content, empty bytes, missing field, corrupt real image, unsupported-but-valid content, response body, and service/model isolation.

**Current result:** `3 passed in 9.34s` using `venv\Scripts\python.exe -m pytest -q`. A bare `pytest -q` was unavailable on PATH.

## 5. QA Strategy: Current Versus Proposed

| Strategy    | Simple meaning                        | Project example                                              | Current status                                                       |
| ----------- | ------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------- |
| Unit        | test one function/class in isolation  | `InventoryCounter.summarize`, `letterbox`, schema validation | Not implemented in the current project.                              |
| Integration | test collaborating modules            | service with mocked detector and real formatter              | Not implemented in the current project.                              |
| API         | test HTTP contract                    | TestClient POST `/api/v1/detect`                             | Partially implemented: 3 tests, no success path.                     |
| End-to-end  | test user flow through UI/backend     | upload in React and view annotated result                    | Not implemented in the current project.                              |
| Regression  | rerun prior behavior after changes    | counter change still preserves totals and response           | Not implemented in the current project.                              |
| Smoke       | shallow build-up check                | app starts and `/health` is 200                              | Partially implemented by health test; no automated startup pipeline. |
| Sanity      | focused check after a small change    | after image validation change, valid upload still works      | Not implemented in the current project.                              |
| Negative    | deliberately invalid input/failure    | random bytes, missing field, model exception                 | Only invalid bytes is implemented.                                   |
| Boundary    | values at limits                      | confidence 0/1, class id 0, empty list, 1-pixel image        | Not implemented in the current project.                              |
| Performance | measure speed/resources under load    | p95 POST latency with serialized inference                   | Not implemented in the current project.                              |
| Reliability | repeated/failure/restart behavior     | repeated uploads, model/backend restart                      | Not implemented in the current project.                              |
| Security    | abuse, exposure, limits, dependencies | oversized upload, path input, error disclosure               | Not implemented in the current project.                              |

## 6. Proposed P0-P3 Test Plan

### P0 - critical

- Valid JPEG and PNG with mocked inference: expect 200, response schema valid, dimensions correct, Base64 decodes.
- Empty bytes, random/corrupt bytes: expect 400 and safe message.
- Missing `image`: expect 422.
- Zero detections: expect 200, `detections=[]`, `total_objects=0`, `products=[]`; also test dashboard because the current `inventory_df.columns = ["Product", "Quantity"]` may fail for a DataFrame created from an empty list.
- Multiple detections: verify one detection produces one count and duplicate class names aggregate.
- Model unavailable and inference exception: verify startup/request failure behavior and no traceback or internal path is exposed.
- Response schema validation: validate nested boxes, inventory, metadata and total consistency.

### P1 - high

- Confidence threshold: mocked detections below/at/above configured threshold; note filtering is delegated to YOLO, so test the call arguments and parsing rather than assuming the engine filters itself.
- Low-confidence model output: verify the engine passes `conf=settings.CONF_THRESHOLD` and does not emit invalid confidence.
- Very small, large, different-resolution, and different-aspect-ratio images.
- Grayscale and RGB input: verify OpenCV output is a 3-channel color matrix.
- Unexpected model output: empty result list, missing boxes, invalid class index, malformed tensor; define safe failure behavior.
- Concurrent requests: submit 10 requests, confirm no corrupted results and measure queueing due to `threading.Lock`.
- API unavailable/timeout from dashboard: verify user-facing error and no stale misleading success.
- Docker build/start/health/network smoke test.

### P2 - medium

- Direct API with unsupported extension and valid bytes, to decide whether backend should enforce MIME/extension.
- Bounding-box edge coordinates and annotation clipping.
- Base64 round trip and image encoding failure.
- `/model-info`, correlation ID, wrong methods, unknown paths, and malformed multipart.
- Counter ordering, case-insensitive `get_product_count`, and sorted `unique_products`.
- Restart and repeated inference reliability.

### P3 - low

- UI layout and analytics formatting for unusual class names.
- Export filename/mime behavior.
- Documentation examples and Swagger contract snapshots.
- Dependency vulnerability and image-size optimization checks.

Expected behavior for invalid or unsupported inputs should be made explicit first. For example, currently valid image bytes named `.txt` can pass direct API validation; a future policy could return 415, but that would be a deliberate behavior change.

## 7. Pydantic Response Testing

`BoundingBox` requires `class_id >= 0`, confidence from 0 to 1, and integer coordinates, but it does not require nonnegative coordinates or enforce `x_min <= x_max` / `y_min <= y_max`. `class_name` can be empty. Those are schema/business validation gaps.

`InventoryItem.quantity >= 0`; `InventorySummary.total_objects` has no nonnegative constraint and there is no schema validator proving it equals the sum of product quantities. `DetectionMetadata` has no range constraints for time or dimensions. `InferenceResponse` requires the four main fields and allows `metadata=None`.

Test missing fields and wrong types with `ValidationError`; test confidence -0.01 and 1.01; class id -1; negative coordinates; quantity -1; missing metadata; empty detections; and inconsistent inventory totals. Structural schema validation asks “does this have the right shape and primitive ranges?” Business validation asks “does this response make sense?” For example, `total_objects == len(detections)` and each product quantity agrees with detections are business invariants and are not currently enforced by Pydantic.

## 8. Error Handling

- `InvalidImageError`: raised by `ShelfMonitoringService` after `validate_image_bytes` returns false; current HTTP status 400 and message is exposed. The message is appropriate for a client, but should not include internal paths.
- `ModelLoadError`: raised while constructing `YOLOInferenceEngine`; current handler returns 500 with `str(exc)`, which may expose model paths or dependency details. A production design would log details server-side and return a stable message, often 503 when the service is unavailable.
- `InferenceError`: defined in `src/core/exceptions.py` but not raised or handled in the current code. Not implemented in the current project.
- `RuntimeError`: dependency getters raise it when services are not initialized. There is no dedicated handler; generic handling is intended to return 500.
- Generic `Exception`: logged with `logger.exception(exc)` and returned as `{"success": false, "message": "Internal Server Error"}` with 500.

The middleware logs method/path/latency and adds `X-Correlation-ID`, but it does not include that ID in the log message. Exception handlers accept `request` but do not use it. Error responses are not the same shape as `InferenceResponse`, which is reasonable for errors but should be documented/tested.

## 9. HTTP Status Codes

| Code | Meaning                               | Applies here?                      | Example                                                           |
| ---: | ------------------------------------- | ---------------------------------- | ----------------------------------------------------------------- |
|  200 | successful request                    | Yes                                | health or successful detection                                    |
|  201 | resource created                      | No current resource creation       | would apply to creating a stored report                           |
|  400 | malformed/invalid application input   | Yes                                | undecodable image handled by `InvalidImageError`                  |
|  401 | unauthenticated                       | No authentication exists           | would apply if protected API had no token                         |
|  403 | authenticated but forbidden           | No authorization exists            | user lacks access to a model/report                               |
|  404 | route/resource not found              | Yes for unknown route              | `/unknown`                                                        |
|  405 | method not allowed                    | Yes                                | POST to `/health`                                                 |
|  409 | state conflict                        | No current conflict resource       | duplicate job/report in a future system                           |
|  415 | unsupported media type                | Not currently emitted              | backend explicitly rejects `application/pdf`                      |
|  422 | request validation failure            | Yes                                | missing required multipart field or wrong FastAPI parameter shape |
|  429 | too many requests                     | No rate limiter exists             | future throttling under load                                      |
|  500 | unexpected server/application failure | Yes                                | generic exception or current model-load handler                   |
|  502 | bad gateway                           | No proxy/upstream gateway contract | reverse proxy gets a bad upstream response                        |
|  503 | service unavailable                   | Not currently emitted              | model not ready or dependency unavailable; a good future mapping  |
|  504 | gateway timeout                       | No gateway in this repo            | proxy times out waiting for inference                             |

400 versus 422: 400 is used by this application for a request that reaches business code but contains undecodable image bytes. 422 is generated by FastAPI/Pydantic when the request cannot satisfy the declared endpoint shape, such as missing `image`. 500 versus 503: 500 means an unexpected application fault; 503 better communicates that the service is temporarily not ready, such as model initialization failure. 404 versus 405: 404 means no route matches; 405 means a route exists but the HTTP method is wrong.

## 10. Smoke, Sanity, Regression

- Smoke: after deployment, call `GET /health` and perhaps `/model-info`; if the API cannot start or respond, stop the pipeline.
- Sanity: after changing `validate_image_bytes`, test one valid JPEG, one invalid upload, and one detection response to check the focused slice.
- Regression: after changing `InventoryCounter`, rerun API, service, formatter, schema, and zero/multiple-detection tests to ensure old behavior remains intact.

Smoke is broad and shallow. Sanity is narrow and change-focused. Regression is broader and protects previously working behavior.

## 11. API Automation and Framework Design

`pytest` discovers functions named `test_*`; `TestClient` performs in-process HTTP calls; assertions compare status and JSON values. Current setup has no fixtures, teardown, mocking, test data directory, or reusable utilities. Module-level `initialize_services()` is setup, but it loads the real model and has no teardown/reset.

A professional proposed structure, not the current structure, would be:

```text
tests/
  conftest.py
  api/
    test_health.py
    test_detection.py
  unit/
    test_counter.py
    test_image_proc.py
    test_formatter.py
    test_schemas.py
    test_detection_engine.py
  integration/
    test_pipeline.py
  e2e/
    test_dashboard_flow.py
  fixtures/
  test_data/
```

Useful fixtures would create a TestClient, a tiny generated JPEG/PNG, valid fake `BoundingBox` objects, and a fake detector. Teardown should restore dependency globals or use FastAPI dependency overrides so tests remain isolated. Reusable helpers should assert response shape and decode Base64. Test data should be small, deterministic, and versioned.

Example mocking approach:

```python
from unittest.mock import Mock

fake_detector = Mock()
fake_detector.model_name = "test-model"
fake_detector.infer.return_value = ([], 1.2)
service = ShelfMonitoringService(fake_detector)
```

Mock YOLO in service/API tests to avoid loading a multi-hundred-megabyte model and to force zero, multiple, malformed, and exception outputs. Mock `ShelfMonitoringService` when testing route wiring only. Mock external HTTP calls in dashboard tests so tests do not require a running backend. Do not mock the code under test; keep at least one real integration test and a small real-model smoke test if model availability is part of deployment risk.

## 12. YOLO and ML Testing

Software QA checks that the model component behaves as a software component: it loads, receives a correctly shaped image, calls `predict` with configured device/confidence/IoU, returns parseable boxes, preserves confidence range, handles empty output, and fails safely. Test class IDs/names, coordinate types, inference timing, lock behavior, and model-loading errors with mocks.

ML evaluation checks model quality against labeled data: precision, recall, IoU, and mAP. These are not expected in every API test and are **Not implemented in the current project.** A labeled evaluation dataset and evaluation pipeline are absent. A QA engineer can gate the model package with a benchmark, but that is separate from HTTP contract testing.

- Precision: of reported detections, how many are correct.
- Recall: of real objects, how many were found.
- IoU: overlap between predicted and ground-truth boxes.
- mAP: aggregate precision-recall quality across classes/thresholds.

## 13. Image Processing

`validate_image_bytes` converts bytes to a NumPy uint8 buffer and calls `cv2.imdecode(..., IMREAD_COLOR)`. `decode_image` repeats this and raises `ValueError` if decoding returns `None`. `letterbox` preserves aspect ratio by resizing and padding to a square but is not called by the current shelf pipeline; YOLO performs its own preprocessing. `draw_boxes` copies the image and draws rectangles/labels. `image_to_base64` JPEG-encodes. `base64_to_image` decodes Base64 back to OpenCV.

Test JPEG, PNG, invalid bytes, truncated/corrupt files, 1x1 and large images, wide/tall aspect ratios, grayscale and RGB sources, and unsupported formats. OpenCV color decoding should yield a 3-channel matrix for grayscale input. Check that output dimensions and pixel type are sensible. Watch for integer coordinate clipping, labels above the image when `y_min` is small, memory use for huge files, and Base64 decode exceptions. There is no explicit size limit, channel validation, MIME enforcement, or EXIF/orientation handling in the current code.

## 14. Performance and Concurrency

Measure end-to-end response time, detector inference time from `inference_time_ms`, average, p95, p99, throughput/RPS, CPU, GPU, and memory. Compare one request against 10 and 100 concurrent requests. The model is loaded once, which avoids repeated load cost. `YOLOInferenceEngine.infer` holds a `threading.Lock` around `model.predict`, so concurrent requests are serialized at inference. Ten users will queue rather than run inference simultaneously through this instance. At 100 users, queue latency, memory from uploaded images, HTTP worker limits, CPU/GPU capacity, and timeout behavior become risks.

The endpoint is declared `async`, but inference is synchronous and runs inside it. This can block the event-loop worker while waiting for model prediction; the lock also serializes the critical section. Improvements could include multiple worker processes/model replicas, a bounded inference queue, batching, a dedicated executor, upload limits, backpressure, and measured GPU-sharing policy. These are proposals; they are **Not implemented in the current project.** Identify bottlenecks with application latency logs, profiling, server metrics, and load-test traces.

## 15. Docker QA

The backend `Dockerfile` builds from `python:3.11-slim`, installs system libraries and all Python requirements, copies the project, exposes 8000, and starts FastAPI. The React `frontend/Dockerfile` builds and previews the Vite app. `docker-compose.yml` defines backend and frontend services, maps ports 8000 and 4173, uses a bridge network, and sets frontend `VITE_API_URL` to `http://127.0.0.1:8000/api/v1/detect`.

Proposed Docker checks: build each image; start both services; call backend `/health`; open React; upload an image; verify browser-to-backend networking; confirm ports, env values, model path, restart behavior, logs, and container health. Docker Compose has no explicit `healthcheck`, so `depends_on` does not prove backend readiness. Compose requires `.env` because backend uses `env_file: .env`; the README mentions `.env.example`, but that file is not in the listed repository structure. Model download/network failure, slow startup, wrong API URL, CORS, and missing system libraries are likely failure scenarios.

## 16. CI/CD Quality Gate

A proposed GitHub Actions pipeline is:

```text
push/pull request
  -> install Python 3.11 and dependencies
  -> syntax/lint/type checks
  -> unit tests with mocked model
  -> API/integration tests
  -> Docker build
  -> vulnerability/dependency/image scan
  -> optional deployment
```

No GitHub Actions workflow is present in the current repository. Linting, type checking, integration tests, security scans, and deployment are **Not implemented in the current project.** A failed test or build should fail the job and block deployment. Real-model tests can be a separate job because they are slower and may need model artifacts/GPU. A deployment job should require all quality gates and should run smoke tests after deployment.

## 17. Frontend QA

The dashboard uses a browser file input accepting JPEG and PNG images, shows an original image preview, posts with `fetch`, handles connection exceptions, shows non-200 response messages, renders `annotated_image` as a Base64 JPEG, stores the response in React state, displays metrics/tables/charts, offers a JPEG download, polls `/health` for backend status, and has a reset button.

Important UI cases: no file, valid file, corrupt file selected, backend offline, timeout, 400/422/500 response, malformed JSON, missing metadata, zero detections, long class names, large image, reset, and changing API URL. The code assumes response keys exist; malformed successful responses can cause `KeyError` or Base64/PIL errors. Dashboard automated tests are **Not implemented in the current project.**

## 18. Contribution Answer

A defensible interview answer is:

> I implemented an end-to-end prototype for retail shelf monitoring. On the backend I built the FastAPI app and routes, startup dependency initialization, YOLO inference engine integration, OpenCV image validation/decoding/annotation/Base64 conversion, inventory counting, Pydantic response models, structured exception handlers, request logging, and health/model-info endpoints. I also built the React dashboard that uploads images, calls the API, displays annotations and analytics, and exports the result. I containerized the backend/frontend setup with Docker and Compose. For testing, I added a small pytest API suite covering the root endpoint, health endpoint, and invalid image upload. I would describe the testing as an initial smoke/negative layer, not as a complete QA automation framework, because unit, integration, load, security, CI, and end-to-end coverage are still missing.

Do not claim that you implemented mAP evaluation, authentication, a database, rate limiting, CI/CD, Kubernetes, or comprehensive automation: those are not in this repository.

## 19. Debugging Playbook

| Symptom                  | Possible cause                                          | Investigation                                              | Fix direction                                                           |
| ------------------------ | ------------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------- |
| API 500                  | model/inference/formatter bug                           | response body, server logs, correlation header, traceback  | isolate service; return safe error; fix failing component               |
| API 422                  | missing/wrong multipart field or route shape            | inspect request field name/content type and FastAPI detail | send `image`; clarify contract                                          |
| model does not load      | missing file, download/network, torch/Ultralytics issue | startup logs and import/model traceback                    | install dependencies, provide artifact/network, map readiness correctly |
| upload fails             | invalid bytes, timeout, wrong URL                       | OpenCV decode result, dashboard URL, HTTP status           | use valid image, fix URL, enforce limits                                |
| dashboard offline        | backend down, wrong health URL, network                 | sidebar API URL and `/health` request/logs                 | start backend or use Compose service URL                                |
| Docker backend fails     | `.env`, dependencies, model/system library              | `docker compose` logs/build output                         | fix env, packages, image/runtime config                                 |
| frontend cannot connect  | using `127.0.0.1` in container or wrong port            | inspect `API_URL` and Compose network                      | use `http://backend:8000/...` inside Compose                            |
| tests fail at collection | real model load or stale global service                 | traceback and dependency state                             | override dependencies and mock model                                    |
| unexpected detections    | model/version/config/input issue                        | log image dimensions, thresholds, raw mocked/real result   | check model artifact and evaluation set                                 |
| inference slow           | warmup, CPU, lock queue, large images                   | compare inference time and concurrent latency              | measure; scale workers/queue/batch as appropriate                       |

## 20. Interview Questions: 50 Project-Based Questions

Each answer is intentionally speakable in an interview.

### Software testing basics

1. **Question:** What is the main testable contract? **Short Answer:** A valid image should produce a safe, schema-valid response. **Detailed Answer:** Test input validation, pipeline behavior, response invariants, and errors separately. **Example:** `/api/v1/detect`.
2. **Question:** What is a positive test? **Short Answer:** A valid request that should succeed. **Detailed Answer:** It verifies expected behavior, not just absence of exceptions. **Example:** valid JPEG returns 200.
3. **Question:** What is negative testing? **Short Answer:** Deliberately sending invalid input or causing failure. **Detailed Answer:** It verifies graceful rejection and safe errors. **Example:** random bytes return 400.
4. **Question:** What is boundary testing? **Short Answer:** Testing values at and around limits. **Detailed Answer:** It catches off-by-one and validation errors. **Example:** confidence 0 and 1, empty detections.
5. **Question:** What is regression testing? **Short Answer:** Rechecking existing behavior after a change. **Detailed Answer:** It prevents a counter or validation change from breaking detection. **Example:** rerun valid and zero-detection flows after changing counting.

### API and HTTP

6. **Question:** Why does missing `image` return 422? **Short Answer:** FastAPI cannot satisfy the required request parameter. **Detailed Answer:** Framework validation happens before service code. **Example:** POST without multipart field.
7. **Question:** Why does invalid image content return 400? **Short Answer:** The request shape is valid but the business input is unusable. **Detailed Answer:** OpenCV cannot decode it and the service raises `InvalidImageError`. **Example:** `b"not_an_image"`.
8. **Question:** What is the difference between 404 and 405? **Short Answer:** Missing route versus wrong method. **Detailed Answer:** A route exists for 405 but not for 404. **Example:** POST `/health` versus GET `/missing`.
9. **Question:** What should a detection response contain? **Short Answer:** Detections, inventory, annotation, metadata, and success. **Detailed Answer:** Validate nested types and business totals. **Example:** `InferenceResponse`.
10. **Question:** What is an idempotent request here? **Short Answer:** Repeating it does not create a stored resource. **Detailed Answer:** Detection has no persistence, though ML output can vary by model/runtime. **Example:** repeated POSTs do not write database state.

### Python, FastAPI, and pytest

11. **Question:** Why use `TestClient`? **Short Answer:** It tests routes in process without a live server. **Detailed Answer:** It exercises request parsing, DI, handlers, and serialization. **Example:** current `client.get` tests.
12. **Question:** What is dependency injection doing? **Short Answer:** Supplying singleton detector/service objects to routes. **Detailed Answer:** It centralizes lifecycle and allows overrides for tests. **Example:** `Depends(get_shelf_service)`.
13. **Question:** What is weak about module-level `initialize_services()` in tests? **Short Answer:** It loads the real model during collection. **Detailed Answer:** Tests become slow, environment-dependent, and stateful. **Example:** 9.34-second baseline.
14. **Question:** What is a pytest fixture? **Short Answer:** Reusable controlled setup/teardown. **Detailed Answer:** Fixtures improve isolation and avoid repeated global setup. **Example:** fake detector and TestClient fixture.
15. **Question:** What should be asserted besides status code? **Short Answer:** Body schema, headers, invariants, and error content. **Detailed Answer:** A 200 with broken JSON is still a contract failure. **Example:** Base64 round trip and `total_objects`.

### Automation and mocking

16. **Question:** Why mock YOLO? **Short Answer:** To isolate software logic and make tests fast/deterministic. **Detailed Answer:** Force empty, multiple, malformed, and failing outputs. **Example:** fake `infer.return_value`.
17. **Question:** When should YOLO not be mocked? **Short Answer:** In at least a small deployment/model smoke test. **Detailed Answer:** Mocked tests cannot prove the artifact loads or real inference works. **Example:** one real-model startup check.
18. **Question:** What is test isolation? **Short Answer:** One test does not depend on another test's state. **Detailed Answer:** Restore dependency overrides and global services. **Example:** avoid stale `_service` and `_detector`.
19. **Question:** What is a reusable API helper? **Short Answer:** A function that sends standard requests and validates common structure. **Detailed Answer:** It reduces duplicated assertions while keeping scenario-specific checks. **Example:** `assert_valid_inference_response`.
20. **Question:** What is a flaky test risk here? **Short Answer:** Real model/runtime and timing dependence. **Detailed Answer:** Model downloads, hardware, and inference latency vary. **Example:** collection-time warmup.

### HTTP, Docker, and CI/CD

21. **Question:** What does the correlation ID do? **Short Answer:** Identifies a request in the response. **Detailed Answer:** It should let logs and client reports be joined, though current logs do not include the ID. **Example:** `X-Correlation-ID` middleware header.
22. **Question:** What does a 503 improve over current 500? **Short Answer:** It communicates service readiness failure. **Detailed Answer:** Clients and orchestrators can retry or remove the instance. **Example:** model unavailable at startup.
23. **Question:** What is Docker smoke testing? **Short Answer:** Build, start, call health, and exercise one detection. **Detailed Answer:** It validates packaging and runtime wiring. **Example:** backend 8000 and dashboard 4173.
24. **Question:** Why is `depends_on` insufficient for readiness? **Short Answer:** It controls start order, not health readiness. **Detailed Answer:** Frontend may start before backend accepts requests. **Example:** no Compose healthcheck exists.
25. **Question:** What should block deployment? **Short Answer:** Failed tests, build, scan, or post-deploy smoke. **Detailed Answer:** A quality gate must fail the workflow rather than deploy known-bad code. **Example:** proposed GitHub Actions pipeline.

### Debugging and computer vision

26. **Question:** How do you distinguish a software bug from a model error? **Short Answer:** Validate the pipeline contract separately from labeled model quality. **Detailed Answer:** Mock outputs to test parsing/counting, then use ground truth for accuracy. **Example:** `InventoryCounter` can be correct even if model recall is poor.
27. **Question:** What happens with zero detections? **Short Answer:** Backend should return an empty list and zero inventory. **Detailed Answer:** The API pipeline supports it, but dashboard empty-data behavior needs testing. **Example:** `Counter([])`.
28. **Question:** What does `IMREAD_COLOR` imply? **Short Answer:** Decoded images are handled as color matrices. **Detailed Answer:** Grayscale input is converted to a 3-channel representation. **Example:** `decode_image`.
29. **Question:** What is IoU? **Short Answer:** Intersection over Union of predicted and true boxes. **Detailed Answer:** It is an ML evaluation metric, not currently used to validate API output. **Example:** evaluate YOLO on labeled shelves.
30. **Question:** What is confidence threshold testing? **Short Answer:** Verify configured `conf` is passed to YOLO. **Detailed Answer:** Filtering is performed by Ultralytics, so inspect call arguments and outputs. **Example:** `self.confidence` from settings.

### Performance, reliability, system design

31. **Question:** Why load YOLO once? **Short Answer:** Model loading is expensive. **Detailed Answer:** Startup initialization and singleton reuse reduce request latency. **Example:** `initialize_services`.
32. **Question:** What does the lock mean for concurrency? **Short Answer:** Inference is serialized per engine. **Detailed Answer:** It protects shared model access but increases queue latency. **Example:** 10 simultaneous requests wait in `threading.Lock`.
33. **Question:** What is p95 latency? **Short Answer:** 95 percent of requests are no slower than that value. **Detailed Answer:** It exposes tail behavior better than average. **Example:** measure concurrent image uploads.
34. **Question:** What is the likely bottleneck? **Short Answer:** YOLO inference and serialized access. **Detailed Answer:** Confirm with timing and resource profiling rather than guessing. **Example:** compare inference time with total request latency.
35. **Question:** How would you improve overload behavior? **Short Answer:** Add limits, queue/backpressure, and scale model workers. **Detailed Answer:** Avoid unbounded memory and request timeouts. **Example:** bounded inference queue proposal.

### Project-specific

36. **Question:** What does `ShelfMonitoringService` own? **Short Answer:** Pipeline orchestration. **Detailed Answer:** It coordinates validation, decode, inference, annotation, counting, and formatting. **Example:** `process_image`.
37. **Question:** What does `InventoryCounter` own? **Short Answer:** Counts by class and sorts products. **Detailed Answer:** It has no YOLO/OpenCV dependency, making it ideal for unit tests. **Example:** `summarize`.
38. **Question:** What does `ResponseFormatter` own? **Short Answer:** Metadata, image encoding, and response construction. **Detailed Answer:** It creates nested Pydantic models. **Example:** `build_response`.
39. **Question:** Is `letterbox` used by the active flow? **Short Answer:** No. **Detailed Answer:** It exists as a utility but `ShelfMonitoringService` decodes then calls the detector directly. **Example:** test it separately or remove/document it.
40. **Question:** Is MIME type enforced by the API? **Short Answer:** No. **Detailed Answer:** OpenCV decodability controls acceptance. **Example:** valid JPEG bytes with `.txt` could pass.
41. **Question:** Does the project have authentication? **Short Answer:** No. **Detailed Answer:** No auth dependency, token, or authorization route exists. **Example:** all listed endpoints are public.
42. **Question:** Does it have a database? **Short Answer:** No. **Detailed Answer:** Inventory exists only in the response/session state. **Example:** no persistence module or database dependency.
43. **Question:** Does it have load tests? **Short Answer:** No. **Detailed Answer:** No load tool or performance test exists. **Example:** propose concurrent TestClient/httpx testing.
44. **Question:** What does the current invalid-image test really prove? **Short Answer:** Undecodable bytes receive 400. **Detailed Answer:** It does not prove extension/MIME policy. **Example:** filename `test.txt` is incidental.
45. **Question:** Why can model loading make API tests fragile? **Short Answer:** Tests depend on actual weights and hardware/dependencies. **Detailed Answer:** Collection can fail before a test runs. **Example:** module-level `initialize_services()`.
46. **Question:** What if the model returns an empty result list? **Short Answer:** `_parse_results` returns an empty list. **Detailed Answer:** The rest should build a zero inventory response. **Example:** explicit branch `if len(results) == 0`.
47. **Question:** What if class ID is not in `result.names`? **Short Answer:** Parsing can raise and become a server error. **Detailed Answer:** Unexpected model output needs a test and a policy. **Example:** mock invalid class index.
48. **Question:** What does the dashboard do if backend is unavailable? **Short Answer:** It shows an error and stops detection; sidebar reports offline. **Detailed Answer:** Detection catches fetch/network exceptions, while health catches any exception. **Example:** browser `fetch` timeout or connection failure.
49. **Question:** What contribution can you honestly claim? **Short Answer:** End-to-end prototype plus initial API tests. **Detailed Answer:** State the boundaries and gaps clearly. **Example:** three pytest tests, no CI/load/E2E.
50. **Question:** What would you improve first as a QA engineer? **Short Answer:** Mocked unit/API coverage for the successful and failure paths. **Detailed Answer:** It gives fast deterministic confidence before adding Docker/load/CI gates. **Example:** valid image, zero/multiple detections, schema and model exception tests.

## 21. Trick Questions and Precise Answers

- **Why 422 instead of 400?** Missing/wrong endpoint shape is rejected by FastAPI validation; undecodable image bytes reach application validation and currently produce 400.
- **What if a valid image contains no objects?** The model should return no boxes; backend should return 200 with empty detections and zero inventory. The dashboard must also handle empty DataFrames; that path needs a test.
- **What if two requests arrive simultaneously?** They can enter the async route, but the shared detector lock serializes `model.predict`; one waits. The synchronous call can also block the worker.
- **Why not load YOLO per request?** It is expensive and increases latency/memory. Current startup singleton loading is the correct general direction.
- **How test a nondeterministic model?** Mock deterministic outputs for software tests; use tolerance/contract assertions and a fixed labeled dataset for ML evaluation.
- **How test the API without testing the model?** Override the service or inject a fake detector that returns known boxes, then assert route, counting, formatting, and schema.
- **What if the model file is missing?** `_load_model` logs a warning that Ultralytics may download it, then attempts `YOLO(path)`. If that fails, it raises `ModelLoadError`; current handler is 500, though 503 is a better readiness contract.
- **What if inference takes five seconds?** Request latency includes that time; lock causes concurrent queueing. Measure p95/p99 and consider workers/queue/batching rather than hiding the delay.
- **What if frontend runs but backend is unavailable?** Dashboard health shows offline; detection catches connection exceptions and shows an error. It does not retry or queue.
- **What if the model returns unexpected detections?** Parsing may fail on missing attributes, invalid class IDs, or malformed tensors; this is an untested server-failure path and should be made explicit.

## 22. Final Cheat Sheet

1. **Project:** image in, YOLO detections/counts/annotated image out.
2. **Architecture:** React -> fetch -> FastAPI -> DI singleton service -> OpenCV -> YOLO -> counter -> formatter -> Pydantic JSON.
3. **Endpoints:** `/`, `/health`, `/model-info`, `/api/v1/detect`.
4. **Current tests:** root 200/name, health 200/healthy, invalid bytes 400.
5. **Current result:** 3 passed; no comprehensive suite.
6. **Positive:** valid JPEG/PNG should return 200 and valid nested response.
7. **Negative:** invalid bytes 400; missing field 422; wrong method 405; unknown path 404.
8. **Boundary:** confidence 0/1, class ID 0, empty detections, tiny/huge images.
9. **Mocking:** fake YOLO for fast deterministic software tests; real model for a small startup smoke test.
10. **Concurrency:** shared detector lock serializes inference; measure queue latency.
11. **Performance:** track average, p95, p99, RPS, CPU/GPU/memory.
12. **Errors:** invalid image 400; generic failures 500; model readiness would be better as 503.
13. **Docker:** build, start, health, ports, env, model, network, restart.
14. **CI:** lint/type/unit/API/integration/Docker/security, and block deployment on failure.
15. **Contribution:** backend, CV integration, dashboard, Docker, and initial pytest API tests.
16. **Not implemented:** unit suite, full API contract suite, E2E, load/reliability/security tests, CI/CD, auth, database, rate limit, ML metrics pipeline, and production readiness health checks.

A strong closing interview sentence is: “I understand both what works and what is unproven. The current project demonstrates the end-to-end path and a basic API smoke/negative layer; my first QA improvement would be deterministic mocked tests around valid, zero-detection, multiple-detection, schema, error, and concurrency contracts, followed by Docker and CI quality gates.”
