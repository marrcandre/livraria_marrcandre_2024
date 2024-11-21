from rest_framework.serializers import (
    CharField,
    CurrentUserDefault,
    DateTimeField,
    HiddenField,
    ModelSerializer,
    SerializerMethodField,
    ValidationError,
)

from core.models import Compra, ItensCompra


class ItensCompraCreateUpdateSerializer(ModelSerializer):
    class Meta:
        model = ItensCompra
        fields = ("livro", "quantidade")

    def validate(self, item):
        if item["quantidade"] > item["livro"].quantidade:
            raise ValidationError({"quantidade": "Quantidade solicitada não disponível em estoque."})
        return item

    def validate_quantidade(self, value):
        if value <= 0:
            raise ValidationError("A quantidade deve ser maior que zero.")
        return value


class ItensCompraListSerializer(ModelSerializer):
    livro = CharField(source="livro.titulo", read_only=True)

    class Meta:
        model = ItensCompra
        fields = ("livro", "quantidade", "preco")
        depth = 1


class ItensCompraSerializer(ModelSerializer):
    total = SerializerMethodField()

    def get_total(self, item):
        return item.preco * item.quantidade

    class Meta:
        model = ItensCompra
        fields = ("livro", "quantidade", "preco", "total")
        depth = 1


class CompraCreateUpdateSerializer(ModelSerializer):
    usuario = HiddenField(default=CurrentUserDefault())
    itens = ItensCompraCreateUpdateSerializer(many=True)

    class Meta:
        model = Compra
        fields = ("usuario", "itens")

    def create(self, validated_data):
        # Remove os itens da validação para tratá-los separadamente
        itens = validated_data.pop("itens")
        usuario = validated_data["usuario"]

        # Verifica se já existe uma compra com status CARRINHO para o usuário
        compra, criada = Compra.objects.get_or_create(
            usuario=usuario, status=Compra.StatusCompra.CARRINHO, defaults=validated_data
        )

        # Atualiza ou adiciona os itens na compra
        for item in itens:
            # Tenta encontrar o item já existente
            item_existente = compra.itens.filter(livro=item["livro"]).first()

            if item_existente:
                # Incrementa a quantidade no item existente
                item_existente.quantidade += item["quantidade"]

                # Atualiza o preço para refletir o preço atual do livro
                item_existente.preco = item["livro"].preco
                item_existente.save()
            else:
                # Define o preço no novo item antes de criar
                item["preco"] = item["livro"].preco
                ItensCompra.objects.create(compra=compra, **item)

        compra.save()
        return compra

    def update(self, compra, validated_data):
        itens = validated_data.pop("itens", [])
        if itens:
            # Remove todos os itens antigos e substitui pelos novos
            compra.itens.all().delete()
            for item in itens:
                item["preco"] = item["livro"].preco  # Define o preço do livro atual
                ItensCompra.objects.create(compra=compra, **item)

        # Atualiza outros dados da compra, se fornecidos
        return super().update(compra, validated_data)


class CompraListSerializer(ModelSerializer):
    usuario = CharField(source="usuario.email", read_only=True)
    itens = ItensCompraListSerializer(many=True, read_only=True)

    class Meta:
        model = Compra
        fields = ("id", "usuario", "total", "itens")


class CompraSerializer(ModelSerializer):
    usuario = CharField(source="usuario.email", read_only=True)
    status = CharField(source="get_status_display", read_only=True)
    data = DateTimeField(read_only=True)
    tipo_pagamento = CharField(source="get_tipo_pagamento_display", read_only=True)  # novo campo
    itens = ItensCompraSerializer(many=True, read_only=True)

    class Meta:
        model = Compra
        fields = ("id", "usuario", "status", "total", "data", "tipo_pagamento", "itens")  # modificado
