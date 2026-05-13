# Code Review — Correções de Bloqueadores de Produção

Branch: `feature/checkout-chaos`  
Data: 2026-05-12  
Revisor: Arquiteto de Software Sênior

---

## Escopo

Este documento registra as três falhas classificadas como **bloqueadoras de produção** identificadas em `src/checkout.py` e as correções aplicadas. Os critérios de bloqueio foram: violação direta de requisitos de segurança do PRD ou risco de comprometimento de dados/identidade em ambiente produtivo.

---

## SEC-1 — Dados de cartão transmitidos em texto plano

### Falha original

```python
# src/checkout.py (antes)
dados_pagamento = {
    "id_usuario": u_data['id'],
    "valor_total": round(val, 2),
    "info_cartao": "XXXX-XXXX-XXXX-1234"  # Dados sensíveis hardcoded
}
```

O payload enviado à API de pagamento incluía um campo `info_cartao` com dados de cartão em texto plano. Mesmo tratando-se de um valor mockado, o design estabelecia um padrão em que o backend receberia e retransmitiria dados PAN (Primary Account Number) sem criptografia, violando diretamente o requisito do PRD:

> "Todas as transações e dados do usuário devem ser criptografados."

Além da violação do PRD, esse padrão viola o PCI-DSS (Payment Card Industry Data Security Standard), que proíbe a transmissão de dados de cartão em texto claro.

### Solução aplicada

Adotado o modelo de **tokenização no lado do cliente**: o frontend obtém um `payment_token` opaco diretamente do SDK do gateway de pagamento (ex: Stripe.js, PagSeguro SDK). Esse token é de uso único e não expõe o número do cartão. O backend apenas encaminha o token — nunca toca nos dados reais.

```python
# src/models.py — novo campo no CheckoutRequest
class CheckoutRequest(BaseModel):
    cart: CheckoutCart
    user: CheckoutUserData
    payment_token: str = Field(min_length=1)  # token opaco do SDK do gateway
```

```python
# src/checkout.py (depois)
dados_pagamento = {
    "id_usuario": request.user.id,
    "valor_total": round(val, 2),
    "payment_token": request.payment_token,  # nenhum dado de cartão no backend
}
```

**Arquivos alterados:** `src/models.py`, `src/checkout.py`

---

## SEC-2 — Ausência de validação de entrada (input schema)

### Falha original

```python
# src/checkout.py (antes)
def processar_tudo(cart_data, u_data):
    if cart_data and 'items' in cart_data:
        for p in cart_data['items']:
            x1 = p['preco'] * p['qtd']   # KeyError se chave ausente
        ...
        if u_data['vip']:                 # KeyError se chave ausente
```

A função aceitava `cart_data` e `u_data` como dicionários crus sem nenhuma validação de schema. Consequências:

- Qualquer chave ausente causava `KeyError` não tratado (crash 500 em produção).
- Valores negativos ou zero em `quantity`/`price` eram aceitos silenciosamente, gerando totais incorretos ou negativos.
- O carrinho e o módulo de modelos (`cart.py`, `models.py`) já usavam Pydantic — o padrão era ignorado apenas no checkout.

### Solução aplicada

Criados modelos Pydantic com validação estrita para todo o contrato de entrada do checkout:

```python
# src/models.py
class CheckoutItem(BaseModel):
    id: int
    price: float = Field(gt=0)      # rejeita zero e negativos
    quantity: int = Field(gt=0)     # rejeita zero e negativos

class CheckoutCart(BaseModel):
    items: List[CheckoutItem] = Field(min_length=1)  # rejeita carrinho vazio

class CheckoutUserData(BaseModel):
    id: int
    vip: bool

class CheckoutRequest(BaseModel):
    cart: CheckoutCart
    user: CheckoutUserData
    payment_token: str = Field(min_length=1)
```

A assinatura da função foi atualizada para receber o modelo validado:

