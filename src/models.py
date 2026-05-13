from pydantic import BaseModel, Field
from typing import List


class Product(BaseModel):
    id: int
    name: str
    price: float


class CartItem(BaseModel):
    product: Product
    quantity: int


class CheckoutItem(BaseModel):
    id: int
    price: float = Field(gt=0)
    quantity: int = Field(gt=0)


class CheckoutCart(BaseModel):
    items: List[CheckoutItem] = Field(min_length=1)


class CheckoutUserData(BaseModel):
    id: int
    vip: bool


class CheckoutRequest(BaseModel):
    cart: CheckoutCart
    user: CheckoutUserData
    payment_token: str = Field(min_length=1)  # SEC-1: opaque token from gateway client SDK


class CheckoutResult(BaseModel):
    sucesso: bool
    transacao: str | None = None
    erro: str | None = None
