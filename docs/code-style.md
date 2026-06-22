# Estilo de Código

- Funções fazem uma coisa. Se precisar de "e" para descrever, divida em duas.
- Nomes de variáveis descrevem o que contêm. Nomes de funções descrevem o que fazem.
- Sem abreviações. `get_market_features` não `get_mkt_feat`.
- Sem código comentado. Delete. O Git lembra.
- Trate erros explicitamente. Nunca `except: pass` ou exception silenciosa.
- Arquivos com mais de 300 linhas devem ser divididos em módulos.
- Type hints em todas as assinaturas de função.
- Docstrings em funções públicas — uma linha em português descrevendo o que a função faz.
- Imports em três grupos separados por linha em branco: stdlib → externos → internos.

## Testes
- Todo teste deve exercitar o mesmo caminho de código que o uso real vai exercitar — não apenas validar o objeto isolado em memória. Testar a construção de um objeto não substitui testar sua serialização, persistência ou qualquer transformação que o código de produção realmente aplica antes de usá-lo.