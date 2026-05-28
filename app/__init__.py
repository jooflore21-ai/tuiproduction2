from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'estoque-tui'

    # Registra blueprints
    from app.routes import main_bp, producao_bp, saida_bp, estoque_bp
    from app.routes.pecas import pecas_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(producao_bp)
    app.register_blueprint(saida_bp)
    app.register_blueprint(estoque_bp)
    app.register_blueprint(pecas_bp)

    # Aliases de endpoint: preserva os nomes originais sem tocar nos templates
    _aliases = {
        'landing_page':        'main.landing_page',
        'producao':            'producao.producao',
        'saidas':              'saida.saidas',
        'estoque_geral':       'estoque.estoque_geral',
        'excluir_producao':    'producao.excluir_producao',
        'excluir_assistencia': 'producao.excluir_assistencia',
        'editar_producao':     'producao.editar_producao',
        'editar_assistencia':  'producao.editar_assistencia',
        'excluir_saida':       'saida.excluir_saida',
        'editar_saida':        'saida.editar_saida',
        'nova_edicao':         'producao.nova_edicao',
        # Peças
        'pecas':               'pecas.listar_pecas',
        'nova_peca':           'pecas.nova_peca',
        'movimentacoes_pecas': 'pecas.movimentacoes',
        'pecas_criticas':      'pecas.criticas',
        'defeitos_pecas':      'pecas.defeitos',
    }
    for alias, real in _aliases.items():
        if real in app.view_functions:
            app.view_functions[alias] = app.view_functions[real]
        if real in app.url_map._rules_by_endpoint:
            app.url_map._rules_by_endpoint[alias] = app.url_map._rules_by_endpoint[real]

    return app
