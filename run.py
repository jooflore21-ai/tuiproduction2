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

    app.run(host='0.0.0.0', port=5000, debug=True)
