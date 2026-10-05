from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_mode_mock():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["mode"] == "mock"


def test_detection_francais():
    r = client.post("/detect-language",
                    json={"text": "Je ne peux plus acceder a mon compte."})
    assert r.status_code == 200
    assert r.json()["language"] == "fr"


def test_detection_anglais():
    r = client.post("/detect-language",
                    json={"text": "I cannot log into my account."})
    assert r.status_code == 200
    assert r.json()["language"] == "en"


def test_detection_arabe():
    r = client.post("/detect-language",
                    json={"text": "لا أستطيع الدخول إلى حسابي"})
    assert r.status_code == 200
    assert r.json()["language"] == "ar"


def test_texte_trop_court_rejete():
    assert client.post("/detect-language", json={"text": "ab"}).status_code == 422


def test_champ_text_absent_rejete():
    assert client.post("/detect-language", json={}).status_code == 422


def test_fournisseur_en_panne_renvoie_503(monkeypatch):
    def panne(text):
        raise RuntimeError("secret interne: https://prive.example/key=abc")

    monkeypatch.setattr("app.main.provider.detect_language", panne)
    r = client.post("/detect-language", json={"text": "Bonjour tout le monde"})
    assert r.status_code == 503
    assert "secret" not in r.text  # aucun detail technique ne fuit


def test_confiance_faible_demande_revue(monkeypatch):
    monkeypatch.setattr("app.main.REVIEW_THRESHOLD", 0.99)
    r = client.post("/detect-language", json={"text": "Bonjour mon ami"})
    assert r.json()["requires_review"] is True