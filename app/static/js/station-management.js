function updateSpaceUsageCharts() {
    const charts = document.querySelectorAll('.space-usage-chart');
    charts.forEach(chart => {
        const bars = chart.querySelectorAll('.space-bar-fill');
        bars.forEach(bar => {
            const height = bar.style.height;
            bar.style.height = '0';
            setTimeout(() => {
                bar.style.height = height;
            }, 100);
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    updateSpaceUsageCharts();
});
