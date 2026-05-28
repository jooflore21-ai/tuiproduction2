from app import app
from app.models import init_db

if __name__ == "__main__":
    print("--------------------------------------------------")
    print("Inicializando o banco de dados...")
    # Garante que as tabelas e os produtos/variações base existam
    init_db()
    print("Banco de dados pronto para uso.")
    print("--------------------------------------------------")

    app.run(debug=True, host="0.0.0.0", port=5000)

