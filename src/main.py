from fastapi import FastAPI, HTTPException, Header

from src.cart import ShoppingCart
from src.checkout import authenticate_user, processar_tudo
from src.models import CheckoutRequest

app = FastAPI()

# LOG-5: in-memory cart store keyed by user_id (production: Redis with session token as key)
_cart_store: dict[int, ShoppingCart] = {}


@app.get("/")
def read_root():
    return {"status": "ok"}


@app.post("/checkout")
def checkout_endpoint(
    request: CheckoutRequest,
    authorization: str = Header(..., description="Bearer <session-token>"),
):
    # SEC-3: token vem do header HTTP, não do corpo da requisição.
    # O user_id reivindicado no body só é aceito se o token pertencer a ele.
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de autorização inválido. Use: Bearer <token>")

    token = authorization[len("Bearer "):]

    if not authenticate_user(token, request.user.id):
        raise HTTPException(status_code=401, detail="Não autorizado")

    result = processar_tudo(request)

    # LOG-5: esvazia o carrinho do usuário após checkout bem-sucedido
    if result.sucesso:
        _cart_store.pop(request.user.id, None)

    return result
