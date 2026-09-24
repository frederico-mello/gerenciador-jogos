## ADDED Requirements

### Requirement: JavaScript compatível com CSP

As templates SHALL renderizar páginas sem código JavaScript inline: nenhum atributo de handler de evento (`onclick=`, `onchange=`, `onsubmit=`, `onload=`, `onerror=`, `oninput=`, `onkeydown=`) e nenhum elemento `<script>` sem atributo `src`. Todo o JavaScript de comportamento da aplicação SHALL residir em um único arquivo externo `app/static/js/app.js`, carregado em `base.html` com `defer` e URL resolvida por `static_v`. A CSP de produção (`script-src 'self'` em `deploy/nginx.conf`) permanece inalterada, sem `unsafe-inline`, e nenhuma interação da interface depende de execução de script inline. O comportamento das interações existentes SHALL ser preservado via listeners acionados por atributos `data-*`:

- botões com `data-modal-open` abrem o `<dialog>` nativo via `showModal()` (requisito "Modal de exclusão via dialog nativo");
- botões com `data-modal-close` fecham o `<dialog>` via `close()`;
- formulários com `data-confirm` pedem confirmação via `confirm()` e abortam o submit quando o usuário rejeita (substitui `onsubmit="return confirm(...)"`);
- elementos de filtro com `data-autosubmit` submetem o formulário que os contém ao mudar de valor (substitui `onchange="this.form.submit()"`);
- o editor EasyMDE é inicializado somente quando a página contém o campo `#descricao`, mantendo o escopo de carregamento limitado ao formulário (requisito da capability `markdown-editor`).

#### Scenario: Templates renderizam sem JS inline

- **WHEN** as páginas de detalhe (`GET /<id>`), formulário (`GET /novo`, `GET /<id>/editar`), lista de usuários (`GET /admin/users`), escolas (`GET /admin/schools`) e empréstimos admin (`GET /emprestimos/admin`) são renderizadas
- **THEN** o HTML não contém nenhum atributo `on<evento>=`, nenhum `<script>` sem `src`, e contém o `<script defer src>` de `app.js`

#### Scenario: Botão Excluir abre modal via listener

- **WHEN** um administrador clica no botão "Excluir" (com `data-modal-open`) na página de detalhe sob CSP `script-src 'self'`
- **THEN** o `<dialog>` de confirmação é aberto via `showModal()` e o texto de confirmação é visível

#### Scenario: Cancelar fecha o modal via listener

- **WHEN** o usuário clica no botão "Cancelar" (com `data-modal-close`) dentro do modal aberto
- **THEN** o `<dialog>` é fechado via `close()` e o jogo permanece sem alteração

#### Scenario: Confirm substitui onsubmit inline

- **WHEN** um administrador aciona "Cancelar" em um empréstimo com status cancelável e confirma no diálogo `confirm()`
- **THEN** o form de cancelamento é submetido normalmente; quando o usuário rejeita, o submit é abortado e nenhuma requisição POST é enviada

#### Scenario: Autosubmit substitui onchange inline

- **WHEN** um administrador altera o filtro de papel em `GET /admin/users` (ou o filtro de rede em `GET /admin/schools`) com `data-autosubmit`
- **THEN** o formulário de filtro é submetido automaticamente, sem handler inline no HTML

#### Scenario: EasyMDE inicializado condicionalmente por app.js

- **WHEN** um admin acessa `GET /novo` (ou `GET /<id>/editar`) e a página contém `#descricao`
- **THEN** `app.js` inicializa o editor EasyMDE no campo; quando `#descricao` não existe, nenhuma inicialização ocorre e nenhum erro é lançado

#### Scenario: Carrossel do manual via app.js

- **WHEN** um usuário acessa `GET /<id>` de um jogo com mais de 1 página de manual
- **THEN** os botões anterior/próximo navegam entre as páginas e o rótulo "Página X de Y" é atualizado, sem script inline na página

#### Scenario: Página sem interações mapeadas não quebra

- **WHEN** uma página sem modal, carrossel, formulário EasyMDE, filtro com `data-autosubmit` ou form com `data-confirm` é carregada (ex. `GET /login`)
- **THEN** `app.js` carrega sem efeito colateral e nenhum erro aparece no console

### Requirement: Teste de regressão de templates sem JS inline

A suíte de testes SHALL incluir um teste de regressão que renderiza os templates com handlers/scripts inline conhecidos e falha quando o HTML produzido contém algum atributo de handler de evento inline ou elemento `<script>` sem atributo `src`, garantindo que novas edições de template não reintroduzam código inline bloqueado pela CSP.

#### Scenario: Teste detecta handler inline reintroduzido

- **WHEN** um template volta a conter `onclick=`, `onchange=` ou `onsubmit=` em qualquer página renderizada coberta pelo teste
- **THEN** o teste de regressão falha, apontando o template e o trecho ofensor

#### Scenario: Teste detecta script inline reintroduzido

- **WHEN** um template volta a conter um `<script>` sem atributo `src`
- **THEN** o teste de regressão falha, apontando o template e o trecho ofensor

#### Scenario: App.js servido como estático

- **WHEN** o navegador requisita `GET /static/js/app.js`
- **THEN** o Flask retorna o arquivo com status 200 e Content-Type `application/javascript`