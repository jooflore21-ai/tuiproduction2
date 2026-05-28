# test_models.py
import os
from app import models

# NOME DO ARQUIVO DO BANCO DE DADOS PARA TESTE
DB_FILE = "teste.db"

def run_tests():
    """
    Executa uma sequência de testes nas funções do models.py.
    """
    print("--- INICIANDO TESTES DO MODELS.PY ---")

    # Garante que estamos começando com um banco de dados limpo
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Arquivo de banco de dados '{DB_FILE}' antigo removido.")

    # Aponta o models para usar o banco de dados de teste
    models.NOME_BANCO_DE_DADOS = DB_FILE

    # 1. Teste de criação de tabelas e carregamento inicial
    print("\n[PASSO 1] Criando tabelas e carregando dados iniciais...")
    models.criar_tabelas()
    models.carregar_variacoes_iniciais()
    print("OK! Tabelas criadas com sucesso.")

    # 2. Teste de registro de produção (Estoque)
    print("\n[PASSO 2] Registrando 5 unidades de 'TUI AMARELO' para o estoque...")
    models.registrar_producao("TUI AMARELO", 5)
    models.registrar_producao("TUI MAIS AZUL", 5)

    print("OK! Produção registrada.")

    # 3. Teste de registro de assistência
    print("\n[PASSO 3] Registrando 2 unidades de 'TUI POP' para assistência...")
    models.registrar_assistencia("TUI POP", 2)
    print("OK! Assistência registrada.")

    # 4. Teste de consulta de estoque
    print("\n[PASSO 4] Consultando o estoque...")
    estoque = models.consultar_estoque()
    print("Estoque atual de 'TUI AMARELO':")
    for item in estoque:
        if item['nome_completo'] == 'TUI AMARELO':
            print(dict(item))
            # Verifica se o estoque foi atualizado corretamente
            assert item['estoque_atual'] == 5

    # 5. Teste de consulta de produção diária
    print("\n[PASSO 5] Consultando a produção diária...")
    producao_dia = models.consultar_producao(periodo="diario")
    print("Produção de hoje (Estoque):")
    print([dict(p) for p in producao_dia])
    assert len(producao_dia) > 0

    # 6. Teste de consulta de assistência diária
    print("\n[PASSO 6] Consultando a assistência diária...")
    assistencia_dia = models.consultar_assistencia(periodo="diario")
    print("Embalado hoje (Assistência):")
    print([dict(a) for a in assistencia_dia])
    assert len(assistencia_dia) > 0
    
    print("\n--- TESTES CONCLUÍDOS COM SUCESSO! ---")

# Executa a função de teste
if __name__ == "__main__":
    run_tests()