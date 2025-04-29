from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from core.models import Categoria
from core.serializers import CategoriaSerializer


class CategoriaViewSet(ModelViewSet):
    queryset = Categoria.objects.order_by('-id')
    search_fields = ['descricao']
    filter_backends = (SearchFilter, OrderingFilter)
    serializer_class = CategoriaSerializer