```python
# src/checkout.py (depois)
def processar_tudo(request: CheckoutRequest) -> dict:
    for item in request.cart.items:     # atributos tipados, sem KeyError
        val += item.price * item.quantity
```

A validação ocorre antes de `processar_tudo` ser chamada: o FastAPI (ou qualquer chamador) deserializa e valida o payload contra `CheckoutRequest`. Dados malformados são rejeitados com HTTP 422 antes de entrar na lógica de negócio.

**Arquivos alterados:** `src/models.py`, `src/checkout.py`

---

## SEC-3 — Ausência de autenticação e autorização

### Falha original

```python
# src/checkout.py (antes)
def processar_tudo(cart_data, u_data):
    dados_pagamento = {
        "id_usuario": u_data['id'],   # qualquer caller pode forjar este valor
        ...
    }
```

```python
# src/main.py (antes — sem endpoint de checkout)
@app.get("/")
def read_root():
    return {"status": "ok"}
```

Não havia nenhuma verificação de identidade: qualquer chamador podia passar um `u_data['id']` arbitrário e processar um pedido em nome de outro usuário. Além disso, `main.py` não expunha o checkout via HTTP, mas a função pública era utilizável sem qualquer guarda de autenticação.

### Solução aplicada

**Separação entre autenticação (quem é você?) e autorização (você pode fazer isso?):**

1. **Camada de autenticação** — função `authenticate_user` em `checkout.py` valida que o token de sessão pertence ao `user_id` reivindicado. Em produção, essa função decodifica e verifica um JWT; no mock, consulta um mapa `token → user_id`.

```python
# src/checkout.py
_VALID_SESSIONS: dict[str, int] = {
    "tok_user1_abc123": 1,
    "tok_user2_def456": 2,
}

def authenticate_user(token: str, user_id: int) -> bool:
    """Produção: decodificar JWT e verificar sub == user_id."""
    return _VALID_SESSIONS.get(token) == user_id
```

2. **Token via header HTTP** — o token de sessão é extraído do header `Authorization: Bearer <token>`, nunca do corpo da requisição. Isso impede que um usuário autenticado reivindique o `id` de outro no payload.

```python
# src/main.py
@app.post("/checkout")
def checkout_endpoint(
    request: CheckoutRequest,
    authorization: str = Header(...),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de autorização inválido.")

    token = authorization[len("Bearer "):]

    if not authenticate_user(token, request.user.id):
        raise HTTPException(status_code=401, detail="Não autorizado")

    return processar_tudo(request)
```

3. **`processar_tudo` como função interna** — a função não realiza autenticação internamente (responsabilidade única). A guarda está na borda HTTP, antes de qualquer lógica de negócio.

**Arquivos alterados:** `src/checkout.py`, `src/main.py`

---

## Resumo das alterações

| Arquivo | Tipo de alteração |
|---|---|
| `src/models.py` | Adicionados `CheckoutItem`, `CheckoutCart`, `CheckoutUserData`, `CheckoutRequest` |
| `src/checkout.py` | Removido dado de cartão hardcoded; função tipada com Pydantic; adicionada `authenticate_user` |
| `src/main.py` | Adicionado endpoint `POST /checkout` com extração de token via header e guarda de autenticação |

---

## LOG-1 — Conflito de regras de desconto entre `cart.py` e `checkout.py`

### Falha original

Dois conjuntos de regras de desconto coexistiam sem integração:

```python
# src/cart.py (antes)
if total > 1000:
    return total * 0.80   # 20%
if total > 500:
    return total * 0.90   # 10%

# src/checkout.py (antes) — regras diferentes e aplicadas após o frete
if val > 200:
    if u_data['vip']:
        val = val * 0.85  # 15%
    else:
        val = val * 0.95  # 5%
```

