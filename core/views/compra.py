from django.contrib.auth.decorators import login_required
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
        compra = self.get_object()
        if compra.status != Compra.StatusCompra.CARRINHO:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"status": "Compra já finalizada"},
            )
        with transaction.atomic():
            for item in compra.itens.all():
                if item.quantidade > item.livro.quantidade:
                    return Response(
                        status=status.HTTP_400_BAD_REQUEST,
                        data={
                            "status": "Quantidade insuficiente",
                            "livro": item.livro.titulo,
                        },
                    )
                item.livro.quantidade -= item.quantidade
                item.livro.save()
            compra.status = Compra.StatusCompra.REALIZADO
            compra.save()
        return Response(status=status.HTTP_200_OK, data={"status": "Compra finalizada"})

    # TODO: criar uma função para adicionar um livro no carrinho de compra
