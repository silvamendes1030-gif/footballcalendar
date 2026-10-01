import os
import json
import requests
from datetime import datetime

API_KEY = os.environ["API_FOOTBALL_KEY"]

BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

TIMEZONE = "Africa/Luanda"


def api_get(endpoint, params=None):
    url = BASE_URL + endpoint

    resposta = requests.get(
        url,
        headers=HEADERS,
        params=params or {},
        timeout=60
    )

    resposta.raise_for_status()

    dados = resposta.json()

    if dados.get("errors"):
        raise Exception(str(dados["errors"]))

    return dados.get("response", [])


def jogo_formatado(jogo):
    fixture = jogo.get("fixture", {})
    league = jogo.get("league", {})
    teams = jogo.get("teams", {})
    goals = jogo.get("goals", {})

    casa = teams.get("home") or {}
    fora = teams.get("away") or {}

    return {
        "id": fixture.get("id"),

        "data": fixture.get("date"),

        "status": (
            fixture.get("status", {}).get("short")
        ),

        "competicao": {
            "id": league.get("id"),
            "nome": league.get("name"),
            "pais": league.get("country"),
            "logo": league.get("logo")
        },

        "casa": {
            "id": casa.get("id"),
            "nome": casa.get("name"),
            "logo": casa.get("logo")
        },

        "fora": {
            "id": fora.get("id"),
            "nome": fora.get("name"),
            "logo": fora.get("logo")
        },

        "resultado": {
            "casa": goals.get("home"),
            "fora": goals.get("away")
        },

        "estadio": (
            fixture.get("venue", {}).get("name")
            if fixture.get("venue")
            else None
        )
    }


def obter_proximos_jogos():
    """
    Busca os próximos jogos disponíveis.
    """

    resposta = api_get(
        "/fixtures",
        {
            "next": 100,
            "timezone": TIMEZONE
        }
    )

    return [
        jogo_formatado(jogo)
        for jogo in resposta
    ]


def obter_resultados_recentes():
    """
    Busca resultados recentes disponíveis.
    """

    resposta = api_get(
        "/fixtures",
        {
            "last": 100,
            "timezone": TIMEZONE
        }
    )

    return [
        jogo_formatado(jogo)
        for jogo in resposta
    ]


def obter_competicoes():
    """
    Obtém competições disponíveis.
    """

    resposta = api_get("/leagues")

    competicoes = []

    for item in resposta:

        league = item.get("league", {})
        country = item.get("country", {})

        competicoes.append({
            "id": league.get("id"),
            "nome": league.get("name"),
            "tipo": league.get("type"),
            "logo": league.get("logo"),
            "pais": country.get("name"),
            "bandeira": country.get("flag")
        })

    return competicoes


def construir_equipas(jogos):
    """
    Cria uma lista de equipas a partir dos jogos
    encontrados.
    """

    equipas = {}

    for jogo in jogos:

        for lado in ["casa", "fora"]:

            equipa = jogo.get(lado) or {}

            id_equipa = equipa.get("id")

            if not id_equipa:
                continue

            equipas[id_equipa] = {
                "id": id_equipa,
                "nome": equipa.get("nome"),
                "logo": equipa.get("logo")
            }

    return list(equipas.values())


def principais_resultados(resultados):

    resultados = [
        jogo for jogo in resultados
        if jogo.get("resultado", {}).get("casa") is not None
        and jogo.get("resultado", {}).get("fora") is not None
    ]

    resultados.sort(
        key=lambda x: x.get("data") or "",
        reverse=True
    )

    return resultados


def remover_duplicados(jogos):

    unicos = {}

    for jogo in jogos:

        identificador = jogo.get("id")

        if identificador:
            unicos[identificador] = jogo

    return list(unicos.values())


def main():

    print("======================================")
    print("FOOTBALL CALENDAR")
    print("Atualização dos dados")
    print("======================================")

    print()
    print("A obter próximos jogos...")

    proximos = obter_proximos_jogos()

    print(
        "Próximos jogos encontrados:",
        len(proximos)
    )

    print()
    print("A obter resultados...")

    resultados = obter_resultados_recentes()

    resultados = principais_resultados(
        resultados
    )

    print(
        "Resultados encontrados:",
        len(resultados)
    )

    print()
    print("A obter competições...")

    competicoes = obter_competicoes()

    print(
        "Competições encontradas:",
        len(competicoes)
    )

    todos = remover_duplicados(
        proximos + resultados
    )

    equipas = construir_equipas(
        todos
    )

    dados = {

        "atualizado_em":
            datetime.utcnow().isoformat() + "Z",

        "total_jogos":
            len(todos),

        "total_competicoes":
            len(competicoes),

        "total_equipas":
            len(equipas),

        "jogos":
            proximos,

        "resultados":
            resultados,

        "competicoes":
            competicoes,

        "equipas":
            equipas

    }

    with open(
        "dados.json",
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("======================================")
    print("ATUALIZAÇÃO CONCLUÍDA")
    print("======================================")

    print(
        "Jogos:",
        len(proximos)
    )

    print(
        "Resultados:",
        len(resultados)
    )

    print(
        "Competições:",
        len(competicoes)
    )

    print(
        "Equipas:",
        len(equipas)
    )


if __name__ == "__main__":
    main()
