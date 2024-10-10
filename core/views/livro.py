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

    @action(detail=True, methods=["patch"], url_path="alterar-preco")
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
