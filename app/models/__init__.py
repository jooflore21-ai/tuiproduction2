from .connection import get_connection
from .scooter import (
    criar_tabelas, carregar_variacoes_iniciais,
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
    consultar_movimentacoes,
    consultar_pecas_criticas,
    consultar_defeitos_para_relatorio,
)
