/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class RoutyDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.chartRef = useRef("chart");
        this.data = {};

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        this.data = await this.orm.call(
            "routy.dashboard",
            "get_dashboard_data",
            []
        );
        this.updateUI();
    }

    updateUI() {
        // Update KPIs
        document.querySelector('.today_requests').textContent = this.data.today_requests || 0;
        document.querySelector('.today_deliveries').textContent = this.data.today_deliveries || 0;
        document.querySelector('.active_drivers').textContent = this.data.active_drivers || 0;
        document.querySelector('.today_revenue').textContent = (this.data.today_revenue || 0).toFixed(2);
        document.querySelector('.pending_parcels').textContent = this.data.pending_parcels || 0;
        document.querySelector('.success_rate').textContent = this.data.success_rate || 0;
        document.querySelector('.open_incidents').textContent = this.data.open_incidents || 0;
        document.querySelector('.currency_symbol').textContent = this.data.currency_symbol || '$';

        // Update chart
        this.renderChart();

        // Update top drivers
        this.renderTopDrivers();
    }

    renderChart() {
        const ctx = document.getElementById('deliveriesChart');
        if (!ctx) return;

        const labels = this.data.chart_data.map(d => d.label);
        const values = this.data.chart_data.map(d => d.count);

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Deliveries',
                    data: values,
                    borderColor: '#4e73df',
                    backgroundColor: 'rgba(78, 115, 223, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    renderTopDrivers() {
        const container = document.querySelector('.top_drivers_list');
        if (!container) return;

        let html = '';
        if (this.data.top_drivers && this.data.top_drivers.length > 0) {
            this.data.top_drivers.forEach((driver, index) => {
                html += `
                    <div class="mb-3">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="font-weight-bold">${index + 1}. ${driver.name}</span>
                            <span class="badge badge-primary">${driver.count} jobs</span>
                        </div>
                        <div class="progress mt-1" style="height: 8px;">
                            <div class="progress-bar bg-primary"
                                 style="width: ${(driver.count / this.data.top_drivers[0].count) * 100}%">
                            </div>
                        </div>
                    </div>
                `;
            });
        } else {
            html = '<p class="text-muted text-center">No data available</p>';
        }
        container.innerHTML = html;
    }
}

RoutyDashboard.template = "routy.Dashboard";

registry.category("actions").add("routy_dashboard", RoutyDashboard);

export default RoutyDashboard;
