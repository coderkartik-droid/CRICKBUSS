/**
 * CrickScore Live - Interactive Charts & Match Analytics
 * Implements Worm Graphs, Manhattan Over-by-Over Charts, and Win Probability meters using Chart.js
 */

class MatchCharts {
    static async renderMatchAnalytics(wormCanvasId, manhattanCanvasId, winProbContainerId, matchSlug) {
        try {
            const res = await fetch(`/matches/${matchSlug}/graphs-json/`);
            if (!res.ok) return;
            const data = await res.json();

            // 1. Render Worm Graph
            if (wormCanvasId) {
                const wormCtx = document.getElementById(wormCanvasId);
                if (wormCtx) {
                    new Chart(wormCtx, {
                        type: 'line',
                        data: {
                            labels: data.labels,
                            datasets: data.datasets
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Cumulative Worm Graph (Runs Progression)',
                                    font: { size: 13, weight: 'bold' }
                                },
                                tooltip: { mode: 'index', intersect: false }
                            },
                            scales: {
                                x: {
                                    title: { display: true, text: 'Completed Overs' },
                                    grid: { color: 'rgba(248, 246, 240, 0.12)' }
                                },
                                y: {
                                    title: { display: true, text: 'Total Runs' },
                                    beginAtZero: true,
                                    grid: { color: 'rgba(248, 246, 240, 0.12)' }
                                }
                            }
                        }
                    });
                }
            }

            // 2. Render Manhattan Graph (Runs per Over)
            if (manhattanCanvasId && data.manhattan_datasets) {
                const manhattanCtx = document.getElementById(manhattanCanvasId);
                if (manhattanCtx) {
                    new Chart(manhattanCtx, {
                        type: 'bar',
                        data: {
                            labels: data.labels,
                            datasets: data.manhattan_datasets
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Manhattan Chart (Runs Scored in Each Over)',
                                    font: { size: 13, weight: 'bold' }
                                },
                                tooltip: { mode: 'index', intersect: false }
                            },
                            scales: {
                                x: {
                                    title: { display: true, text: 'Overs' },
                                    grid: { display: false }
                                },
                                y: {
                                    title: { display: true, text: 'Runs in Over' },
                                    beginAtZero: true,
                                    grid: { color: 'rgba(248, 246, 240, 0.12)' }
                                }
                            }
                        }
                    });
                }
            }

            // 3. Render Win Probability Meter
            if (winProbContainerId && data.win_probability) {
                const container = document.getElementById(winProbContainerId);
                if (container) {
                    const wp = data.win_probability;
                    container.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center mb-1 small fw-bold">
                            <span>${wp.team1_name}: ${wp.team1_prob}%</span>
                            <span>${wp.team2_name}: ${wp.team2_prob}%</span>
                        </div>
                        <div class="progress rounded-pill overflow-hidden" style="height: 12px;">
                            <div class="progress-bar bg-emerald" role="progressbar" style="width: ${wp.team1_prob}%" aria-valuenow="${wp.team1_prob}" aria-valuemin="0" aria-valuemax="100"></div>
                            <div class="progress-bar bg-warning" role="progressbar" style="width: ${wp.team2_prob}%" aria-valuenow="${wp.team2_prob}" aria-valuemin="0" aria-valuemax="100"></div>
                        </div>
                        <div class="text-center text-muted small mt-2" style="font-size:0.75rem;">
                            Live algorithmic match predictor based on match conditions and required run rate.
                        </div>
                    `;
                }
            }
        } catch (err) {
            console.error('Failed to load match analytics charts:', err);
        }
    }

    static async renderWormGraph(canvasId, matchSlug) {
        return this.renderMatchAnalytics(canvasId, null, null, matchSlug);
    }

    static renderCareerGraph(canvasId, chartData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx || !chartData) return;

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [
                    {
                        label: 'Total Career Runs',
                        data: chartData.runs,
                        backgroundColor: '#0B1F3A',
                        borderRadius: 6,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Batting Average',
                        data: chartData.averages,
                        type: 'line',
                        borderColor: '#F7E7CE',
                        backgroundColor: '#F7E7CE',
                        tension: 0.3,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { display: true, text: 'Runs Scored' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        title: { display: true, text: 'Batting Average' }
                    }
                }
            }
        });
    }
}

window.MatchCharts = MatchCharts;
