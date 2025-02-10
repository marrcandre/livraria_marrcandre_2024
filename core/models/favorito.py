from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .livro import Livro
from .user import User


class Favorito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favoritos")
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE, related_name="favoritos")
    data_atualizacao = models.DateTimeField(auto_now=True)
    nota = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    comentario = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-data_atualizacao"]
        unique_together = ["usuario", "livro"]  # Impede duplicatas de favoritos

    def __str__(self):
        return f"{self.usuario} - {self.livro}"