Consequências:
- Um cliente VIP com carrinho de R$800 veria 10% no carrinho, mas 5% (ou 15%) no checkout — valores diferentes na mesma compra.
- O desconto no checkout incidia sobre `(subtotal + frete)`, repassando desconto também sobre o frete.
- Adicionar qualquer nova regra (cupom, categoria) exigia editar dois arquivos em locais diferentes.

### Solução aplicada

Criado `src/discount.py` como **única fonte de verdade** para todas as regras de desconto. VIP recebe +5 pp sobre qualquer faixa ativa (máximo 25%).

```python
# src/discount.py
def apply_discount(subtotal: float, is_vip: bool = False) -> float:
    if subtotal > 1000:
        rate = 0.20
    elif subtotal > 500:
        rate = 0.10
    else:
        rate = 0.0
    if is_vip and rate > 0:
        rate = min(rate + 0.05, 0.25)
    return subtotal * (1 - rate)
```

`cart.py` delega para `apply_discount` (sem VIP — carrinho não conhece o usuário). `checkout.py` também delega, passando `is_vip`, e aplica o desconto **antes** do frete:

```python
# src/checkout.py (depois)
total_com_desconto = apply_discount(subtotal, is_vip=request.user.vip)
total_final = round(total_com_desconto + _SHIPPING_COST, 2)
```

**Arquivos alterados:** `src/discount.py` (novo), `src/cart.py`, `src/checkout.py`

---

## LOG-2 — Pedidos acima de R$9.999 rejeitados silenciosamente

### Falha original

```python
# src/checkout.py (antes)
if json['valor_total'] > 0 and json['valor_total'] < 9999:
    return FakeResponse(200, {"status": "pagamento_aprovado", ...})
else:
    return FakeResponse(400, {"status": "pagamento_recusado", "motivo": "valor_invalido"})
```

Qualquer pedido com valor `>= R$9.999` era recusado com o motivo genérico `"valor_invalido"`. Em um e-commerce de tecnologia (notebooks, servidores), pedidos nessa faixa são rotineiros. O chamador recebia `"api_pagamento_offline"` como erro, não havendo forma de distinguir falha real de rejeição por limite.

### Solução aplicada

O limite arbitrário foi removido. A única condição para aprovação é `valor_total > 0`, que é a validação semanticamente correta. Limites reais de transação são configurados diretamente no gateway de pagamento contratado, não no backend da aplicação.

```python
# src/checkout.py (depois)
if json["valor_total"] > 0:
    return FakeResponse(200, {"status": "pagamento_aprovado", ...})
```

**Arquivos alterados:** `src/checkout.py`

---

## LOG-3 — Verificação de estoque hardcoded e não substituível

### Falha original

```python
# src/checkout.py (antes)
for p in cart_data['items']:
    estoque_disponivel = 10  # mock fixo dentro do loop
    if p['qtd'] <= estoque_disponivel:
        ...
```

O valor `10` era reinstanciado a cada iteração do loop, sem possibilidade de consulta real ao serviço de inventário. Não havia forma de testar o caminho de "estoque insuficiente" sem modificar o código-fonte.

### Solução aplicada

A verificação de estoque foi extraída para uma função injetável via parâmetro com default. `StockChecker` é um alias de `Callable[[int, int], bool]`, o que permite substituir a implementação em testes ou para diferentes backends (banco de dados, API de ERP) sem alterar `processar_tudo`.

```python
# src/checkout.py (depois)
StockChecker = Callable[[int, int], bool]

def _default_stock_checker(_product_id: int, quantity: int) -> bool:
    """Production: call inventory service API."""
    return quantity <= 10

def processar_tudo(
    request: CheckoutRequest,
    stock_checker: StockChecker = _default_stock_checker,
) -> CheckoutResult:
    ...
    if not stock_checker(item.id, item.quantity):
        return CheckoutResult(sucesso=False, erro="estoque_insuficiente")
```

Exemplo de uso em teste:

