from alphaessaio import AlphaEssAuth
from tests.helpers import DOC_APP_ID, DOC_APP_SECRET


def test_create_headers_matches_documented_signature(auth: AlphaEssAuth, monkeypatch):
    monkeypatch.setattr("alphaessaio.auth.time.time", lambda: 1676353875)

    headers = auth.create_headers()

    assert headers == {
        "appId": DOC_APP_ID,
        "timeStamp": "1676353875",
        "sign": "0f023c2287b8f6b21b0994947465f8e"
        "9de0e1542567b1735bdc6c427336b9b6406285cd9"
        "4f9215c3e9af958df37fb11c2c9fe792713d8afbdb8c463359a1add8",
    }


def test_repr_hides_app_secret(auth: AlphaEssAuth):
    assert DOC_APP_SECRET not in repr(auth)
