# ROADMAP.md — TUI Production Control

Documento de planejamento vivo. Complementa o CLAUDE.md (que guarda
estado técnico e regras). Aqui ficam as ideias em andamento, decisões
pendentes e a fila de prioridades — para não perder nenhum fio solto
entre conversas.

---

## Fila de execução atual

### Prontos para rodar (não dependem de nada novo)
- [ ] **Prompt 2** — Saídas: renomear motivos (Cliente/Revenda/Feira/
      Bonificado, zerando histórico), adicionar 5 modelos, ajustar
      width/height dos botões de quantidade
- [ ] **Prompt 3** — Peças: remover Código e Origem da tabela visível,
      mover para dentro do modal de Entrada/Saída como informação
      de contexto (leitura). Tabela final: Nome · Estoque · Ações

### Precisa de projeto antes de codar
- [ ] **Drawer universal** — extrair header + drawer para um
      template base (`base.html` com `{% extends %}`), aplicado a
      todas as páginas (produção, saídas, estoque, peças, landing).
      Mesma regra mobile (`max-height` + `max-width: 767px`) usada
      hoje só em produção. **Risco:** refatoração de templates,
      testar cada página depois.
- [ ] **Bloco C expandido — Pedido unificado** (era "carrinho de
      pedidos", agora absorve a ideia de reserva desde a produção).
      Ver seção dedicada abaixo. Precisa de sessão de projeto
      completa antes do primeiro prompt.

---

## Bloco C expandido — Pedido unificado (decisão tomada, projeto pendente)

### Contexto e decisão
Ideia original (conversa anterior): carrinho de pedidos só na saída,
agrupando scooters + peças pelo mesmo `num_pedido`.

Nova ideia (03/07/2026): mover a origem do `num_pedido` para a
**produção**. Ao invés de só informar o pedido na saída, o operador
já marca a scooter como pertencente a um pedido no momento em que
embala — e ela fica **reservada** (não conta no estoque geral
"livre") até a saída confirmar o despacho.

**Decisão confirmada pelo usuário:** unificar as duas ideias em um
único ciclo de vida de pedido, ao invés de dois sistemas
desconectados. Razão: um sistema separado geraria "estoque fantasma"
— reservas que nunca são liberadas porque produção e saída não se
comunicam.

### Ciclo de vida do pedido (rascunho — validar em sessão de projeto)

```
RESERVADO (criado na produção)
  → scooter/peça vinculada a um num_pedido
  → NÃO aparece no estoque geral livre
  → aparece em alguma visão de "pendentes de despacho"
        ↓
DESPACHADO (confirmado na saída)
  → operador busca por num_pedido
  → vê o que já foi embalado para aquele pedido
  → confirma quantidades e despacha
  → baixa definitiva, sai da lista de pendentes
```

### O que já foi decidido
1. Scooter embalada com tipo "Pedido" fica **reservada**, não conta
   no estoque geral imediatamente (evita "achar" que tem uma TUI
   preta disponível quando ela já tem dono).
2. Na saída, o fluxo é **busca por número de pedido** → mostra o que
   já foi embalado → operador confirma. Não é reentrada manual de
   modelo/cor/quantidade do zero.
3. Isso avisa logística/comercial que o pedido já está fisicamente
   pronto, mesmo antes do despacho formal.

### Perguntas em aberto para a sessão de projeto dedicada
- Terceiro tipo de lançamento "Pedido" na produção: como o modal de
  número de pedido se encaixa no fluxo atual (Tipo de Lançamento →
  Modelo → Cor → Quantidade → Registrar)? Antes ou depois de
  Registrar?
- Onde aparecem os itens "reservados, aguardando despacho"? Nova aba
  na página de produção? Nova página? Painel na página de saídas?
- Como o operador de saída busca o pedido — campo de busca livre,
  lista de pendentes clicável, ou os dois?
- O que acontece se um pedido reservado precisa ser cancelado ou
  alterado antes do despacho?
- Como isso se conecta com a ideia already-aprovada de peças
  reservadas junto ao mesmo pedido (o "lembrete" de adicionar peças
  antes de finalizar o carrinho)?
- Schema de banco: nova tabela `pedidos` (id, num_pedido, status,
  data_criacao, data_despacho) + `itens_pedido_scooter` +
  `itens_pedido_peca`? Ou reaproveitar `producao`/`saidas_estoque`
  com uma coluna de status?
- `consultar_estoque()` precisa mudar para excluir reservados —
  qual o impacto nas queries existentes (dashboard, KPIs, etc.)?

**Não escrever nenhum prompt de código para isso até a sessão de
projeto responder essas perguntas.**

---

## Backlog — itens definidos, aguardando janela de execução

- [ ] **ASSISTENCIA** — terceiro tipo de saída de peça (só custo,
      sem receita). Já modelado no banco (`movimentacoes_peca.tipo`
      aceita o valor), falta UI.
- [ ] **Financeiro** — painel de gastos por tipo de movimentação
      (CONSUMO, ASSISTENCIA, DEFEITO). `custo_unitario` já existe
      no banco desde o Passo 1.
- [ ] **TUI POP — limpar nomes no banco** — `nome_completo` inclui
      cor de chassis (ex: "TUI POP PRETO BRANCO"), precisa
      normalizar para só cor de paralama. Requer migração cuidadosa
      (risco de colisão de nomes). Ver conversa de 21/05 para o
      diagnóstico completo.
- [ ] **HTTPS / certificado SSL** — Flask em dev roda HTTP puro,
      browser mostra aviso de conexão não seguera. Solução: nginx
      como proxy reverso + certificado. Tarefa de infraestrutura,
      não de código Flask.
- [ ] **Bug pré-existente do modal "Nova Edição"** — botão Cancelar
      usa `document.querySelector('.btn-cancel-modal')` global, que
      captura o primeiro do DOM (`#edit-modal`) ao invés do modal
      certo. Fix sugerido: escopar a busca dentro do
      `addEdicaoModal`. Identificado no Bloco D, não corrigido
      (fora do escopo daquele prompt).

---

## Como usar este documento

- Antes de iniciar qualquer prompt novo, verificar se ele já está
  mapeado aqui.
- Ao concluir um item, mover para o CLAUDE.md (seção "Concluído")
  e remover ou riscar aqui.
- Ideias novas que surgirem no meio de uma sessão entram aqui
  primeiro, analisadas antes de virarem prompt — nunca direto pro
  Claude Code sem passar pelo projeto.

---

## Bloco C expandido — decisões travadas em 03/07/2026

### UI — Produção
- Tipo de lançamento "Pedido" (3º além de Estoque/Assistência)
- Ao clicar Registrar com tipo=Pedido: modal pop-up pede o número
- Modal vem com o número do ÚLTIMO pedido inserido como default
  (facilita múltiplos registros do mesmo pedido — caso de revenda)
- Nova aba/seção na página de produção: "Pedidos" — lista o que
  está reservado/aguardando despacho, visível para a equipe

### UI — Saídas
- O campo de número de pedido MANUAL continua existindo e
  funcionando como hoje (fluxo direto pro estoque, sem reserva)
- NOVO bloco abaixo do botão "Registrar Saída": lista de pedidos
  já embalados aguardando despacho
- Campo de busca por número de pedido nesse bloco
- Cada linha do pedido tem botão de ação à direita: "Confirmar
  despacho"
- Itens de cada pedido visíveis/expansíveis, no mesmo padrão que
  já existe no log de saídas atual

### Schema de banco — decisão de engenharia (recomendada)
Nova tabela dedicada em vez de reaproveitar `producao`/
`saidas_estoque` com coluna de status. Razão: pedido é uma
entidade com identidade própria (agrupa scooters E peças, tem
ciclo de vida RESERVADO→DESPACHADO) — forçar isso em cima de
tabelas que já têm outro propósito (registro de produção diária,
registro de saída) acopla dois conceitos diferentes e complica
toda query futura.

```
pedidos
  id, num_pedido, status (RESERVADO|DESPACHADO),
  data_criacao, data_despacho

itens_pedido_scooter
  pedido_id (FK), modelo, cor, quantidade

itens_pedido_peca
  pedido_id (FK), peca_id, cor, quantidade
```

`consultar_estoque()` precisa somar apenas o que está fora de
pedidos com status RESERVADO — ajuste de query, não de schema.

### Ainda em aberto (resolver na sessão de mockup)
- Layout exato da aba "Pedidos" em produção — mesma estrutura de
  tabela do log atual, ou cards?
- O que acontece se um pedido reservado precisa ser cancelado/
  alterado antes do despacho (edição, exclusão)?
- Como a peça se vincula ao mesmo pedido na produção (o "lembrete"
  discutido antes) — resolver junto com o mockup do modal

---

## Bloco C expandido — design fechado, pronto para fases (03/07/2026)

### Últimas decisões
- Pedido reservado PODE ser cancelado ou editado antes do despacho
- Aba "Pedidos" em produção mostra a mesma lista da saída (número,
  itens, data), MAS sem o botão de confirmar despacho — só leitura
  + ação de cancelar/editar

### Plano de fases (seguir esta ordem, uma fase por prompt)

**Fase C1 — Schema e backend puro**
- Criar tabelas `pedidos`, `itens_pedido_scooter`, `itens_pedido_peca`
- Funções: `criar_pedido()`, `adicionar_item_scooter_pedido()`,
  `buscar_pedido()`, `listar_pedidos_reservados()`,
  `confirmar_despacho()`, `cancelar_pedido()`, `editar_item_pedido()`
- Ajustar `consultar_estoque()` para excluir reservados
- Sem UI nesta fase — só banco + models, testado via query direta

**Fase C2 — Produção: tipo "Pedido" + modal**
- 3º tipo de lançamento no formulário
- Modal pop-up ao Registrar, pré-preenchido com último num_pedido
- Ao confirmar: chama criar_pedido() + adiciona item, scooter fica
  reservada (não conta no estoque geral)

**Fase C3 — Produção: aba "Pedidos" (visão)**
- Nova aba/seção na página de produção
- Lista pedidos reservados: número, itens, data
- Ações de cancelar/editar (sem botão de despacho)

**Fase C4 — Saída: bloco de despacho**
- Bloco abaixo do botão Registrar Saída
- Busca por número de pedido
- Lista com itens expansíveis + botão "Confirmar despacho"
- Ao confirmar: chama confirmar_despacho(), some da lista de
  reservados, entra definitivamente no histórico de saída

**Fase C5 — Peças no mesmo pedido (retomando ideia do "lembrete")**
- Ao finalizar registro de saída avulsa OU confirmar despacho,
  perguntar se quer atribuir peças ao mesmo pedido (carrinho)
- Conecta com a ideia original de "carrinho" discutida antes deste
  desvio de produção-reservada

### Regra de execução
Cada fase é um prompt próprio, com leitura de arquivos antes,
validação explícita depois, e relatório estruturado. Não pular
fase — C2 depende de C1, C4 depende de C1, etc.

---

## Prompt 2 — Saídas · Concluído (03/07/2026)

### O que foi feito (em etapas, por conta da descoberta abaixo)
1. Migração idempotente de motivos: CPF→CLIENTE, CNPJ→REVENDA,
   FEIRA→FEIRA, PRESENTE→BONIFICADO
2. **Descoberta crítica:** os 3 modelos novos (MAIS-S, POP-S, MAIS-LS)
   tinham peças/BOM (do Passo 1) mas NUNCA tiveram produto/variação
   de estoque — por isso registrar produção OU saída falhava.
   Resolvido com `carregar_variacoes_modelos_novos()`, seguindo o
   mesmo padrão de `carregar_variacoes_iniciais()`. Família MAIS-S/
   MAIS-LS só varia por paralama; POP-S tem chassis fixo PRETO +
   paralama (igual família POP original).
3. form_data atualizado com motivos e 5 modelos
4. Lógica de nome_completo em saidas.py estendida para os 5 modelos
5. Grid de modelo em saidas.html replicado exatamente do padrão de
   produção (.modelo-grid-5, .btn-modelo, .btn-modelo-s, .btn-modelo-full)
6. **Edit companheiro não previsto no prompt original:** `saida.js`
   só reconhecia `.btn` no setupButtonGroup — precisou aceitar
   `.btn-modelo` também, senão os botões ficavam visuais mas mortos.
   Identificado e corrigido pelo Claude Code durante a validação.

### Lição registrada
Sempre que replicarmos um padrão visual de uma página pra outra
(grid de modelo, quantidade, etc.), verificar se o JS companheiro
da página de destino reconhece as MESMAS classes — não basta copiar
o HTML/CSS, o event delegation precisa casar.

---

## Prompt 3 — Peças · Concluído (03/07/2026)

Tabela simplificada para Nome · Estoque · Ações. Código e origem
movidos para bloco de contexto (somente leitura) nos modais de
Entrada e Saída, populados via JS. Backend intocado — pecas.py já
retornava os dados necessários. Testado com entrada real (+2 un.
em Acelerador, id 30 — dado de dev, reversível).

### Status da fila
- [x] Prompt 2 — Saídas (concluído, incluindo seed dos 3 modelos novos)
- [x] Prompt 3 — Peças (concluído)
- [ ] Drawer universal — próximo da fila
- [ ] Bloco C — Fases C1 a C5

---

## Drawer universal — Fase 1 · Concluído (05/07/2026)

Criados: `base.html` (blocos title/extra_head/header_title/
current_page/content/scripts, nav via `self.current_page()|trim`)
e `drawer.js` (compartilhado). Migradas: saidas.html,
estoque_geral.html, pecas/index.html. Produção e Landing
intocadas, conforme decidido.

Todas as 3 páginas testadas: HTTP 200, nav exclui a própria
página, drawer funciona (desktop sem ☰, mobile com ☰ + overlay
pointer-events correto), scripts próprios (Chart.js, modais,
formulários) intactos, regressão de saída real registrada com
sucesso.

**Dado de teste no banco:** saída TST-BASE-HTML (TUI MAIS BRANCO,
CLIENTE) — reversível pela tela de Saídas.

### Status da fila
- [x] Drawer Fase 1 (Saídas, Estoque, Peças)
- [ ] Drawer Fase 2 — migrar Produção para base.html (maior risco:
      página já validada e corrigida do bug do overlay; remover
      lógica de drawer duplicada de producao.js em favor do
      drawer.js compartilhado, sem tocar em mais nada)
- [ ] Bloco C — Fases C1 a C5

---

## Backlog — item novo identificado em 05/07/2026

- [ ] **Filtros da aba "Visão Geral" em Produção** (linha ~140 de
      producao.html) só têm: Todos, TUI, TUI MAIS, TUI POP. Faltam
      TUI MAIS-S, TUI POP-S, TUI MAIS-LS. Diferente do formulário
      de embalagem em si (que já tem os 5 modelos corretos) — isso
      é o filtro da TABELA de estoque detalhado, dentro da aba.
      Baixo risco, prompt isolado quando houver janela.

---

## Drawer universal — Fase 2 (Produção) · Concluído (05/07/2026)

Migração de maior risco da sequência, concluída sem regressão.
Teste decisivo repetido: `elementFromPoint` no centro de cada
botão do formulário confirma `pointer-events:none` no overlay
fechado — o bug crítico do Prompt 1 não retornou.

Todas as 4 páginas de conteúdo (Produção, Saídas, Estoque, Peças)
agora compartilham header+drawer via base.html. Landing segue
standalone por decisão registrada. drawer.js é a única fonte da
lógica de abrir/fechar.

**Achado confirmado (não é regressão):** bug do botão Cancelar
do modal "Nova Edição" (querySelector global captura o Cancelar
do edit-modal primeiro) é pré-existente, já estava documentado.
Fix conhecido: escopar `addEdicaoModal.querySelector('.btn-cancel-modal')`.

**Dados de teste no banco:** 1x produção TUI MAIS-S BRANCO
(estoque) + 1x assistência TUI MAIS. Reversíveis pela tela de
Produção.

### Status da fila
- [x] Drawer Fase 1 (Saídas, Estoque, Peças)
- [x] Drawer Fase 2 (Produção)
- [x] Fix — botão Cancelar do modal Nova Edição (concluído 05/07/2026)
- [x] Fix — filtros de modelo na Visão Geral (concluído 05/07/2026)
- [ ] Bloco C — Fases C1 a C5

---

## Fix — Cancelar do modal Nova Edição · Concluído (05/07/2026)

`btnCancelModal` reescopado para `addEdicaoModal.querySelector(...)`
em vez de `document.querySelector(...)` global. Testado: Nova
Edição fecha pelo Cancelar, salva via fetch normalmente, e
edit-modal (não tocado) continua fechando pelo seu próprio
Cancelar — sem regressão.

**Dado de teste no banco:** edição "TESTE-CANCEL-FIX-4" criada
via fluxo real de salvar. Inofensiva, removível manualmente pela
tela se desejar.

---

## Fix — filtros de modelo na Visão Geral · Concluído (05/07/2026)

7 botões de filtro agora (Todos, TUI, TUI MAIS, TUI POP,
TUI MAIS-S, TUI POP-S, TUI MAIS-LS). Nenhum ajuste de regex foi
necessário — testado ao vivo com números reais (ex: "TUI MAIS"
mostrou 12/938, não 14/942, confirmando que MAIS-S não vaza).
JS não foi tocado, só o HTML dos botões.

### Toda a limpeza de backlog concluída
- [x] Drawer Fase 1 e Fase 2
- [x] Fix Cancelar modal Nova Edição
- [x] Fix filtros de modelo

### Próximo: Bloco C — Fase C1 (schema e backend)

---

## Backlog — item novo identificado em 05/07/2026 (Fase C1)

- [ ] **Bug: baixa automática de BOM só considera TUI MAIS/TUI POP**
      Em app/routes/producao.py, a condição
      `if modelo_nome in ('TUI MAIS', 'TUI POP'):` está desatualizada.
      Os 3 modelos novos têm BOM cadastrada mas nunca são consultados
      ao embalar para estoque normal — peças não são descontadas.
      Fix: verificar dinamicamente se existe BOM para o modelo
      (query em vez de tupla fixa), não uma lista hardcoded.
      Prioridade: corrigir logo, afeta rastreio real de estoque
      de peças para os modelos novos.

---

## Bloco C — Fase C1 · Design finalizado (05/07/2026)

### Descoberta chave (leitura de scooter.py)
`registrar_producao()` incrementa DIRETAMENTE `variacoes.estoque_atual`.
`consultar_estoque()` só lê esse campo. Não existe camada de status.
Conclusão: NÃO é preciso ajustar `consultar_estoque()` — scooter
reservada simplesmente nunca toca `estoque_atual`, resolvendo o
problema na raiz.

### Schema final (revisado — usa variacao_id, não texto solto)
```sql
pedidos
  id, num_pedido, status (RESERVADO|DESPACHADO|CANCELADO),
  data_criacao, data_despacho

itens_pedido_scooter
  id, pedido_id (FK), variacao_id (FK), producao_id (FK, rastreio),
  quantidade
```

### Decisões confirmadas pelo usuário
1. Produção reservada AINDA gera log em `producao` (mesma tabela do
   histórico normal — aparece em Log de Produção e dashboards) —
   só NÃO incrementa `variacoes.estoque_atual`.
2. Despacho grava direto em `saidas_estoque` (bypass da checagem/
   desconto de estoque geral, já que a reserva nunca entrou nele).
   Isso mantém o log de Saídas unificado (já agrupa por num_pedido).
3. Confirmar despacho pede o motivo (CLIENTE/REVENDA/FEIRA/
   BONIFICADO) nesse momento — não é clique único.
4. Cancelar pedido devolve a scooter ao estoque geral (incrementa
   estoque_atual de volta) — fisicamente ela já existe, só perdeu
   o destino. Histórico de produção e o item cancelado são mantidos
   (não deletados), pedido marca status=CANCELADO.
5. Peças ficam FORA do escopo do C1 — `movimentacoes_peca` já tem
   `num_pedido`, reaproveitado na Fase C5.
6. Editar quantidade de um item ajusta `itens_pedido_scooter` e o
   `producao` vinculado (delta simples) — NÃO reconcilia peças da
   BOM retroativamente (mesma limitação que `atualizar_producao()`
   já tem hoje).

### Novo módulo: app/models/pedido.py
Segue o padrão de separação por domínio já usado (scooter.py,
peca.py). Funções: criar_tabelas_pedidos, buscar_ultimo_num_pedido_usado,
registrar_producao_pedido, listar_pedidos_reservados,
buscar_pedido_por_numero, confirmar_despacho, cancelar_pedido,
editar_item_pedido.

---

## Bloco C — Fase C1 · Concluído (07/07/2026)

`app/models/pedido.py` criado com 8 funções + 2 helpers privados.
Todos os 10 testes passaram com valores reais do banco (não só
"passou" — números conferidos: estoque inalterado na reserva,
BOM descontada corretamente até nos modelos novos, despacho grava
em saidas_estoque, cancelamento devolve ao estoque geral).

### Decisões de implementação registradas
- `edicao_id = 1` fixado em `_resolver_variacao_id` (única edição
  existente hoje; evita ambiguidade se surgirem outras)
- Retornos estruturados (dicts) em confirmar_despacho/cancelar_pedido/
  editar_item_pedido — úteis para mensagens de flash em C2-C4
- `saidas_estoque.observacao` fica NULL no despacho (coluna aceita)

**Dados de teste no banco:** pedidos TESTE-C1-001 (DESPACHADO),
C1-002 e C1-003 (CANCELADO), C1-POP (RESERVADO) + registros
correspondentes em producao/saidas_estoque. Histórico de teste,
reversível se quiser.

### Status da fila
- [x] Bloco C — Fase C1 (schema e backend)
- [x] Bloco C — Addendum: prioridade + transportadora em pedidos (concluído 07/07/2026)
- [x] Bloco C — Fase C2 (produção: tipo Pedido + modal) — concluído 07/07/2026
- [x] Bloco C — Fase C3 (produção: aba Pedidos) — concluído 07/07/2026
- [ ] Bloco C — Fase C4 (saída: bloco de despacho)
- [ ] Bloco C — Fase C5 (peças no mesmo pedido)

---

# ═══════════════════════════════════════════════════
# VISÃO DE LONGO PRAZO — MES / Ferramentaria / Integração
# Iniciado em 07/07/2026 · APENAS PLANEJAMENTO, sem código
# ═══════════════════════════════════════════════════

Conversa com o diretor de operações antes das férias dele gerou
uma expansão de escopo grande. Registrando aqui ANTES de detalhar
qualquer parte, para não perder nenhuma ideia.

## [Visão] Ferramentaria — controle de WIP (Work In Progress)

Hoje o sistema só sabe "peça consumida" ou "peça em estoque"
(binário). Falta rastrear o ESTADO de cada peça em fabricação
interna, com uma etapa terceirizada no meio (pintura, outra
cidade). Estados mencionados até agora:
  - Tubo (matéria-prima, chega em container)
  - Tubo dobrado
  - Quadro/chassis soldado
  - Garfo pronto
  - → ENVIO para pintura (outra cidade, terceirizado)
  - ← RETORNO da pintura
  - Chassis com suspensão pronto (2-3x o tempo de montar
    um chassis sem suspensão — modelos -S/-LS)

**Ainda não sei:** quantas etapas reais existem, quem opera cada
uma, como a ida/volta da pintura é rastreada hoje (prazo, perdas,
atrasos), se cada etapa tem um "responsável" que precisa ver
uma fila de trabalho.

## [Visão] Compras — planejamento antecipado

Objetivo: comprar com mais antecedência custa menos por unidade.
Precisa cruzar consumo histórico real (já temos: Bloco B do
dashboard, comparativo de meses) com lead time do fornecedor
chinês, para sugerir QUANDO e QUANTO comprar.

## [Visão] Prioridade manual de pedido (era "Integração ERP")

Ideia: quando um pedido é registrado no Microssys, disparar
alerta via API para:
  - Encarregado de produção (confirma se há estoque de
    embaladas ou se precisa produzir)
  - Setor de almoxarifado
  - Checkpoints intermediários: pedido foi aceito pela
    qualidade? está na esteira de produção?
  - Alerta específico de "montagem de paralama necessária
    para modelo X" — conecta direto com o chão de fábrica

## [Visão] Alertas por setor

- Setor de embalagem testa carregadores quando há pedido de
  carregador — alerta na tela deles quando isso acontece
- Padrão geral: alertas que aceleram sem virar cobrança —
  ninguém precisa "ir pedir", o sistema avisa sozinho

## [Visão] Logística de expedição

Pedidos de transportadoras diferentes (Rodonaves, Coppex, etc.)
precisam ser sinalizados para separação no MESMO pallet — evita
misturar carga de transportadoras diferentes.

## [Visão] Dispositivos por setor

- Almoxarifado → tablet (precisa de visão mais ampla de tela)
- Outros setores → celulares sobrando disponíveis para teste
- Ainda a definir: quais setores usam qual dispositivo

## Ordem de ataque sugerida (a validar com o usuário)

1. Ferramentaria primeiro — é a base física que
   falta modelar; sem isso, os Blocos C/D (alertas) não têm
   "estado" nenhum para alertar sobre
2. Compras depois — já tem boa base no dashboard,
   só falta a camada de sugestão
3. Integração ERP + Alertas + Logística — dependem
   de A estar modelado, e de decisões de infraestrutura (API
   do Microssys, quem tem acesso a quê)
4. Dispositivos — decisão de compra/distribuição,
   não é código

## REGRA: nada disso vira prompt até estar bem entendido

Esta seção é só mapa. Cada bloco precisa da mesma disciplina
que aplicamos no resto do projeto: entender o processo real
antes de desenhar schema, perguntar até não haver ambiguidade,
só então executar em fases pequenas.

## Respostas coletadas — [Visão] Ferramentaria
1. Corte é seção separada (não é a mesma pessoa que dobra)
2. Dobra e solda: pessoas/estações diferentes
3. Perda existe e é importante rastrear — causas via entrevista

## Respostas coletadas — [Visão] Compras

**Descoberta importante:** existem DUAS cadeias de suprimento
distintas, não uma só:
  - Kit importado da China (820 kits/2 containers, fornecedor
    G-LUX/Jordan) — só itens classificados como "importados"
  - Matéria-prima NACIONAL (tubos, placas de ferro para detalhes
    do garfo/tampas/pedais) — comprada no Brasil, alimenta a
    ferramentaria (Bloco A). Planilha do diretor de operações
    tem as dimensões dos tubos e vai explicar melhor esse lado.

**Risco central:** erro de conta na compra nacional gera compra
emergencial mais cara com prazo mínimo de entrega — o oposto do
que se quer (comprar grande/antecipado = mais barato).

**Flexibilidade do pedido chinês:** os 820 kits são só a base
importada, mas dá pra pedir mais peças no mesmo pedido, ou peças
avulsas específicas (ex: manete do freio) fora do ciclo do kit.
Já existe suporte pra isso no sistema (entrada de peça com
quantidade editável). Registros de DEFEITO (já implementados)
servem de base para decidir quanto trocar com o fornecedor
(garantia) vs. quanto pedir a mais por erro interno.

**Paralama — pedido por cor sob demanda:** sempre um total de
1000 pares por pedido, distribuído por cor conforme uma lista que
o usuário monta e envia ANTES da proforma ser fechada. Existe
planilha própria de controle de quantidade tem/precisa para
paralama. **Gap identificado:** possivelmente não há controle de
defeitos cosméticos (arranhões) em paralama — a verificar.
**Conexão direta:** o gráfico "Variação mais embalada" do
dashboard (Bloco B do sistema, já entregue) é exatamente o dado
que deveria informar essa lista de cores enviada ao fornecedor.

**Tempo:** ~2 meses do pedido à chegada (a confirmar com precisão).

**Cadência e trava:** peças importadas costumam ser pedidas 2x/mês,
mas a compra pode atrasar se não houver caixa disponível — ou
seja, a decisão de comprar é travada por fluxo de caixa, não só
por nível de estoque.

**Sazonalidade — prazo real de planejamento:** fim de outubro até
meados de fevereiro é altíssima temporada (marketplaces e revenda
muito fortes). Ano passado tinham estoque suficiente; este ano
precisam carregar o estoque ANTES desse período. Estamos em julho
— ainda há tempo, mas o relógio já está correndo.

**Confirmado:** compra nacional (tubos/placas) é frente totalmente
separada do circuito chinês — não entra na mesma lógica do Bloco B.

**Achado novo:** existia algum controle de tubos/placas que a
produção parou de usar — precisa ser reimplementado e voltar a
ser funcional. Urgência real: o usuário também vai tirar férias
em breve e quer isso rodando antes/durante, para já estar fazendo
diferença quando ele voltar. Perguntar: data da viagem, e o que
exatamente era esse controle que caiu em desuso (planilha, papel,
outra ferramenta?).

**Confirmado (item 3):** o motivo de menos estoque este ano foi o
tempo investido em projetar/executar os modelos com suspensão
(MAIS-S/POP-S/MAIS-LS) — agora prontos, produção e vendas
começando. Isso explica a urgência de carregar estoque antes da
alta temporada (out-fev).

---

## Plano de ativação física (14 dias — volta das férias)

Objetivo: provar valor do projeto aos diretores, colocando em uso
real na fábrica o que já está pronto e estável:
  - Registro de Produção (5 modelos, drawer, mobile-first)
  - Registro de Saída (motivos novos, mesmo grid de modelos)
  - Estoque de Peças (entrada/saída/movimentações/defeitos)
  - Dashboard de Estoque (KPIs, comparativo de meses)

Treinamento é conduzido pelo próprio usuário — já ensinou 1 membro
da embalagem, falta almoxarifado (novo) e relembrar o encarregado
(já usou antes). Não é responsabilidade desta IA preparar material
de treinamento — usuário já tem essa habilidade coberta.

Contexto: o controle antigo que a produção usava era só de "TUI
embalada" (não de tubo/placa) e parou por causa de máquina
inacessível durante mudança de local, numa época anterior ao
trabalho conjunto (usava Gemini antes). Não foi problema de
adoção/treinamento — é seguro reativar.

**Ferramentaria (Bloco A) e Bloco C (pedido unificado) seguem em
ritmo calmo, planejados por celular e implementados no notebook
via Claude Code quando houver tempo — sem pressa de prazo fixo.**

### Simplificação importante (07/07/2026)

Microssys é sistema comprado, industrial (cadastros/pedidos/
faturamento). Ninguém administra formalmente, mas o usuário é
quem mais usou/imprimiu relatórios de lá — teria acesso se
precisasse. NÃO existe API nem integração automática planejada
por enquanto, e **não precisa existir**: a solução é manual.

**Ideia validada:** quem registra o pedido no Microssys vai até
o NOSSO sistema e marca a prioridade daquele pedido. Almoxarifado
e encarregado veem essa prioridade na aba "Pedidos" (mesma que já
estamos construindo no C3 do pedido unificado).

**Isso deixa de ser "visão de longo prazo" e vira uma extensão
barata do Bloco C que já está em andamento** — só precisa de um
campo `prioridade` na tabela `pedidos` e exibição na aba C3.
Não é integração externa, é feature interna simples.

A ideia de integração automática via API com o Microssys fica
registrada como possibilidade futura, sem necessidade de agir.

### Detalhes fechados — Prioridade manual de pedido

- Níveis: BAIXA, MÉDIA, ALTA, URGENTE
- Edição: qualquer pessoa por enquanto (sem restrição). Futuro:
  usuários/permissões — hoje o sistema não tem autenticação
  nenhuma (decisão de design original, rede interna aberta).
  Se permissões por usuário virarem necessidade real, é uma
  mudança de arquitetura maior (login, papéis) — não é trivial
  como os campos de prioridade.
- Dados extras a trazer do Microssys manualmente (futuro mais
  distante que a Ferramentaria): nome do cliente, status de
  faturamento, possivelmente localização para dashboard mais
  robusto. Conecta com a ideia de logística por transportadora
  (Rodonaves/Coppex) já registrada.

### Prioridade de execução confirmada
Ferramentaria > Compras > Prioridade de pedido (barata, já
encaixa no C3) > tudo o mais (Alertas por setor, Logística,
Dispositivos, dados extra do Microssys)

## Respostas coletadas — [Visão] Alertas por setor

1. Carregador: maioria é venda separada de peça avulsa (cliente
   e revenda pedem com frequência). Registrado no Microssys.
2. Garfo é um caso parecido — depende da ferramentaria ter pronto
   separado, montado depois de pintado. CONFIRMADO: mesmo padrão
   do carregador — "precisa preparar X garfos" (ação direta, não
   aviso de disponibilidade).
3. Alerta confirmado — minimalista por design: tela de produção
   mostra só "precisa de X carregadores testados". Número de
   pedido e prioridade NÃO aparecem ali — isso é preocupação do
   almoxarifado, não da produção. Princípio: cada papel vê só o
   que precisa agir, não tudo.

## Respostas coletadas — [Visão] Logística de expedição

4. Pallet = juntar pedidos DIFERENTES da mesma transportadora,
   e isso vale especificamente para PEDIDOS RESERVADOS (conecta
   direto com o pedido unificado C1-C5 já em andamento).
5. Transportadora: às vezes não aparece no Microssys — precisa
   ser campo manual/editável, mesmo padrão da prioridade.
6. Volume constante e alto, ainda maior na alta temporada.

**Conexão confirmada:** `pedidos` (tabela já criada na C1) vai
ganhar, no futuro, DOIS campos manuais editáveis: `prioridade`
e `transportadora`. Os dois nascem juntos quando chegarmos na
aba "Pedidos" (C3) — não são features separadas, é o mesmo
lugar da tela.

## Respostas coletadas — [Visão] Dispositivos por setor

7. Tablet: incerto se existe algum disponível. Celulares: 2 de
   sobra confirmados. Alguns funcionários mais responsáveis podem
   usar o próprio celular pessoal (BYOD) — nota: sem autenticação
   no sistema, isso é aceitável hoje (rede interna), mas vale
   lembrar se algum dia entrar dado sensível.

8. Ordem de rollout de dispositivo/uso, por setor:
   1º Almoxarifado, Encarregado, Embalagem (assim que o usuário
      voltar de férias)
   2º Montagem de paralamas
   3º Estoque da ferramentaria

**Decisão de design registrada:** Ferramentaria deve ter PÁGINA
PRÓPRIA no sistema, seguindo o mesmo padrão visual/estrutural da
página de Produção/Embalagem (mobile-first, drawer, etc.) — não
é uma aba dentro de outra tela, é uma rota nova quando chegarmos
nessa fase.

### Visão de longo prazo — mapeamento inicial concluído (07/07/2026)
Todos os 6 domínios (Ferramentaria, Compras, Prioridade/
Transportadora de pedido, Alertas por setor, Logística,
Dispositivos) têm perguntas respondidas ou entrevista rascunhada.
Pronto para retomar execução do que já está em andamento.

---

## Bloco C — Addendum prioridade/transportadora · Concluído (07/07/2026)

Colunas `prioridade` (default MEDIA) e `transportadora` (default
NULL) adicionadas a `pedidos` via migração idempotente. Função
`atualizar_prioridade_transportadora()` criada e testada
isoladamente. Zero uso em UI ainda — pura preparação para C3/C4,
sem risco de migração futura numa tabela já com dados reais.

**Dados de teste:** TESTE-C1-001 ficou com prioridade=URGENTE,
transportadora=Correios (teste da função). Pedido TESTE-ADDENDUM
criado (RESERVADO). Reversível se quiser.

---

## Bloco C — Fase C2 · Concluído (07/07/2026)

Tipo "Pedido" no formulário de produção, com modal de número
(pré-preenchido com o último usado), fix do bug de chassis do
TUI POP-S (não casava em nenhuma condição antes), fallback pro
tipo "Estoque" quando o operador cancela o modal.

Testado com test_client (backend, valores reais do banco) +
browser real (fluxo de modal completo, incluindo o caso de
campo vazio e o cancelamento).

**Bug já conhecido, RECONFIRMADO neste prompt (não corrigido,
propositalmente fora de escopo):** a baixa automática de BOM no
ramo "Estoque" continua restrita a `('TUI MAIS','TUI POP')` —
os 3 modelos novos não descontam peça quando embalados
diretamente pro estoque (só funciona no fluxo "Pedido", que usa
`_tem_bom` dinâmico). Já estava no backlog desde a C1; agora
foi visto de novo, no mesmo arquivo que acabamos de editar —
bom momento pra corrigir antes de seguir pra C3.

**Dados de teste:** pedidos C2-PEDIDO-A/B, C2-UI-CONFIRM
(reservados); produções de teste nos 5 modelos; 1 assistência.
Reversíveis.

### Status da fila
- [x] Bloco C — Fase C1, Addendum, Fase C2
- [x] Fix — BOM restrita a 2 modelos no fluxo Estoque — concluído 07/07/2026
- [x] Bloco C — Fase C3 (produção: aba Pedidos) — concluído 07/07/2026

---

## Fix — BOM dinâmica no fluxo Estoque · Concluído (07/07/2026)

`existe_bom_para_modelo()` criada em peca.py (pública). Produção
normal (fluxo Estoque) agora desconta peças para os 5 modelos,
não só os 2 originais. Prova: amortecedor (×4 na BOM de -S) e
quadro comprido (×1 na BOM de -LS) descontaram corretamente.

---

## Bloco C — Fase C3 · Concluído (07/07/2026)

4ª aba "Pedidos" na produção: lista de reservados com badge de
prioridade colorido (BAIXA verde/MEDIA cinza/ALTA amarelo/
URGENTE vermelho), transportadora, itens, edição inline e
cancelamento com devolução ao estoque.

Achado e corrigido: `listar_pedidos_reservados` não retornava
`prioridade`/`transportadora` (gap C1→addendum). Adição mínima
ao SELECT. Mesma correção pendente em `buscar_pedido_por_numero`
— antecipada para a C4.

`setupLiveSearch` não reaproveitado (é table-specific) — busca
inline simples por `data-num` nos `.pedido-card`.

Dados de teste: C3-URGENTE (RESERVADO/JadLog), C3-ALTA (editado
→MEDIA/Correios), C3-BAIXA (cancelado, estoque devolvido).

### Status da fila
- [x] C1, Addendum, C2, Fix BOM, C3
- [x] Bloco C — Fase C4 (saída: bloco de despacho) — concluído 17/08/2026
- [ ] Bloco C — Fase C5 (peças no mesmo pedido)