```python
def test_estoque_insuficiente():
    sem_estoque = lambda pid, qty: False
    result = processar_tudo(request_valido, stock_checker=sem_estoque)
    assert result.sucesso is False
    assert result.erro == "estoque_insuficiente"
```

**Arquivos alterados:** `src/checkout.py`

---

## LOG-4 — Tipo de retorno inconsistente

### Falha original

```python
# src/checkout.py (antes) — quatro tipos de retorno diferentes
return "Erro de estoque"           # str
return "Carrinho vazio"            # str
return "Dados inválidos"           # str
return {"sucesso": True, ...}      # dict
return {"sucesso": False, ...}     # dict
```

Qualquer chamador precisava fazer `isinstance(result, dict)` antes de acessar campos, tornando o contrato implícito e quebrável silenciosamente.

### Solução aplicada

Adicionado `CheckoutResult` em `src/models.py`. Todos os caminhos de retorno emitem o mesmo tipo; FastAPI serializa automaticamente para JSON.

```python
# src/models.py
class CheckoutResult(BaseModel):
    sucesso: bool
    transacao: str | None = None
    erro: str | None = None
```

```python
# src/checkout.py (depois) — retorno único em todos os paths
return CheckoutResult(sucesso=False, erro="estoque_insuficiente")
return CheckoutResult(sucesso=True, transacao=body["transacao_id"])
return CheckoutResult(sucesso=False, erro="api_pagamento_offline")
```

Os caminhos de string (`"Carrinho vazio"`, `"Dados inválidos"`) foram eliminados como efeito colateral da validação Pydantic introduzida em SEC-2.

**Arquivos alterados:** `src/models.py`, `src/checkout.py`

---

## LOG-5 — Carrinho não esvaziado após checkout bem-sucedido

### Falha original

Após pagamento aprovado, o carrinho do usuário permanecia intacto. Um segundo `POST /checkout` com os mesmos dados processaria o mesmo pedido novamente, gerando cobrança duplicada.

### Solução aplicada

O endpoint é a camada responsável pelo ciclo de vida do carrinho. `processar_tudo` retorna `CheckoutResult` e o endpoint, ao receber `sucesso=True`, remove o carrinho da sessão do usuário. A arquitetura do store (dict em memória) foi desenhada para ser substituída por Redis sem alterar o endpoint.

```python
# src/main.py
# in-memory cart store keyed by user_id (production: Redis with session token as key)
_cart_store: dict[int, ShoppingCart] = {}

@app.post("/checkout")
def checkout_endpoint(request, authorization):
    ...
    result = processar_tudo(request)
    if result.sucesso:
        _cart_store.pop(request.user.id, None)
    return result
```

`processar_tudo` não conhece o `ShoppingCart` — responsabilidade única preservada. O esvaziamento é efeito colateral do sucesso, não lógica de negócio do checkout.

**Arquivos alterados:** `src/main.py`

---

## Resumo das alterações (completo)

| Arquivo | Alterações |
|---|---|
| `src/discount.py` | Novo — única fonte de verdade para regras de desconto |
| `src/models.py` | `CheckoutItem`, `CheckoutCart`, `CheckoutUserData`, `CheckoutRequest`, `CheckoutResult` |
| `src/cart.py` | `calculate_total_with_discount` delegada para `apply_discount` |
| `src/checkout.py` | SEC-1: payment_token; SEC-2: Pydantic; SEC-3: authenticate_user; LOG-1: apply_discount; LOG-2: sem cap R$9.999; LOG-3: stock_checker injetável; LOG-4: CheckoutResult |
| `src/main.py` | SEC-3: auth via header; LOG-5: cart clearing pós-checkout |

## Itens ainda pendentes (fora do escopo desta entrega)

- **SOLID-SRP** `processar_tudo` ainda acumula múltiplas responsabilidades — decomposição em `StockValidator`, `PriceCalculator`, `PaymentGateway` recomendada para a próxima sprint.
