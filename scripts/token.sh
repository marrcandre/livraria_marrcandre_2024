#!/bin/zsh

# Verifica se o número correto de argumentos foi passado
if [ "$#" -ne 2 ]; then
  echo "Uso: $0 email password"
  exit 1
fi

# Atribui os argumentos às variáveis
email=$1
password=$2

# Executa o comando curl com os parâmetros fornecidos
response=$(curl --silent -X 'POST' \
  'http://0.0.0.0:19005/token/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'X-CSRFTOKEN: 7iW9WGU8frH4WNcUEueM7gyyx26vbkcXLDnZ0pEwl9sbyErBMyUSDhOa3uOP8sO3' \
  -d '{
  "email": "'"$email"'",
  "password": "'"$password"'"
}')

# Extrai o token da resposta
#token=$(echo $response | cut -d'"' -f8)

# Copia o token para a área de transferência
echo $token #| xclip -sel clip

# Opcional: Imprime o token para o usuário
echo "Token copiado para a área de transferência: $token"
