from app import create_app
from app import models

app = create_app()

if __name__ == '__main__':
    # Garante que as tabelas e dados iniciais existam
    models.criar_tabelas()
    models.carregar_variacoes_iniciais()
    models.criar_tabelas_pecas()
    models.carregar_pecas_iniciais()
    models.carregar_bom_inicial()
    models.atualizar_custos_iniciais()
    models.carregar_bom_modelos_novos()
    models.carregar_variacoes_modelos_novos()
    models.migrar_motivos_saida()
    models.criar_tabelas_pedidos()

    app.run(host='0.0.0.0', port=5000, debug=True)
