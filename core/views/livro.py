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
        # Busca o livro pelo ID
        livro = self.get_object()

        # Instancia o serializer passando os dados da requisição
        serializer = LivroAlterarPrecoSerializer(data=request.data)

        # Valida os dados e lança uma exceção se inválidos
        serializer.is_valid(raise_exception=True)

        # Atualiza o preço do livro com o valor validado
        livro.preco = serializer.validated_data["preco"]
        livro.save()

        # Retorna uma resposta de sucesso
        return Response(
            {"detail": f"Preço do livro '{livro.titulo}' atualizado para {livro.preco}."}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def ajustar_estoque(self, request, pk=None):
        # Recupera o livro pelo ID
        livro = self.get_object()

        # Serializa os dados de entrada com o livro como contexto
        serializer = LivroAjustarEstoqueSerializer(data=request.data, context={"livro": livro})
        serializer.is_valid(raise_exception=True)

        # Obtém a quantidade ajustada validada
        quantidade_ajuste = serializer.validated_data["quantidade"]

        # Ajusta o estoque e salva
        livro.quantidade += quantidade_ajuste
        livro.save()

        # Retorna uma resposta com o novo valor em estoque
        return Response(
            {"status": "Quantidade ajustada com sucesso", "novo_estoque": livro.quantidade}, status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["get"])
    def mais_vendidos(self, request):
        """
        Retorna os livros com mais de 10 unidades vendidas.
        """
        # Calcula o total de unidades vendidas para cada livro
        livros = Livro.objects.annotate(total_vendidos=Sum("itenscompra__quantidade")).filter(total_vendidos__gt=10)

        # Serializa os dados para a resposta
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
        # Obtém o usuário autenticado
        usuario = request.user
        if not usuario.is_authenticated:
            return Response(
                {"detail": "Autenticação necessária."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Obtém o livro pelo ID
        livro = get_object_or_404(Livro, pk=pk)

        # Tenta buscar ou criar um carrinho para o usuário
        compra, criada = Compra.objects.get_or_create(
            usuario=usuario,
            status=Compra.StatusCompra.CARRINHO,
            defaults={"tipo_pagamento": Compra.TipoPagamento.CARTAO_CREDITO},
        )

        # Verifica se o item já existe no carrinho
        item_existente = compra.itens.filter(livro=livro).first()
        if item_existente:
            # Incrementa a quantidade do item existente
            item_existente.quantidade += 1
            item_existente.save()
        else:
            # Adiciona o novo item no carrinho
            ItensCompra.objects.create(
                compra=compra,
                livro=livro,
                quantidade=1,
                preco=livro.preco,
            )

        # Serializa a compra completa
        compra_serializada = CompraSerializer(compra)

        # Retorna a resposta com a compra completa
        return Response(
            compra_serializada.data,
            status=status.HTTP_200_OK if not criada else status.HTTP_201_CREATED,
        )



