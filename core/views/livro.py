from django.db.models.aggregates import Sum
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Compra, ItensCompra, Livro
from core.serializers import (
    CompraSerializer,
    LivroAdicionarAoCarrinhoSerializer,
    LivroAjustarEstoqueSerializer,
    LivroAlterarPrecoSerializer,
    LivroListSerializer,
    LivroRetrieveSerializer,
    LivroSerializer,
)


class LivroViewSet(ModelViewSet):
    queryset = Livro.objects.order_by("-id")
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["categoria__descricao", "editora__nome"]
    search_fields = ["titulo"]
    ordering_fields = ["titulo", "preco"]
    ordering = ["titulo"]

    def get_serializer_class(self):
        if self.action == "list":
            return LivroListSerializer
        elif self.action == "retrieve":
            return LivroRetrieveSerializer

        return LivroSerializer

    @action(detail=True, methods=["patch"])
    def alterar_preco(self, request, pk=None):
        livro = self.get_object()

        serializer = LivroAlterarPrecoSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        livro.preco = serializer.validated_data["preco"]
        livro.save()

        return Response(
            {"detail": f"Preço do livro '{livro.titulo}' atualizado para {livro.preco}."}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def ajustar_estoque(self, request, pk=None):
        livro = self.get_object()

        serializer = LivroAjustarEstoqueSerializer(data=request.data, context={"livro": livro})
        serializer.is_valid(raise_exception=True)

        quantidade_ajuste = serializer.validated_data["quantidade"]

        livro.quantidade += quantidade_ajuste
        livro.save()

        return Response(
            {"status": "Quantidade ajustada com sucesso", "novo_estoque": livro.quantidade}, status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["get"])
    def mais_vendidos(self, request):
        """
        Retorna os livros com mais de 10 unidades vendidas.
        """
        livros = Livro.objects.annotate(total_vendidos=Sum("itenscompra__quantidade")).filter(total_vendidos__gt=10)

        data = [
            {
                "id": livro.id,
                "titulo": livro.titulo,
                "total_vendidos": livro.total_vendidos,
            }
            for livro in livros
        ]

        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def adicionar_ao_carrinho(self, request, pk=None):
        livro = self.get_object()

        serializer = LivroAdicionarAoCarrinhoSerializer(data=request.data, context={"livro": livro})
        serializer.is_valid(raise_exception=True)
        quantidade = serializer.validated_data["quantidade"]

        compra, created = Compra.objects.get_or_create(usuario=request.user, status=Compra.StatusCompra.CARRINHO)

        item_existente = compra.itens.filter(livro=livro).first()

        if item_existente:
            item_existente.quantidade += quantidade
            item_existente.preco = livro.preco
            item_existente.save()
        else:
            ItensCompra.objects.create(compra=compra, livro=livro, quantidade=quantidade, preco=livro.preco)

        compra_serializada = CompraSerializer(compra)
        return Response(compra_serializada.data, status=status.HTTP_200_OK)
