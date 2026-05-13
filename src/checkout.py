from typing import Callable

from src.discount import apply_discount
from src.models import CheckoutRequest, CheckoutResult

# ---------------------------------------------------------------------------
# SEC-3: Session store (production: Redis + JWT validation)
# Maps opaque session token -> authenticated user_id
# ---------------------------------------------------------------------------
_VALID_SESSIONS: dict[str, int] = {
    "tok_user1_abc123": 1,
    "tok_user2_def456": 2,
}


def authenticate_user(token: str, user_id: int) -> bool:
    """
    Validates that the token is active and belongs to the claimed user.
    Production: decode and verify JWT signature, then check sub == user_id.
    """
    return _VALID_SESSIONS.get(token) == user_id


# ---------------------------------------------------------------------------
# Payment gateway mock
# ---------------------------------------------------------------------------
class FakeResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


def fake_post(url, json):
    print(f"--- Simulando POST para API de pagamento: {url} ---")
    # LOG-2: removed arbitrary R$9.999 cap that silently rejected high-value orders
    if json["valor_total"] > 0:
        print("--- Pagamento APROVADO (simulado) ---")
        return FakeResponse(200, {"status": "pagamento_aprovado", "transacao_id": "xyz123abc"})
    print("--- Pagamento RECUSADO (simulado) ---")
    return FakeResponse(400, {"status": "pagamento_recusado", "motivo": "valor_invalido"})


# ---------------------------------------------------------------------------
# LOG-3: Stock check extracted as injectable callable
# Production: replace with a real InventoryService client
# ---------------------------------------------------------------------------
StockChecker = Callable[[int, int], bool]


def _default_stock_checker(_product_id: int, quantity: int) -> bool:
    """Production: call inventory service API."""
    return quantity <= 10  # TODO: replace with real inventory API call


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------
_SHIPPING_COST = 15.50


def processar_tudo(
    request: CheckoutRequest,
    stock_checker: StockChecker = _default_stock_checker,
) -> CheckoutResult:
    """
    Processa o checkout completo a partir de uma requisição validada.
    Pré-condição: autenticação já verificada pelo chamador via authenticate_user.
    """
    print("Iniciando processamento de checkout...")
    subtotal = 0.0

    for item in request.cart.items:
        print(f"Verificando estoque para o produto ID: {item.id}...")
        # LOG-3: delegated to injectable stock_checker — swappable without touching this function
        if not stock_checker(item.id, item.quantity):
            return CheckoutResult(sucesso=False, erro="estoque_insuficiente")
        print(f"Estoque OK para {item.quantity} unidades do produto {item.id}.")
        subtotal += item.price * item.quantity

    print(f"Subtotal: {subtotal}")

    # LOG-1: single unified discount engine — no more conflicting rules between cart and checkout
    # Discount applied on subtotal before shipping (shipping is never discounted)
    total_com_desconto = apply_discount(subtotal, is_vip=request.user.vip)
    total_final = round(total_com_desconto + _SHIPPING_COST, 2)
    print(f"Total com desconto e frete: {total_final}")

    dados_pagamento = {
        "id_usuario": request.user.id,
        "valor_total": total_final,
        # SEC-1: payment_token is an opaque token from the gateway client SDK
        "payment_token": request.payment_token,
    }

    res = fake_post("https://api.pagamento.exemplo/processar", json=dados_pagamento)

    if res.status_code == 200:
        body = res.json()
        if body["status"] == "pagamento_aprovado":
            print(f"Checkout finalizado! ID da transação: {body['transacao_id']}")
            # LOG-4: consistent typed return in all paths
            return CheckoutResult(sucesso=True, transacao=body["transacao_id"])
        return CheckoutResult(sucesso=False, erro="problema_na_api_de_pagamento")

    print("API de pagamento retornou um erro.")
    return CheckoutResult(sucesso=False, erro="api_pagamento_offline")
