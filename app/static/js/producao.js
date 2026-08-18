// app/static/script.js

// Espera o HTML carregar completamente para rodar o script
document.addEventListener('DOMContentLoaded', () => {


    // --- ELEMENTOS DO FORMULÁRIO ---
    const edicaoSelect = document.getElementById('edicao-select');
    const tipoRegistroSelect = document.getElementById('tipo-registro-select');

    const modeloGroup = document.getElementById('modelo-group');
    const corChassisGroup = document.getElementById('cor-chassis-group');
    const corParalamaGroup = document.getElementById('cor-paralama-group');
    
    const chassisSection = document.getElementById('chassis-section');
    const paralamaSection = document.getElementById('paralama-section');
    
    const chassisStaticLabel = document.getElementById('chassis-static-label');

    // --- INPUTS ESCONDIDOS ---
    //const tipoRegistroHidden = document.getElementById('tipo_registro_hidden');
    const modeloHidden = document.getElementById('modelo_hidden');
    const corChassisHidden = document.getElementById('cor_chassis_hidden');
    const corParalamaHidden = document.getElementById('cor_paralama_hidden');

    // --- QUANTIDADE ---
    const quantidadeInput = document.getElementById('quantidade');
    const btnDecrement = document.getElementById('decrement');
    const btnIncrement = document.getElementById('increment');
    const quickButtons = document.querySelectorAll('.btn-quick');

    // --- FUNÇÃO PRINCIPAL PARA ATUALIZAR O ESTADO DO FORMULÁRIO ---
    function updateFormState() {
        const tipo = tipoRegistroSelect.value;
        const modelo = modeloHidden.value;

        // Reseta o estado de todos os campos antes de aplicar as novas regras
        chassisSection.classList.remove('disabled');
        paralamaSection.classList.remove('disabled');
        chassisStaticLabel.textContent = '';

        // REGRA 1: Se for "Assistência", desabilita todas as cores.

        // if (!tipoRegistroHidden || !modeloHidden) return;
        if (tipo === 'assistencia') {
            chassisSection.classList.add('disabled');
            paralamaSection.classList.add('disabled');
            return; // Encerra a função aqui
        }

        // REGRA 2: Lógica baseada no MODELO selecionado (quando tipo é "Estoque")
        switch (modelo) {
            case 'TUI':
            case 'TUI MAIS':
            case 'TUI MAIS-S':
            case 'TUI MAIS-LS':
                // Chassis é sempre PRETO e travado.
                chassisSection.classList.add('disabled');
                chassisStaticLabel.textContent = '(Fixo: PRETO)';
                setButtonGroupValue(corChassisGroup, corChassisHidden, 'PRETO');
                paralamaSection.classList.remove('disabled');
                break;

            case 'TUI POP':
            case 'TUI POP-S':
                // Ambos habilitados.
                chassisSection.classList.remove('disabled');
                paralamaSection.classList.remove('disabled');
                break;
        }
    }
    
    // --- FUNÇÃO AUXILIAR PARA CONTROLAR OS GRUPOS DE BOTÕES ---
    function setupButtonGroup(groupElement, hiddenInputElement) {
        groupElement.addEventListener('click', (e) => {
            // Verifica se o clique foi em um botão dentro do grupo
            if (e.target.matches('.btn, .btn-modelo')) {
                // Remove a classe 'active' de todos os botões do grupo
                groupElement.querySelectorAll('.btn, .btn-modelo').forEach(btn => btn.classList.remove('active'));
                
                // Adiciona 'active' apenas ao botão clicado
                e.target.classList.add('active');
                
                // Atualiza o valor do input escondido correspondente
                hiddenInputElement.value = e.target.dataset.value;

                // Sempre que um botão é clicado, reavalia o estado do formulário
                updateFormState();
            }
        });
    }

    if (btnDecrement && btnIncrement) {
        btnDecrement.addEventListener('click', () => {
            let val = parseInt(quantidadeInput.value) || 1;
            if (val > 1) quantidadeInput.value = val - 1;
        });
        btnIncrement.addEventListener('click', () => {
            let val = parseInt(quantidadeInput.value) || 1;
            quantidadeInput.value = val + 1;
        });
    }

    if (quickButtons.length > 0) {
        quickButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                quantidadeInput.value = btn.dataset.value;
            });
        });
    }

    // Função para forçar um valor em um grupo de botões (usado para travar o chassis em 'PRETO')
    function setButtonGroupValue(groupElement, hiddenInputElement, value) {
        groupElement.querySelectorAll('.btn').forEach(btn => {
            if (btn.dataset.value === value) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        hiddenInputElement.value = value;
    }


        // --- LÓGICA DA INTERFACE DE ABAS ---
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault(); // Impede o comportamento padrão do link

            // Remove a classe 'active' de todos os links e painéis
            tabLinks.forEach(item => item.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));

            // Adiciona a classe 'active' ao link clicado
            link.classList.add('active');

            // Pega o ID do painel alvo a partir do href do link (ex: '#visao-geral')
            const targetPaneId = link.getAttribute('href');
            const targetPane = document.querySelector(targetPaneId);

            // Adiciona a classe 'active' ao painel correspondente
            if (targetPane) {
                targetPane.classList.add('active');
            }

            const currentUrl = new URL(window.location);
            // Define o novo valor para o parâmetro 'aba'
            currentUrl.searchParams.set('aba', targetPaneId.substring(1)); // Remove o '#' do início
            
            // Atualiza a URL na barra de endereço sem recarregar a página
            history.pushState(null, '', currentUrl);
        });
    });

    // =================================================================
    // NOVO: LÓGICA PARA SALVAR E RESTAURAR A POSIÇÃO DE SCROLL
    // =================================================================

    // PARTE 1: Restaurar a Posição ao Carregar a Página
    // Isso deve ser uma das primeiras coisas a rodar.
    const savedPosition = localStorage.getItem('scrollPosition');
    if (savedPosition) {
        // Rola a janela para a posição salva
        window.scrollTo(0, parseInt(savedPosition, 10));
        // Limpa a posição salva para que não afete a próxima navegação normal
        localStorage.removeItem('scrollPosition');
    }

    // PARTE 2: Salvar a Posição Antes de Clicar em um Filtro
    // Seleciona todos os links de filtro de período
    const filterLinks = document.querySelectorAll('.filter-controls a');

    filterLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Um instante antes de o navegador seguir o link,
            // salvamos a posição vertical atual do scroll no localStorage.
            localStorage.setItem('scrollPosition', window.scrollY);
        });
    });

    // =================================================================


    // --- LÓGICA DE CONFIRMAÇÃO PARA EXCLUSÃO ---
    const deleteForms = document.querySelectorAll('.form-delete');

    deleteForms.forEach(form => {
        form.addEventListener('submit', (event) => {
            // Exibe a caixa de diálogo de confirmação do navegador
            const confirmed = confirm('Você tem certeza que deseja excluir este registro? Esta ação não pode ser desfeita.');

            // Se o usuário clicar em "Cancelar", impede o envio do formulário
            if (!confirmed) {
                event.preventDefault();
            }
        });
    });

    // --- LÓGICA DO MODAL DE EDIÇÃO ---
    const editModal = document.getElementById('edit-modal');
    
    if (editModal) { // segurança
        const editForm = document.getElementById('edit-form');
        const productNameSpan = document.getElementById('edit-product-name');
        const quantityInput = document.getElementById('edit-quantity');
        const cancelEditBtn = document.getElementById('cancel-edit');
        const editButtons = document.querySelectorAll('.btn-edit');
        const dateInput = document.getElementById('edit-date');

        editButtons.forEach(button => {
            button.addEventListener('click', () => {
                // 1. Coletar os dados do botão clicado
                const id = button.dataset.id;
                const name = button.dataset.name;
                const quantity = button.dataset.quantity;
                const rawDate = button.dataset.date;
                const type = button.dataset.type; // 'producao' ou 'assistencia'


                // 2. Configurar o formulário do modal
                productNameSpan.textContent = name;
                quantityInput.value = quantity;

                if (rawDate) {
                    const formattedDate = rawDate.substring(0, 16).replace(' ', 'T');
                    dateInput.value = formattedDate;
                }
                
                // 3. Montar a URL correta para o 'action' do formulário
                if (type === 'producao') {
                    editForm.action = `/producao/editar/${id}`;
                } else if (type === 'assistencia') {
                    editForm.action = `/assistencia/editar/${id}`;
                }
                
                // 4. Exibir o modal
                editModal.style.display = 'flex';
            });
        });

        // Função para fechar o modal
        function closeModal() {
            editModal.style.display = 'none';
        }

        // Fechar ao clicar no botão "Cancelar"
        cancelEditBtn.addEventListener('click', closeModal);

        // Fechar ao clicar fora do conteúdo do modal (na área escura)
        editModal.addEventListener('click', (event) => {
            if (event.target === editModal) {
                closeModal();
            }
        });
    }

    // --- LÓGICA DO NOVO MODAL DE EDIÇÃO ---
    const addEdicaoModal = document.getElementById('add-edicao-modal');

    if(addEdicaoModal){

        const btnAddEdicao = document.getElementById('btn-add-edicao');
        const btnCancelModal = addEdicaoModal.querySelector('.btn-cancel-modal');
        const addEdicaoForm = document.getElementById('add-edicao-form');
        const edicaoSelect = document.getElementById('edicao-select');
        const newEdicaoNameInput = document.getElementById('new-edicao-name');
    
        btnAddEdicao.addEventListener('click', () => {
            addEdicaoModal.style.display = 'flex';
            newEdicaoNameInput.focus();
        });
        
        function closeModal() {
            addEdicaoModal.style.display = 'none';
            addEdicaoForm.reset();
        }
    
        btnCancelModal.addEventListener('click', closeModal);

        addEdicaoModal.addEventListener('click', (event) => {
            if (event.target === addEdicaoModal) {
                closeModal();
            }
        });
    
        addEdicaoForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const nomeEdicao = newEdicaoNameInput.value.trim();

            if (!nomeEdicao) {
                alert('O nome não pode estar em branco.');
                return;
            }
            
            try {
                const response = await fetch('/edicoes/nova', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nome: nomeEdicao })
                });
    
                const result = await response.json();
    
                if (result.success) {
                    // Cria a nova opção
                    const newOption = document.createElement('option');
                    newOption.value = result.id;
                    newOption.textContent = result.nome;
                    
                    // Adiciona ao select
                    edicaoSelect.appendChild(newOption);
                    
                    // Seleciona a nova opção
                    edicaoSelect.value = result.id;
                    
                    closeModal();
                } else {
                    alert('Erro ao salvar: ' + result.error);
                }
            } catch (error) {
                alert('Ocorreu um erro de comunicação com o servidor.');
            }
        });
    }

        // --- LÓGICA DA BUSCA RÁPIDA (LIVE SEARCH) ---
    function setupLiveSearch(filterContainerId, inputId, tableId, totalCellId) {
        const searchInput = document.getElementById(inputId);
        const table = document.getElementById(tableId);
        const filterContainer = document.getElementById(filterContainerId);
        
        // Verifica se os elementos existem antes de continuar
        if (!searchInput || !table) {
            return;
        }
        
        const tableRows = table.querySelectorAll('tbody tr');
        const totalCell = document.getElementById(totalCellId);

        let activeFilter = 'todos';
        let searchTerm = '';

        function updateTotal() {
            let totalQuantity = 0;
            tableRows.forEach(row => {
                const rowText = row.textContent.toLowerCase();
                
                const productCell = row.querySelector('td:first-child');
                const productText = productCell ? productCell.textContent.trim().toLowerCase() : '';
                const filterText = activeFilter.trim().toLowerCase();

                let modelMatch = true;

                if (filterContainer && activeFilter !== 'todos') {
                    if (filterText === 'tui') {
                        // Garante que começa com "tui"
                        // e não é seguido de "m" (de MAIS) nem "po" (de POP)
                        const regexTui = /^tui(?!\s*m|\s*po)/i;
                        modelMatch = regexTui.test(productText);
                    } else {
                        // Regex genérica para os demais modelos
                        const regex = new RegExp(`^${filterText}(\\s|$)`, 'i');
                        modelMatch = regex.test(productText);
                    }
                }

                const searchMatch = rowText.includes(searchTerm);
                // Verifica se a linha está visível
                if (modelMatch && searchMatch) {
                    row.style.display = '';
                    // Encontra a célula de quantidade na linha
                    const quantityCell = row.querySelector('.quantity-cell');
                    
                    if (quantityCell) {
                        totalQuantity += parseInt(quantityCell.textContent, 10) || 0;
                    }
                } else {
                row.style.display = 'none';
                }
            });

            // Atualiza a célula de total no rodapé
            if (totalCell) {
                totalCell.textContent = totalQuantity;
            }
        }

        if (filterContainer) {
            const filterButtons = filterContainer.querySelectorAll('.filter-btn');
            filterButtons.forEach(button => {
                button.addEventListener('click', () => {
                    filterButtons.forEach(btn => btn.classList.remove('active-filter'));
                    button.classList.add('active-filter');
                    activeFilter = button.dataset.filter;
                    updateTotal();
                });
            });
        }


        // Evento de busca
        searchInput.addEventListener('keyup', () => {
           searchTerm = searchInput.value.toLowerCase();

            updateTotal();
        });

        updateTotal();
    }

    // Inicializa a busca para ambas as tabelas
    setupLiveSearch('model-filters-container', 'search-estoque', 'table-estoque', 'total-estoque');

    setupLiveSearch(null, 'search-producao', 'table-producao', 'total-producao');

    setupLiveSearch(null, 'search-assistencia', 'table-assistencia', 'total-assistencia');

    // Busca da aba "Pedidos": a lista usa .pedido-card (divs), não uma
    // tabela — setupLiveSearch é específico de 'tbody tr', então aqui vai
    // uma busca inline simples por número de pedido (data-num).
    const searchPedidos = document.getElementById('search-pedidos');
    if (searchPedidos) {
        searchPedidos.addEventListener('input', function () {
            const q = this.value.toLowerCase();
            document.querySelectorAll('#lista-pedidos-reservados .pedido-card')
                .forEach(card => {
                    card.style.display =
                        card.dataset.num.toLowerCase().includes(q) ? '' : 'none';
                });
        });
    }

    

    // --- INICIALIZAÇÃO ---
    // Configura o comportamento de 'rádio' para cada grupo de botões

    if (tipoRegistroSelect) {
        tipoRegistroSelect.addEventListener('change', updateFormState);
    }
    if (edicaoSelect) {
        edicaoSelect.addEventListener('change', updateFormState);
    }

    if (modeloGroup && modeloHidden) {
        setupButtonGroup(modeloGroup, modeloHidden);
    }
    if (corChassisGroup && corChassisHidden) {
        setupButtonGroup(corChassisGroup, corChassisHidden);
    }
    if (corParalamaGroup && corParalamaHidden) {
        setupButtonGroup(corParalamaGroup, corParalamaHidden);
    }


    // Chama a função uma vez no início para configurar o estado inicial do formulário
    updateFormState();

    // ── Tipo "Pedido": intercepta o submit e pede o número do pedido ──
    const productionForm = document.getElementById('production-form');
    const modalNumPedido = document.getElementById('modal-num-pedido');
    const inputNumPedido = document.getElementById('input-num-pedido');
    const numPedidoHidden = document.getElementById('num_pedido_hidden');
    const erroNumPedido = document.getElementById('erro-num-pedido');
    const btnConfirmarPedido = document.getElementById('btn-confirmar-pedido');
    const btnCancelarPedido = document.getElementById('btn-cancelar-pedido');

    let pedidoConfirmado = false;

    if (productionForm && modalNumPedido) {
        productionForm.addEventListener('submit', function (e) {
            const tipo = tipoRegistroSelect.value;
            if (tipo === 'pedido' && !pedidoConfirmado) {
                e.preventDefault();
                erroNumPedido.style.display = 'none';
                modalNumPedido.style.display = 'flex';
            }
        });

        btnConfirmarPedido.addEventListener('click', function () {
            const valor = inputNumPedido.value.trim();
            if (!valor) {
                erroNumPedido.style.display = 'block';
                return;
            }
            numPedidoHidden.value = valor;
            modalNumPedido.style.display = 'none';
            pedidoConfirmado = true;
            productionForm.requestSubmit();
        });

        btnCancelarPedido.addEventListener('click', function () {
            modalNumPedido.style.display = 'none';
            tipoRegistroSelect.value = 'estoque';
            updateFormState();
            productionForm.requestSubmit();
        });

        modalNumPedido.addEventListener('click', function (e) {
            if (e.target === this) {
                this.style.display = 'none';
            }
        });
    }
});
