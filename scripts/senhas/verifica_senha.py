from django.contrib.auth.hashers import check_password

hash_armazenado = 'pbkdf2_sha256$390000$...'
senha_fornecida = 'senha123'

if check_password(senha_fornecida, hash_armazenado):
    print("Senha correta")
else:
    print("Senha incorreta")
