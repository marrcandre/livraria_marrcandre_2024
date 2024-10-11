from django.db import transaction

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Compra, User
from core.serializers import CompraSerializer, CriarEditarCompraSerializer


class CompraViewSet(ModelViewSet):
    queryset = Compra.objects.all()
    serializer_class = CompraSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["usuario__email", "status", "data"]
    search_fields = ["usuario__email"]
    ordering_fields = ["usuario__email", "status", "data"]
    ordering = ["-data"]

    def get_queryset(self):
        usuario = self.request.user
        if usuario.is_superuser:
            return Compra.objects.all()
        if usuario.groups.filter(name="Administradores"):
            return Compra.objects.all()
        if usuario.tipo_usuario == User.TipoUsuario.GERENTE:
            return Compra.objects.all()
        return Compra.objects.filter(usuario=usuario)

    def get_serializer_class(self):
        if self.action in ("create", "update"):
            return CriarEditarCompraSerializer
        return CompraSerializer

    @action(detail=True, methods=["post"])
    def finalizar(self, request, pk=None):
        # Recupera o objeto 'compra' usando self.get_object(), com base no pk fornecido.
        compra = self.get_object()

        # Verifica se o status da compra é diferente de 'CARRINHO'.
        # Se não for, a compra já foi finalizada e não pode ser finalizada novamente.
        if compra.status != Compra.StatusCompra.CARRINHO:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"status": "Compra já finalizada"},
            )

        # Abre uma transação atômica para garantir que todas as operações no banco
        # de dados ocorram de forma consistente (ou todas são salvas ou nenhuma).
        with transaction.atomic():
            # Itera sobre todos os itens da compra.
            for item in compra.itens.all():

                # Verifica se a quantidade de um item é maior que a quantidade disponível no estoque do livro.
                if item.quantidade > item.livro.quantidade:
                    # Se a quantidade solicitada for maior que o estoque disponível, retorna um erro.
                    return Response(
                        status=status.HTTP_400_BAD_REQUEST,
                        data={
                            "status": "Quantidade insuficiente",  # Mensagem de erro
                            "livro": item.livro.titulo,  # Informa qual livro tem estoque insuficiente
                            "quantidade_disponivel": item.livro.quantidade,  # Mostra a quantidade disponível
                        },
                    )

                # Se o estoque for suficiente, subtrai a quantidade do item do estoque do livro.
                item.livro.quantidade -= item.quantidade
                # Salva as alterações no livro (atualiza o estoque no banco de dados).
                item.livro.save()

            # Após todos os itens serem processados e o estoque ser atualizado,
            # atualiza o status da compra para 'REALIZADO'.
            compra.status = Compra.StatusCompra.REALIZADO
            # Salva as alterações da compra no banco de dados.
            compra.save()

        # Retorna uma resposta de sucesso indicando que a compra foi finalizada.
        return Response(status=status.HTTP_200_OK, data={"status": "Compra finalizada"})

