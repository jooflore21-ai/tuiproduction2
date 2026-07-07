# CLAUDE.md — TUI Production Control

## Método de trabalho obrigatório

Antes de qualquer tarefa, internalizar e seguir este método:

### Antes de executar — agir como projetista/engenheiro
1. **Perguntar antes de assumir** — fazer perguntas cirúrgicas para esclarecer o interesse real. Nunca inventar comportamento não confirmado.
2. **Explicar o complexo** — quando a tarefa envolver decisão arquitetural, migração de dados ou risco, explicar o que vai acontecer antes de agir. O usuário precisa entender para aprovar.
3. **Projetar, analisar, viabilizar** — pensar como engenheiro antes de executar. Identificar dependências, riscos, ordem correta de execução e possíveis efeitos colaterais.
4. **Dividir em fases** — tarefas grandes devem ser quebradas em partes menores com objetivos claros. Cada fase tem escopo, validação e entrega definidos antes de começar.

### Durante a execução
5. **Ler antes de escrever** — ler TODOS os arquivos relevantes antes de uma linha de código. Nunca assumir estrutura de banco, assinatura de função ou padrão de código.
6. **Uma responsabilidade por execução** — visual numa tarefa, dados em outra, migração em outra. Nunca misturar riscos.
7. **Fases numeradas** — executar edições em ordem de dependência (Edit 1/N, Edit 2/N…). Reportar progresso a cada edição.

### Ao encerrar
8. **Validar antes de encerrar** — rodar o servidor, testar cada rota afetada, consultar o banco quando necessário. Nunca encerrar sem validação.
9. **Reportar estruturado** — ao final de cada tarefa: arquivos alterados, dados inseridos/migrados, resultado de cada rota testada, o que não foi encontrado.

---

## Contexto do projeto

**Sistema:** TUI Production Control
**Stack:** Python Flask · SQLite · Jinja2 · Blueprints
**Acesso:** Rede interna (tablets + desktop) · sem autenticação · `host='0.0.0.0' port=5000`
**Princípios:** Clean Architecture · SOLID · Repository Pattern · SQL nunca vaza para rotas

---

## Estrutura de arquivos

```
production/
├── run.py                        ← ponto de entrada
├── requirements.txt
├── estoque.db                    ← banco SQLite (NUNCA dropar tabelas)
└── app/
    ├── __init__.py               ← create_app() com blueprints + aliases
    ├── models/
    │   ├── __init__.py           ← reexporta TUDO de scooter.py e peca.py
    │   ├── connection.py         ← get_connection() com row_factory
    │   ├── scooter.py            ← lógica de scooter, produção, saídas, edições
    │   └── peca.py               ← lógica completa de peças
    └── routes/
        ├── __init__.py
        ├── main.py               ← GET /
        ├── producao.py           ← /producao e sub-rotas
        ├── saidas.py             ← /saidas e sub-rotas
        ├── estoque.py            ← /estoque_geral
        └── pecas.py              ← /pecas e sub-rotas
```

---

## Banco de dados — tabelas existentes

### Tabelas de scooter (não alterar estrutura)
`produtos` · `variacoes` · `producao` · `assistencia` · `saidas_estoque` · `edicoes`

### Tabelas de peças
```
pecas
  id, codigo, nome, origem, container_tipo, tem_variacao_cor,
  peca_pai_id, ativo, custo_unitario (US$)

estoque_pecas
  id, peca_id, cor, quantidade
  UNIQUE(peca_id, cor) + índice parcial para cor IS NULL

movimentacoes_peca
  id, peca_id, cor, tipo, quantidade, motivo_detalhe,
  num_pedido, num_lote, modelo_scooter, data_hora
  tipos válidos: ENTRADA | CONSUMO | VENDA | DEFEITO | ASSISTENCIA

bom
  id, modelo, peca_id, usa_cor_scooter, cor_fixa, quantidade
  UNIQUE(modelo, peca_id)
```

---

## Estado atual do banco (pós passo 1)

### Peças
- **63 peças** no total (53 originais + 10 novas)
- Todas com `custo_unitario` em US$ (ferramentaria = 0, editável)

### BOMs — itens por modelo
| Modelo      | Itens |
|-------------|-------|
| TUI MAIS    | 31    |
| TUI POP     | 29    |
| TUI MAIS-S  | 32    |
| TUI POP-S   | 30    |
| TUI MAIS-LS | 33    |

