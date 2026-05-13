from typing import List
from src.discount import apply_discount
from src.models import CartItem, Product

class ShoppingCart:
    """
    Representa um carrinho de compras.
    """
    def __init__(self):
        """
        Inicializa um carrinho de compras com uma lista vazia de itens.
        """
        self.items: List[CartItem] = []

    def add_item(self, product: Product, quantity: int):
        """
        Adiciona um produto ao carrinho. Se o produto já existir,
        a quantidade é somada à existente.

        Args:
            product (Product): O produto a ser adicionado.
            quantity (int): A quantidade a ser adicionada.
        """
        for item in self.items:
            if item.product.id == product.id:
                item.quantity += quantity
                return

        self.items.append(CartItem(product=product, quantity=quantity))

    def remove_item(self, product_id: int):
        """
        Remove um item do carrinho pelo ID do produto.

        Args:
            product_id (int): O ID do produto a ser removido.
        """
        self.items = [item for item in self.items if item.product.id != product_id]

    def calculate_total(self) -> float:
        """
        Calcula o valor total dos itens no carrinho.

        Returns:
            float: O valor total do carrinho.
        """
        return sum(item.product.price * item.quantity for item in self.items)

    def calculate_total_with_discount(self) -> float:
        """
        Calcula o valor total com desconto aplicado.
        - 10% de desconto para compras acima de R$ 500.
        - 20% de desconto para compras acima de R$ 1000.

        Returns:
            float: O valor total com o desconto aplicado.
        """
        return apply_discount(self.calculate_total())
