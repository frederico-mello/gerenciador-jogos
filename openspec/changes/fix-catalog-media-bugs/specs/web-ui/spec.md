## ADDED Requirements

### Requirement: Modal de exclusão via dialog nativo
O modal de confirmação de exclusão SHALL ser implementado com o elemento `<dialog>` e aberto/fechado exclusivamente pelas APIs nativas `showModal()`/`close()`. O comportamento do botão "Excluir" (abrir modal), "Cancelar" (fechar sem excluir) e do submit do form interno permanece conforme o requisito "Exclusão com confirmação" da capability `web-ui`.

#### Scenario: Abrir modal de exclusão
- **WHEN** um administrador clica no botão "Excluir" na página de detalhe
- **THEN** o `<dialog>` é aberto via `showModal()` como modal nativo (fundo bloqueado, `:modal` aplicado) e o texto de confirmação é visível

#### Scenario: Cancelar fecha o modal
- **WHEN** o usuário clica em "Cancelar" dentro do modal aberto
- **THEN** o `<dialog>` é fechado via `close()` e o jogo permanece sem alteração

### Requirement: Cache-busting de mídias de jogo
As templates que referenciam imagens de jogo (`imagem_perfil`, `imagem_componentes`, páginas de manual) via `url_for('games.media', ...)` SHALL acrescentar query string de versão `?v=<updated_at>` do jogo, de forma que um re-upload produza uma URL diferente e o browser busque a nova imagem sem depender de cache local.

#### Scenario: Re-upload gera nova URL de imagem
- **WHEN** um administrador substitui a imagem de perfil de um jogo (com `updated_at` atualizado) e a página de detalhe é recarregada
- **THEN** o atributo `src` da imagem contém `?v=` com o novo `updated_at`, forçando o browser a buscar a imagem nova

### Requirement: Quebra de linha simples na descrição
A renderização Markdown da descrição SHALL preservar quebras de linha simples (Enter único no textarea) convertendo-as em `<br>` visíveis, além dos parágrafos separados por linha em branco já suportados. O HTML sanitizado continua restrito a `ALLOWED_TAGS`/`ALLOWED_ATTRIBUTES` (que já incluem `br`).

#### Scenario: Enter único vira quebra visível
- **WHEN** a descrição contém "linha um\nlinha dois" (sem linha em branco entre elas)
- **THEN** a página de detalhe exibe "linha um" e "linha dois" em linhas separadas (com `<br>` no HTML renderizado)

#### Scenario: Sanitização continua aplicada
- **WHEN** a descrição contém Markdown com quebras simples e conteúdo permitido (negrito, listas)
- **THEN** o HTML renderizado contém `<br>` e mantém a sanitização bleach existente

### Requirement: Rótulo do campo regras_resumo na UI
As telas de formulário e de detalhe SHALL exibir o rótulo "Objetivo" para o campo `regras_resumo`. O nome do campo no banco, o payload do form e os dados existentes permanecem `regras_resumo`.

#### Scenario: Rótulo no formulário
- **WHEN** o form de criar/editar é renderizado
- **THEN** o label do campo `regras_resumo` exibe "Objetivo"

#### Scenario: Rótulo no detalhe
- **WHEN** a página de detalhe é renderizada com metadados técnicos
- **THEN** o card de `regras_resumo` exibe o rótulo "Objetivo"

## MODIFIED Requirements

### Requirement: Servir arquivos estáticos de imagens
O sistema SHALL servir as imagens de `data/` via uma rota `GET /media/<path:filename>` que usa `flask.send_from_directory('data', filename)`, para que templates possam referenciar `<img src="/media/<game.imagem_perfil>">`.

#### Scenario: Acessar imagem de perfil
- **WHEN** o navegador requisita `GET /media/anatomia/memotomia/perfil.jpg`
- **THEN** o Flask retorna o arquivo JPEG com content-type `image/jpeg`
