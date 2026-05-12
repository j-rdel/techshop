import pytest
from src.cart import ShoppingCart
from src.models import Product


class TestShoppingCart:

    # -------------------------------------------------------------------------
    # Fixtures
    # -------------------------------------------------------------------------

    @pytest.fixture
    def cart(self) -> ShoppingCart:
        """Retorna um carrinho de compras vazio."""
        return ShoppingCart()

    @pytest.fixture
    def product_a(self) -> Product:
        """Produto com preço R$ 300."""
        return Product(id=1, name="Teclado Mecânico", price=300.0)

    @pytest.fixture
    def product_b(self) -> Product:
        """Produto com preço R$ 250."""
        return Product(id=2, name="Mouse Gamer", price=250.0)

    @pytest.fixture
    def product_expensive(self) -> Product:
        """Produto com preço R$ 600."""
        return Product(id=3, name="Monitor 4K", price=600.0)

    # -------------------------------------------------------------------------
    # add_item
    # -------------------------------------------------------------------------

    def test_add_new_item(self, cart: ShoppingCart, product_a: Product) -> None:
        """Caminho feliz: adicionar um produto novo ao carrinho."""
        # Arrange
        quantity = 2

        # Act
        cart.add_item(product_a, quantity)

        # Assert
        assert len(cart.items) == 1
        assert cart.items[0].product.id == product_a.id
        assert cart.items[0].quantity == 2

    def test_add_same_item_increments_quantity(
        self, cart: ShoppingCart, product_a: Product
    ) -> None:
        """Caminho feliz: adicionar o mesmo produto soma a quantidade."""
        # Arrange
        cart.add_item(product_a, 1)

        # Act
        cart.add_item(product_a, 3)

        # Assert
        assert len(cart.items) == 1
        assert cart.items[0].quantity == 4

    def test_add_multiple_different_items(
        self, cart: ShoppingCart, product_a: Product, product_b: Product
    ) -> None:
        """Caminho feliz: adicionar produtos distintos cria entradas separadas."""
        # Arrange / Act
        cart.add_item(product_a, 1)
        cart.add_item(product_b, 2)

        # Assert
        assert len(cart.items) == 2

    def test_add_item_with_zero_quantity(
        self, cart: ShoppingCart, product_a: Product
    ) -> None:
        """Erro: adicionar quantidade zero deve inserir o item com quantity 0."""
        # Arrange
        quantity = 0

        # Act
        cart.add_item(product_a, quantity)

        # Assert
        assert cart.items[0].quantity == 0

    def test_add_item_with_negative_quantity(
        self, cart: ShoppingCart, product_a: Product
    ) -> None:
        """Erro: quantidade negativa não deve alterar o total para positivo."""
        # Arrange / Act
        cart.add_item(product_a, -1)

        # Assert
        assert cart.items[0].quantity == -1
        assert cart.calculate_total() < 0

    # -------------------------------------------------------------------------
    # remove_item
    # -------------------------------------------------------------------------

    def test_remove_existing_item(
        self, cart: ShoppingCart, product_a: Product
    ) -> None:
        """Caminho feliz: remover um item existente esvazia o carrinho."""
        # Arrange
        cart.add_item(product_a, 1)

        # Act
        cart.remove_item(product_a.id)

        # Assert
        assert len(cart.items) == 0

    def test_remove_one_of_multiple_items(
        self, cart: ShoppingCart, product_a: Product, product_b: Product
    ) -> None:
        """Caminho feliz: remover apenas o produto correto entre vários."""
        # Arrange
        cart.add_item(product_a, 1)
        cart.add_item(product_b, 2)

        # Act
        cart.remove_item(product_a.id)

        # Assert
        assert len(cart.items) == 1
        assert cart.items[0].product.id == product_b.id

    def test_remove_nonexistent_item_does_not_raise(
        self, cart: ShoppingCart
    ) -> None:
        """Erro: remover ID inexistente não deve lançar exceção."""
        # Arrange
        nonexistent_id = 999

        # Act / Assert
        cart.remove_item(nonexistent_id)  # não deve lançar exceção
        assert len(cart.items) == 0

    # -------------------------------------------------------------------------
    # calculate_total
    # -------------------------------------------------------------------------

    def test_total_empty_cart(self, cart: ShoppingCart) -> None:
        """Caminho feliz: carrinho vazio retorna total zero."""
        # Arrange / Act
        total = cart.calculate_total()

        # Assert
        assert total == 0.0

    def test_total_single_item(
        self, cart: ShoppingCart, product_a: Product
    ) -> None:
        """Caminho feliz: total com um item é preço × quantidade."""
        # Arrange
        cart.add_item(product_a, 3)

        # Act
        total = cart.calculate_total()

        # Assert
        assert total == 900.0  # 300 * 3

    def test_total_multiple_items(
        self, cart: ShoppingCart, product_a: Product, product_b: Product
    ) -> None:
        """Caminho feliz: total é a soma de todos os itens."""
        # Arrange
        cart.add_item(product_a, 2)  # 600
        cart.add_item(product_b, 1)  # 250

        # Act
        total = cart.calculate_total()

        # Assert
        assert total == 850.0

    # -------------------------------------------------------------------------
    # calculate_total_with_discount
    # -------------------------------------------------------------------------

    def test_no_discount_below_500(
        self, cart: ShoppingCart, product_a: Product
    ) -> None:
        """Caminho feliz: total abaixo de R$500 não recebe desconto."""
        # Arrange
        cart.add_item(product_a, 1)  # R$ 300

        # Act
        total = cart.calculate_total_with_discount()

        # Assert
        assert total == 300.0

    def test_discount_10_percent_above_500(
        self, cart: ShoppingCart, product_a: Product, product_b: Product
    ) -> None:
        """Caminho feliz: total acima de R$500 recebe 10% de desconto."""
        # Arrange
        cart.add_item(product_a, 1)  # 300
        cart.add_item(product_b, 1)  # 250 → total 550

        # Act
        total = cart.calculate_total_with_discount()

        # Assert
        assert total == pytest.approx(495.0)  # 550 * 0.90

    def test_discount_20_percent_above_1000(
        self, cart: ShoppingCart, product_expensive: Product
    ) -> None:
        """Caminho feliz: total acima de R$1000 recebe 20% de desconto."""
        # Arrange
        cart.add_item(product_expensive, 2)  # 1200

        # Act
        total = cart.calculate_total_with_discount()

        # Assert
        assert total == pytest.approx(960.0)  # 1200 * 0.80

    def test_no_discount_at_exactly_500(
        self, cart: ShoppingCart, product_b: Product
    ) -> None:
        """Erro de fronteira: total exatamente igual a R$500 não recebe desconto."""
        # Arrange
        cart.add_item(product_b, 2)  # 500

        # Act
        total = cart.calculate_total_with_discount()

        # Assert
        assert total == 500.0

    def test_no_discount_at_exactly_1000(self) -> None:
        """Erro de fronteira: total exatamente igual a R$1000 recebe apenas 10%."""
        # Arrange
        product_mid = Product(id=10, name="SSD", price=500.0)
        cart = ShoppingCart()
        cart.add_item(product_mid, 2)  # 500 * 2 = 1000 exato

        # Act
        total = cart.calculate_total_with_discount()

        # Assert
        # 1000 > 500 é verdadeiro → aplica 10% de desconto; só >1000 aciona 20%
        assert total == pytest.approx(900.0)