### Peças novas cadastradas
| Código | Nome                        | Origem        | Custo |
|--------|-----------------------------|---------------|-------|
| 10001  | Farol traseiro              | IMPORTADA     | $3.32 |
| 10002  | Alarme                      | IMPORTADA     | $16.79|
| 10003  | Amortecedor                 | IMPORTADA     | $2.35 |
| 10004  | Garfo adaptado suspensão    | FERRAMENTARIA | $0.00 |
| 10005  | Quadro adaptado TUI MAIS-S  | FERRAMENTARIA | $0.00 |
| 10006  | Quadro adaptado TUI POP-S   | FERRAMENTARIA | $0.00 |
| 10007  | Quadro comprido TUI MAIS-LS | FERRAMENTARIA | $0.00 |
| 10008  | Cabo freio traseiro longo   | IMPORTADA     | $0.00 |
| 10009  | Chave e trava painel        | IMPORTADA     | $1.00 |
| 10010  | Controle de alarme          | IMPORTADA     | $0.50 |

### Custos das peças-set distribuídos
- RD-TRAS $75.84 (70%) · RD-DI $32.50 (30%) — roda traseira tem motor
- FREIO-TRAS $10.90 (55%) · FREIO-DI $8.92 (45%) — traseiro tem cabo mais longo
- PARALAMA $8.38 · RDT-DISCO $1.67 · RDD-DISCO $1.66

---

## Modelos de scooter reconhecidos

`TUI MAIS` · `TUI POP` · `TUI MAIS-S` · `TUI POP-S` · `TUI MAIS-LS`

Diferenças entre modelos -S e base: quadro adaptado + garfo adaptado + amortecedor ×4
Diferença MAIS-LS vs MAIS-S: quadro comprido + cabo freio traseiro longo
Cor da scooter = cor do paralama (usa_cor_scooter=1 na BOM)

---

## Regras técnicas obrigatórias

- **Banco:** nunca dropar tabelas. Migrações via `ALTER TABLE` com verificação de coluna (`PRAGMA table_info`).
- **Seed:** sempre `INSERT OR IGNORE` — idempotente. Pode rodar múltiplas vezes sem duplicar.
- **SQL:** nunca em rotas. Sempre em `models/peca.py` ou `models/scooter.py`.
- **Estoque negativo:** permitido — é alerta, não bloqueio. `baixar_estoque_por_bom()` registra mesmo no negativo.
- **row_factory:** verificar `connection.py` antes de usar `PRAGMA table_info` ou processar resultados de query.
- **Custo:** US$, campo `custo_unitario REAL DEFAULT 0`, sempre editável. Ferramentaria = 0.
- **Tipos de movimentação:** `ENTRADA | CONSUMO | VENDA | DEFEITO | ASSISTENCIA`
- **Blueprints:** `producao_bp`, `saida_bp`, `estoque_bp`, `main_bp`, `pecas_bp`
- **Aliases de endpoint:** mantidos em `__init__.py` para compatibilidade com templates antigos.

---

## Pedidos ao fornecedor chinês

- Fornecedor: Shenzhen G-LUX Electric Co., Ltd (contato: Jordan Wang)
- Pedidos padrão: 820 kits por container · 2 containers simultâneos
- Container especial: baterias (separado)
- Peças ~420 un./tipo por container
- Custos em US$ conforme proforma

---

## Sequência de trabalho em andamento

### Concluído
- ✅ Fase 1 — Clean Architecture (Blueprints, models separados)
- ✅ Fase 2 — Banco de peças + rotas + templates funcionais
- ✅ Fase 3 — Baixa automática de peças ao embalar scooter
- ✅ Fase 4 — Saída manual de peças + pedido unificado
- ✅ Fase 5 — Dashboard visual (KPIs + gráficos + críticas)
- ✅ Nav — link Peças em todas as páginas
- ✅ Passo 1 — Modelos novos + peças novas + custos + BOMs

### Próximos (em ordem)
- ✅ Bloco A — Visual: barras coloridas por cor do paralama + CSS tabela peças
- ⏳ Bloco D — Repaginação embalagem/saída + botões modelos novos
- ⏳ Bloco B — Comparação entre meses no dashboard
- ⏳ Bloco C — Carrinho de pedidos (maior, por último)
- ⏳ Financeiro — Painel de gastos por tipo de movimentação
- ⏳ ASSISTENCIA — Terceiro tipo de saída de peça
- ⏳ TUI POP — Limpar nomes no banco (chassis no nome_completo)

---

## Decisões de design registradas

- **Cor infantil vs. profissional:** manter cor-coding (funcional no chão de fábrica), mas aplicar saturação menor, hierarquia e tipografia séria no redesign visual
- **Carrinho de pedidos:** confirmação ativa pré-registro ("deseja adicionar peças a este pedido?") — intercepta sem atrapalhar pedido de item único
- **Custo em sets:** RD 70/30 (motor na traseira), Freio 55/45 (cabo mais longo no traseiro), resto 50/50 ou valor cheio
- **Parafusos:** deixados para o futuro — estrutura SOLID permite adicionar sem risco
- **Mola/parafusos vs peças:** mola do pezinho já cadastrada; parafusos aguardam fase futura
- **Key and lock:** peça de assistência técnica, não entra em BOM
- **Manete e pastilha avulsos:** já existem como componentes de kit (FD/FT), vendáveis individualmente pela estrutura peca_pai_id

