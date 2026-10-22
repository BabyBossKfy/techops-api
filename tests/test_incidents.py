INCIDENT = {
    "title": "Groupe électrogène à l'arrêt",
    "description": "Le groupe ne démarre pas après la coupure de 14 h.",
    "equipment": "GE-02",
    "severity": "critique",
}


def _create(client, headers, **overrides):
    response = client.post("/incidents", json={**INCIDENT, **overrides}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_agent_can_create_incident(client, agent_headers):
    incident = _create(client, agent_headers)
    assert incident["status"] == "ouvert"
    assert incident["severity"] == "critique"
    assert incident["reporter_id"] > 0


def test_incidents_require_authentication(client):
    assert client.get("/incidents").status_code == 401
    assert client.post("/incidents", json=INCIDENT).status_code == 401


def test_invalid_severity_is_rejected(client, agent_headers):
    response = client.post(
        "/incidents", json={**INCIDENT, "severity": "apocalyptique"}, headers=agent_headers
    )
    assert response.status_code == 422


def test_list_can_filter_by_severity(client, agent_headers):
    _create(client, agent_headers)
    _create(client, agent_headers, title="Onduleur en alarme", severity="faible")

    response = client.get("/incidents", params={"severity": "faible"}, headers=agent_headers)
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()]
    assert titles == ["Onduleur en alarme"]


def test_unknown_incident_returns_404(client, agent_headers):
    assert client.get("/incidents/9999", headers=agent_headers).status_code == 404


def test_agent_cannot_change_status_but_supervisor_can(
    client, agent_headers, supervisor_headers
):
    incident = _create(client, agent_headers)
    url = f"/incidents/{incident['id']}/status"

    assert client.patch(url, json={"status": "resolu"}, headers=agent_headers).status_code == 403

    response = client.patch(url, json={"status": "resolu"}, headers=supervisor_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "resolu"

    response = client.get("/incidents", params={"status": "resolu"}, headers=agent_headers)
    assert [item["id"] for item in response.json()] == [incident["id"]]


def test_only_admin_can_delete(client, agent_headers, admin_headers):
    incident = _create(client, agent_headers)
    url = f"/incidents/{incident['id']}"

    assert client.delete(url, headers=agent_headers).status_code == 403
    assert client.delete(url, headers=admin_headers).status_code == 204
    assert client.get(url, headers=admin_headers).status_code == 404
