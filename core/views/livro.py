from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Livro
from core.serializers import LivroDetailSerializer, LivroListSerializer, LivroSerializer


class LivroViewSet(ModelViewSet):
    queryset = Livro.objects.all()
    serializer_class = LivroSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["categoria__descricao", "editora__nome"]
    search_fields = ["titulo"]
    ordering_fields = ["titulo", "preco"]
    ordering = ["titulo"]

    def get_serializer_class(self):
        if self.action == "list":
            return LivroListSerializer
        elif self.action == "retrieve":
            return LivroDetailSerializer
        return LivroSerializer

    @action(detail=True, methods=["patch"], url_path="alterar_preco")
    def alterar_preco(self, request, pk=None):
        # Busca o livro pelo ID
        livro = get_object_or_404(Livro, pk=pk)

        # Obtém o novo preço do corpo da requisição
        novo_preco = request.data.get("preco")

        # Verifica se o preço foi fornecido e se é um número válido
        if novo_preco is None:
            return Response({"detail": "O preço é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            novo_preco = float(novo_preco)
        except ValueError:
            return Response({"detail": "O preço deve ser um número válido."}, status=status.HTTP_400_BAD_REQUEST)

        # Atualiza o preço do livro e salva
        livro.preco = novo_preco
        livro.save()

        # Retorna uma resposta de sucesso
        return Response(
            {"detail": f"Preço do livro '{livro.titulo}' atualizado para {livro.preco}."}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def ajustar_estoque(self, request, pk=None):
        # Recupera o livro pelo ID
        livro = get_object_or_404(Livro, pk=pk)

        # Recupera o valor de ajuste passado no body da requisição
        quantidade_ajuste = request.data.get("quantidade")

        if quantidade_ajuste is None:
            return Response(
                {"erro": "Por favor, informe uma quantidade para ajustar."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Tenta converter o valor para um número inteiro
            quantidade_ajuste = int(quantidade_ajuste)
        except ValueError:
            return Response(
                {"erro": "O valor de ajuste deve ser um número inteiro."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Atualiza a quantidade em estoque
        livro.quantidade += quantidade_ajuste

        # Garante que o estoque não seja negativo
        if livro.quantidade < 0:
            return Response(
                {"erro": "A quantidade em estoque não pode ser negativa."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Salva as alterações no banco de dados
        livro.save()

        # Retorna uma resposta com o novo valor em estoque
        return Response(
            {"status": "Quantidade ajustada com sucesso", "novo_estoque": livro.quantidade},
            status=status.HTTP_200_OK
        )