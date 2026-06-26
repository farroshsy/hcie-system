from app.infrastructure.v3.v3_client import V3APIClient, resolve_v3_base_url


class SettingsStub:
    v3_api_base_url = None
    docker_env = True


class LocalSettingsStub:
    v3_api_base_url = None
    docker_env = False


def test_resolve_v3_base_url_uses_api_service_in_docker():
    assert resolve_v3_base_url(SettingsStub()) == "http://api:8000"


def test_resolve_v3_base_url_uses_localhost_outside_docker():
    assert resolve_v3_base_url(LocalSettingsStub()) == "http://localhost:8000"


def test_client_governance_state_path_matches_v3_router():
    client = V3APIClient(base_url="http://api:8000")
    url = client._governance_state_url("u1")
    assert url == "http://api:8000/v3/runtime/governance/state?user_id=u1"
    client.close()