---

## Método de trabalho — adições confirmadas em 02/07/2026

As diretrizes abaixo foram consolidadas pelo usuário e fazem parte do método obrigatório:

1. **Fazer perguntas para esclarecer o interesse real** — não perguntar o que já pode ser inferido. Só perguntar quando falta dado concreto para decidir.
2. **Explicar antes de executar em casos complexos** — quando a tarefa envolve risco, migração de dados ou decisão arquitetural, explicar o que vai acontecer e por quê antes de agir. O usuário precisa entender para aprovar.
3. **Dividir tarefas em busca do cumprimento do prazo** — tarefas grandes quebradas em fases com escopo claro. Cada fase entrega valor independente.
4. **Projetar, analisar, viabilizar — trabalhar como engenheiro/projetista antes de executar** — pensar nas dependências, riscos, ordem correta, efeitos colaterais. Mockup ou diagrama quando a decisão for visual ou complexa.

---

## Decisões técnicas — Bloco D (formulário de embalagem)

- **Responsividade por altura:** 3 breakpoints `@media (max-height)` — 750px, 650px, 580px
- **Drawer de navegação:** desliza da direita, overlay fecha ao clicar fora, acionado por ☰
- **Nav desktop:** `.nav-desktop` some em `max-height: 750px`, ☰ aparece
- **Título do card:** `#form-card-title` some em `max-height: 750px`
- **Modelos:** grid `.modelo-grid-5` — 2+2+1, azul para base, roxo para -S/-LS
- **Quantidade:** duas linhas — `.quick-buttons` (3/6/9/12) acima, `.input-stepper` (−/input/+) abaixo, dentro de `.quantidade-wrapper`
- **Botão Registrar:** sem hover, `:active` escurece, `min-height: 48px`
- **Bug pré-existente (não corrigido):** botão Cancelar do modal "Nova Edição" usa querySelector global — fix: `addEdicaoModal.querySelector('.btn-cancel-modal')`
- **Tipo + Edição sempre lado a lado:** `#production-form .form-row` com `flex-wrap: nowrap` e `min-width: 0` nos filhos

---

## Decisões técnicas — Bloco B (comparativo de meses)

- **Seletor:** dois inputs type="month" + botão Comparar → GET com ?mes_a=&mes_b=
- **Default:** mês atual vs mês anterior (calculado em Python, sem depender de locale)
- **Agregação por modelo:** MODELOS_CONHECIDOS ordenados por len() desc antes do startswith — evita TUI MAIS engolir TUI MAIS-S
- **KPI cards:** total geral + top 2 modelos por maior variação percentual absoluta
- **Ordenação top 2:** 'novo' (mes_b=0) primeiro, depois por |percentual| desc, 'sem_dados' por último
- **Edge case crescimento infinito:** tipo 'novo' → "+N un. (novo)" em vez de percentual
- **Edge case zerado:** tipo 'zerado' → "↓ zerado" com pct=-100
- **Gráfico:** barras agrupadas Chart.js — azul #2a78d6 (mês A) vs cinza #c3c2b7 (mês B), 5 modelos
- **Guard de vazio:** {% if comp_data_a|sum > 0 or comp_data_b|sum > 0 %} antes do canvas
- **Meses PT:** dict manual MESES_PT — não depende de locale do sistema

---

## Bug crítico documentado — overlay do drawer (resolvido em 03/07/2026)

**Sintoma:** todos os botões e links de /producao não respondiam a cliques reais, mas funcionavam via `.click()` programático.

**Causa:** `#nav-drawer-overlay` com `position:fixed; inset:0; z-index:200; opacity:0` cobria toda a viewport. `opacity:0` não desativa `pointer-events` — o overlay invisível interceptava 100% dos cliques.

**Correção:**
```css
#nav-drawer-overlay {
    pointer-events: none; /* fechado: não intercepta cliques */
}
#nav-drawer.open #nav-drawer-overlay {
    opacity: 1;
    pointer-events: auto; /* aberto: funciona como área de fechamento */
}
```

**Regra geral:** qualquer overlay com `position:fixed` e `opacity:0` DEVE ter `pointer-events:none` enquanto invisível. Aplicar esta regra em todos os drawers/modais do projeto.

**Lição de diagnóstico:** `.click()` programático ignora hit-testing — não serve para validar se cliques reais chegam ao elemento. Usar `document.elementFromPoint()` para confirmar o que está no topo em cada coordenada.
