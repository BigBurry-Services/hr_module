document.addEventListener('DOMContentLoaded', function() {
    const menuIcon = document.getElementById('menuIcon');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const dashboardLayout = document.querySelector('.dashboard-layout');

    if (menuIcon && sidebar && mainContent && dashboardLayout) {
        menuIcon.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            menuIcon.classList.toggle('active');
            // Toggle body overflow to prevent scrolling when sidebar is open on mobile
            document.body.classList.toggle('no-scroll');
            // On mobile, the main content should not be offset, but an overlay appears
            if (window.innerWidth <= 768) { // Assuming 768px as breakpoint for mobile
                dashboardLayout.classList.toggle('overlay-active');
            }
        });

        // Close sidebar if clicking outside of it on mobile
        dashboardLayout.addEventListener('click', function(event) {
            if (sidebar.classList.contains('active') && !sidebar.contains(event.target) && !menuIcon.contains(event.target) && window.innerWidth <= 768) {
                sidebar.classList.remove('active');
                menuIcon.classList.remove('active');
                document.body.classList.remove('no-scroll');
                dashboardLayout.classList.remove('overlay-active');
            }
        });

        // Adjust sidebar state on window resize
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768) {
                sidebar.classList.remove('active'); // Ensure sidebar is closed on desktop if it was open on mobile
                menuIcon.classList.remove('active');
                document.body.classList.remove('no-scroll');
                dashboardLayout.classList.remove('overlay-active');
            }
        });
    }
});