document.addEventListener('DOMContentLoaded', () => {
    let touchStart = 0;
    let pullStarted = false;
    const indicator = document.getElementById('pull-to-refresh-indicator');
    
    document.addEventListener('touchstart', (e) => {
        touchStart = e.touches[0].clientY;
        pullStarted = window.scrollY === 0;
    });

    document.addEventListener('touchmove', (e) => {
        if (!pullStarted) return;
        
        const touch = e.touches[0].clientY;
        const distance = touch - touchStart;
        
        if (distance > 0) {
            e.preventDefault();
            indicator.style.transform = `translateY(${Math.min(distance/2, 100)}px)`;
        }
    });

    document.addEventListener('touchend', () => {
        if (!pullStarted) return;
        
        indicator.style.transform = '';
        if (window.location.href) {
            window.location.reload();
        }
    });
}); 