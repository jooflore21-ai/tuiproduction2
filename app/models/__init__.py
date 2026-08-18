from .connection import get_connection
from .scooter import (
    criar_tabelas, carregar_variacoes_iniciais,
    carregar_variacoes_modelos_novos, migrar_motivos_saida,
    registrar_producao, consultar_producao,
    registrar_assistencia, consultar_assistencia,
    deletar_assistencia, deletar_producao,
    atualizar_producao, atualizar_assistencia,
    consultar_estoque, consultar_estoque_por_modelo,
    registrar_saida, consultar_saidas,
    deletar_saida, atualizar_saida,
    criar_edicao, listar_edicoes, CORES_CSS
)
from .peca import (
    criar_tabelas_pecas,
    carregar_pecas_iniciais,
    carregar_bom_inicial,
    listar_pecas,
    buscar_peca_por_codigo,
    buscar_peca_por_id,
    consultar_estoque_pecas,
    adicionar_peca,
    entrada_estoque_peca,
    saida_manual_peca,
    baixar_estoque_por_bom,
    existe_bom_para_modelo,
    consultar_movimentacoes,
    consultar_pecas_criticas,
    consultar_defeitos_para_relatorio,
    atualizar_custo_peca,
    atualizar_custos_iniciais,
    carregar_bom_modelos_novos,
)
from .pedido import (
    criar_tabelas_pedidos,
    buscar_ultimo_num_pedido_usado,
    registrar_producao_pedido,
    listar_pedidos_reservados,
    buscar_pedido_por_numero,
    confirmar_despacho,
    cancelar_pedido,
    editar_item_pedido,
    atualizar_prioridade_transportadora,
)
