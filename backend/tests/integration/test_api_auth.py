"""Autenticação de ponta a ponta: cadastro, login e rotas protegidas (AQ-24)."""


def test_cadastro_login_e_dados_do_treinador(api, client):
    headers = api.coach(email="Ana@Teste.com", name="Ana Souza")
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    me = response.json()
    assert me["name"] == "Ana Souza"
    assert me["email"] == "ana@teste.com"  # e-mail guardado em minúsculas
    assert "password" not in me and "password_hash" not in me  # senha nunca volta


def test_email_repetido_e_recusado(api, client):
    api.coach(email="repetido@teste.com")
    response = client.post(
        "/auth/register",
        json={"name": "Outro", "email": "repetido@teste.com", "password": api.password},
    )
    assert response.status_code == 409


def test_login_com_senha_errada_ou_email_inexistente_tem_a_mesma_resposta(api, client):
    api.coach(email="login@teste.com")
    errada = client.post("/auth/login", data={"username": "login@teste.com", "password": "x" * 10})
    inexistente = client.post(
        "/auth/login", data={"username": "ninguem@teste.com", "password": api.password}
    )
    assert errada.status_code == inexistente.status_code == 401
    assert errada.json()["detail"] == inexistente.json()["detail"]  # não revela quem existe


def test_rotas_protegidas_exigem_token_valido(client):
    assert client.get("/athletes").status_code == 401
    assert client.get("/dashboard").status_code == 401
    invalido = {"Authorization": "Bearer token-invalido"}
    assert client.get("/auth/me", headers=invalido).status_code == 401