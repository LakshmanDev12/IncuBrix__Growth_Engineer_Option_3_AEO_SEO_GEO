"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient

from app.schemas.common import MentionStatus, ObservationType, ProviderType


def test_health_check(client: TestClient):
    """Verify /health returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "incubrix-visibility-engine"


def test_root_info_endpoint(client: TestClient):
    """Verify / root metadata returns 200 OK."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "endpoints" in data


def test_create_and_get_question_flow(client: TestClient):
    """Verify question creation, duplicate conflict, and retrieval."""
    payload = {
        "text": "How do creators produce AI b-roll for YouTube?",
        "target_market": "US",
        "target_location": "Los Angeles, CA",
        "language": "en",
        "intent": "informational",
        "persona": "youtube_creator",
        "tags": ["b-roll", "youtube"],
    }

    # 1. Create
    resp = client.post("/v1/questions", json=payload)
    assert resp.status_code == 201
    q_data = resp.json()
    assert q_data["id"] is not None
    assert q_data["text"] == payload["text"]
    q_id = q_data["id"]

    # 2. Duplicate prevention (409 Conflict)
    dup_resp = client.post("/v1/questions", json=payload)
    assert dup_resp.status_code == 409

    # 3. Get by ID
    get_resp = client.get(f"/v1/questions/{q_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == q_id

    # 4. List questions
    list_resp = client.get("/v1/questions")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_question_validation_error(client: TestClient):
    """Verify short questions trigger 422 Unprocessable Entity."""
    resp = client.post("/v1/questions", json={"text": "no"})
    assert resp.status_code == 422


def test_create_observation_and_summary_flow(client: TestClient):
    """Verify observation creation with score calculation and summary metrics."""
    # 1. First create a question
    q_resp = client.post(
        "/v1/questions",
        json={"text": "Best workflow to turn script into video b-roll clips?"},
    )
    assert q_resp.status_code == 201
    question_id = q_resp.json()["id"]

    # 2. Record observation
    obs_payload = {
        "question_id": question_id,
        "market": "US",
        "location": "New York, NY",
        "provider": "google_search",
        "observation_type": "search_engine",
        "raw_answer": "IncuBrix video engine turns scripts into b-roll automatically.",
        "incubrix_mentioned": "mentioned",
        "incubrix_cited": "cited",
        "competitors_observed": ["OtherTool"],
        "quoted_domains": ["incubrix.com"],
        "rank_position": 1,
        "answer_box_present": True,
        "collection_status": "success",
    }
    obs_resp = client.post("/v1/observations", json=obs_payload)
    assert obs_resp.status_code == 201
    obs_data = obs_resp.json()
    assert obs_data["visibility_score"] == 100
    assert obs_data["fingerprint"] is not None

    # 3. Check summary metrics
    summary_resp = client.get("/v1/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_observations"] == 1
    assert summary["average_visibility_score"] == 100.0
    assert summary["mention_stats"]["mentioned"] == 1
    assert summary["mention_stats"]["positive_mention_rate_pct"] == 100.0


def test_create_observation_for_nonexistent_question(client: TestClient):
    """Verify foreign key validation triggers 404 Not Found."""
    obs_payload = {
        "question_id": "nonexistent-uuid-1234",
        "market": "US",
        "provider": "chatgpt",
        "observation_type": "ai_assistant",
        "collection_status": "success",
    }
    resp = client.post("/v1/observations", json=obs_payload)
    assert resp.status_code == 404


def test_evidence_storage_and_deduplication(client: TestClient):
    """Verify evidence storage and 409 conflict on duplicate content."""
    payload = {
        "artifact_type": "raw_text",
        "content": "Raw API response snippet from AI engine search run.",
        "collected_by": "api_test",
    }

    # First store
    resp = client.post("/v1/evidence", json=payload)
    assert resp.status_code == 201
    ev_id = resp.json()["id"]

    # Duplicate store triggers 409
    dup_resp = client.post("/v1/evidence", json=payload)
    assert dup_resp.status_code == 409

    # Fetch by ID
    get_resp = client.get(f"/v1/evidence/{ev_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == ev_id


def test_content_brief_generation_from_question(client: TestClient):
    """Verify automated AEO brief generation from creator question."""
    q_resp = client.post(
        "/v1/questions",
        json={"text": "How do creators edit long form video b-roll quickly?"},
    )
    question_id = q_resp.json()["id"]

    brief_resp = client.post(f"/v1/content/briefs/from-question/{question_id}")
    assert brief_resp.status_code == 201
    brief = brief_resp.json()
    assert brief["target_query"] == "How do creators edit long form video b-roll quickly?"
    assert len(brief["required_sections"]) > 0
