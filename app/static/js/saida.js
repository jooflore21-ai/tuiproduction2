document.addEventListener('DOMContentLoaded', () => {

    // ===========================================================
    // GRUPOS DE BOTÕES
    // ===========================================================
    function setupButtonGroup(groupElement, hiddenInputElement) {
        if (!groupElement || !hiddenInputElement) return;

        const activeBtn = groupElement.querySelector('.btn.active');
        if (activeBtn && activeBtn.dataset.value !== undefined) {
            hiddenInputElement.value = activeBtn.dataset.value;
        }

        groupElement.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn');
            if (!btn || !groupElement.contains(btn)) return;

            groupElement.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const val = btn.dataset.value;
            if (typeof val !== 'undefined') hiddenInputElement.value = val;
        });
    }

    setupButtonGroup(document.getElementById('motivo-group'),    document.getElementById('motivo_hidden'));
    setupButtonGroup(document.getElementById('modelo-group'),    document.getElementById('modelo_hidden'));
    setupButtonGroup(document.getElementById('cor-paralama-group'), document.getElementById('cor_paralama_hidden'));

    // ===========================================================
    // QUANTIDADE
    // ===========================================================
    const quantityInputEl = document.getElementById('quantidade');
    const minusBtn        = document.getElementById('decrement');
    const plusBtn         = document.getElementById('increment');

    if (quantityInputEl && minusBtn && plusBtn) {
        minusBtn.addEventListener('click', () => {
            let val = parseInt(quantityInputEl.value) || 1;
            if (val > 1) quantityInputEl.value = val - 1;
        });
        plusBtn.addEventListener('click', () => {
            let val = parseInt(quantityInputEl.value) || 1;
            quantityInputEl.value = val + 1;
        });
        document.querySelectorAll('.btn-quick').forEach(btn => {
            btn.addEventListener('click', () => { quantityInputEl.value = btn.dataset.value; });
        });
    }

    // ===========================================================
    // ACORDEÃO — expandir / recolher itens do pedido
    // ===========================================================
    document.querySelectorAll('.btn-toggle-pedido').forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.target;
            const pedidoRow = btn.closest('.pedido-row');
            const itemRows = document.querySelectorAll(`.item-row[data-parent="${target}"]`);
            const isExpanded = pedidoRow.dataset.expanded === 'true';

            itemRows.forEach(row => {
                row.style.display = isExpanded ? 'none' : '';
            });

            pedidoRow.dataset.expanded = String(!isExpanded);
            btn.classList.toggle('expanded', !isExpanded);
            btn.textContent = isExpanded ? '›' : '↓';
        });
    });

    // ===========================================================
    // BUSCA POR Nº PEDIDO
    // ===========================================================
    const searchInput = document.getElementById('search-saidas');
    const totalCell   = document.getElementById('total-saidas');

    function calcTotal() {
        let total = 0;
        document.querySelectorAll('.pedido-row').forEach(row => {
            if (row.style.display === 'none') return;
            const target = row.querySelector('.btn-toggle-pedido')?.dataset.target;
            if (!target) return;
            document.querySelectorAll(`.item-row[data-parent="${target}"]`).forEach(ir => {
                const qtyCell = ir.querySelector('.quantity-cell');
                if (qtyCell) total += parseInt(qtyCell.textContent, 10) || 0;
            });
        });
        if (totalCell) totalCell.textContent = total;
    }

    if (searchInput) {
        searchInput.addEventListener('keyup', () => {
            const term = searchInput.value.toLowerCase().trim();

            document.querySelectorAll('.pedido-row').forEach(row => {
                const pedidoNum = (row.querySelector('strong')?.textContent || '').toLowerCase();
                const visible = !term || pedidoNum.includes(term);

                row.style.display = visible ? '' : 'none';

                // Se o pedido fica oculto, esconde também seus itens
                const target = row.querySelector('.btn-toggle-pedido')?.dataset.target;
                if (target && !visible) {
                    document.querySelectorAll(`.item-row[data-parent="${target}"]`).forEach(ir => {
                        ir.style.display = 'none';
                    });
                }
            });

            calcTotal();
        });
    }

    calcTotal();

    // ===========================================================
    // CONFIRMAÇÃO DE EXCLUSÃO
    // ===========================================================
    document.querySelectorAll('.form-delete').forEach(form => {
        form.addEventListener('submit', (event) => {
            const confirmed = confirm('Excluir este item? O estoque será devolvido.');
            if (!confirmed) event.preventDefault();
        });
    });

    // ===========================================================
    // MODAL DE EDIÇÃO
    // ===========================================================
    const editModal = document.getElementById('edit-modal');

    if (editModal) {
        const editForm       = document.getElementById('edit-form');
        const productNameSpan = document.getElementById('edit-product-name');
        const quantityInput  = document.getElementById('edit-quantity');
        const cancelEditBtn  = document.getElementById('cancel-edit');

        document.querySelectorAll('.btn-edit').forEach(button => {
            button.addEventListener('click', () => {
                const id       = button.dataset.id;
                const name     = button.dataset.name;
                const quantity = button.dataset.quantity;
                const type     = button.dataset.type;

                productNameSpan.textContent = name;
                quantityInput.value = quantity;

                if (type === 'saida') {
                    editForm.action = `/saidas/editar/${id}`;
                }

                editModal.style.display = 'flex';
            });
        });

        function closeModal() { editModal.style.display = 'none'; }
        cancelEditBtn.addEventListener('click', closeModal);
        editModal.addEventListener('click', e => { if (e.target === editModal) closeModal(); });
    }

    // ===========================================================
    // MEMÓRIA DE SCROLL
    // ===========================================================
    const savedPosition = localStorage.getItem('scrollPosition');
    if (savedPosition) {
        window.scrollTo(0, parseInt(savedPosition, 10));
        localStorage.removeItem('scrollPosition');
    }
    document.querySelectorAll('.filter-controls a').forEach(link => {
        link.addEventListener('click', () => {
            localStorage.setItem('scrollPosition', window.scrollY);
        });
    });
});
