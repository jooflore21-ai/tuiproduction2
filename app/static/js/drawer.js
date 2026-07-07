document.addEventListener('DOMContentLoaded', function () {
    const drawer = document.getElementById('nav-drawer');
    const btnDrawer = document.getElementById('btn-drawer');
    const drawerOverlay = document.getElementById('nav-drawer-overlay');

    if (btnDrawer && drawer) {
        function openDrawer() { drawer.classList.add('open'); }
        function closeDrawer() { drawer.classList.remove('open'); }

        btnDrawer.addEventListener('click', openDrawer);
        if (drawerOverlay) {
            drawerOverlay.addEventListener('click', closeDrawer);
        }

        drawer.querySelectorAll('#nav-drawer-panel a')
              .forEach(a => a.addEventListener('click', closeDrawer));
    }
});
