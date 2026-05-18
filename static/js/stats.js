let allData = [];
let chart = null;

document.addEventListener('DOMContentLoaded', async () => {
    await loadStats();
});

async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        allData = data.months || [];
        renderAll(allData);
    } catch (e) {
        document.getElementById('stats-empty').classList.remove('hidden');
    }
}

function filterStats(n) {
    if (n === 0) { renderAll(allData); return; }
    const filtered = allData.slice(-n);
    renderAll(filtered);
    // Update active button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.includes(n === 0 ? '全部' : `近${n}月`));
    });
}

function renderAll(months) {
    renderChart(months);
    renderTable(months);

    const emptyEl = document.getElementById('stats-empty');
    const chartEl = document.querySelector('.chart-container');
    const tableEl = document.querySelector('.stats-table');

    if (months.length === 0) {
        emptyEl.classList.remove('hidden');
        if (chartEl) chartEl.classList.add('hidden');
        if (tableEl) tableEl.classList.add('hidden');
    } else {
        emptyEl.classList.add('hidden');
        if (chartEl) chartEl.classList.remove('hidden');
        if (tableEl) tableEl.classList.remove('hidden');
    }
}

function renderChart(months) {
    const ctx = document.getElementById('stats-chart').getContext('2d');
    if (chart) chart.destroy();

    const labels = months.map(m => {
        const [y, mo] = m.month.split('-');
        return `${y}年${parseInt(mo)}月`;
    });

    chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: '总计',
                    data: months.map(m => m.total),
                    backgroundColor: 'rgba(79, 70, 229, 0.35)',
                    borderColor: '#4f46e5',
                    borderWidth: 1.5,
                    borderRadius: 4,
                },
                {
                    label: '已完成',
                    data: months.map(m => m.completed),
                    backgroundColor: 'rgba(5, 150, 105, 0.5)',
                    borderColor: '#059669',
                    borderWidth: 1.5,
                    borderRadius: 4,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const month = months[ctx.dataIndex];
                            if (ctx.datasetIndex === 1 && month) {
                                return `已完成: ${month.completed} (${month.rate}%)`;
                            }
                            return `${ctx.dataset.label}: ${ctx.raw}`;
                        },
                    },
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 },
                },
            },
        },
    });
}

function renderTable(months) {
    const tbody = document.querySelector('#stats-table tbody');
    tbody.innerHTML = months.map(m => {
        let cls = 'rate-low';
        if (m.rate >= 80) cls = 'rate-high';
        else if (m.rate >= 50) cls = 'rate-mid';
        return `<tr>
            <td>${m.month}</td>
            <td>${m.total}</td>
            <td>${m.completed}</td>
            <td class="${cls}">${m.rate}%</td>
        </tr>`;
    }).join('');
}
