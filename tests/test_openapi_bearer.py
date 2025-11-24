def test_openapi_contains_bearer_scheme():
    import requests
    from fastapi.testclient import TestClient
    from app.api.main import app

    client = TestClient(app)
    openapi = client.get("/openapi.json").json()
    # components.securitySchemes must include a bearer scheme named HTTPBearer or bearerAuth
    schemes = openapi.get("components", {}).get("securitySchemes", {})
    assert schemes, "securitySchemes missing from openapi"

    # find an http bearer scheme
    found = False
    for name, scheme in schemes.items():
        if scheme.get("type") == "http" and scheme.get("scheme") and scheme.get("scheme").lower() == "bearer":
            found = True
            break
    assert found, f"no http bearer scheme found in securitySchemes: {schemes}"


def test_calculations_endpoint_requires_security():
    from fastapi.testclient import TestClient
    from app.api.main import app

    client = TestClient(app)
    openapi = client.get("/openapi.json").json()
    paths = openapi.get("paths", {})
    calc_post = paths.get("/calculations", {}).get("post")
    assert calc_post is not None, "/calculations POST operation missing from OpenAPI"
    # the operation should have a security requirement (non-empty list)
    security = calc_post.get("security")
    assert isinstance(security, list) and len(security) > 0, "/calculations POST must require security"
