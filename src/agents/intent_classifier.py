"""
Classifies free-text user messages into FINOVA intents.
Simple keyword-based router — no external model needed.
"""

INTENT_KEYWORDS: dict[str, list[str]] = {
    "saldo": ["saldo", "conta", "dinheiro", "quanto tenho", "saldo atual"],
    "extrato": ["extrato", "transaç", "gastei", "recebi", "compras", "movimentaç"],
    "carteira": ["carteira", "investimento", "ações", "acoes", "bolsa", "bitcoin", "btc", "fundo"],
    "resumo_diario": ["resumo", "hoje", "dia", "diario", "manha"],
    "relatorio_mensal": ["relatorio", "mês", "mes", "mensal", "mensal"],
}

_DEFAULT_INTENT = "ajuda"


def classify_intent(text: str) -> str:
    normalized = text.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in normalized for kw in keywords):
            return intent
    return _DEFAULT_INTENT
