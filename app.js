document.addEventListener("DOMContentLoaded", async () => {
    
    let rawData = [];

    // 1. ბაზის წამოღება (history.json)
    try {
        const response = await fetch('history.json');
        if (response.ok) {
            rawData = await response.json();
        }
    } catch (e) {
        console.log("ისტორიის ფაილი ჯერ არ არსებობს ან ცარიელია.");
    }

    const noDataAlert = document.getElementById("noDataAlert");
    const chartWrapper = document.querySelector(".chart-wrapper");
    if (!rawData || rawData.length === 0) {
        noDataAlert.style.display = "block";
        chartWrapper.style.opacity = "0.2";
        // არ ვწყვეტთ მუშაობას, უბრალოდ გაფრთხილებას ვაჩვენებთ
    }

    const companyColors = {
        'Gulf':      { border: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' }, // Orange
        'Wissol':    { border: '#10b981', bg: 'rgba(16, 185, 129, 0.1)' }, // Green
        'Socar':     { border: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)' }, // Blue
        'Rompetrol': { border: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },  // Red
        'Lukoil':    { border: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.1)' }, // Purple
        'Portal':    { border: '#0ea5e9', bg: 'rgba(14, 165, 233, 0.1)' }, // Light Blue
        'Connect':   { border: '#ec4899', bg: 'rgba(236, 72, 153, 0.1)' }  // Pink
    };

    const fuelTypeSelect = document.getElementById("fuelType");
    const checkboxes = document.querySelectorAll('.toggles-grid input[type="checkbox"]');
    
    const lowestPriceEl = document.getElementById("lowestPrice");
    const lowestCompanyNamesEl = document.getElementById("lowestCompanyNames");
    const averagePriceEl = document.getElementById("averagePrice");
    const trendBadgeEl = document.getElementById("trendBadge");
    const lastUpdatedEl = document.getElementById("lastUpdated");
    const lowestCompanyDisplayEl = document.getElementById("lowestCompanyDisplay");

    let priceChart = null;

    // 2. მთავარი ფუნქცია UI-ის და გრაფიკის გასაახლებლად
    const updateDashboard = () => {
        const selectedFuel = fuelTypeSelect.value;
        const fuelNameKa = fuelTypeSelect.options[fuelTypeSelect.selectedIndex].text;
        const activeCompanies = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);

        lowestCompanyDisplayEl.textContent = `ყველაზე იაფი დღეს (${fuelNameKa})`;

        if (rawData.length > 0) {
            const lastRecord = rawData[rawData.length - 1]; // ყველაზე ახალი ჩანაწერი
            
            // UI სტატისტიკის განახლება მიმდინარე დღის მიხედვით
            let minPrice = Infinity;
            let minCompanies = [];
            let totalSum = 0;
            let count = 0;

            const currentPrices = lastRecord.prices;
            
            Object.keys(currentPrices).forEach(company => {
                if (activeCompanies.includes(company)) {
                    let val = currentPrices[company][selectedFuel];
                    if (val !== null && val !== undefined && !isNaN(val)) {
                        totalSum += val;
                        count++;
                        if (val < minPrice) {
                            minPrice = val;
                            minCompanies = [company];
                        } else if (val === minPrice) {
                            minCompanies.push(company);
                        }
                    }
                }
            });

            if (count > 0) {
                lowestPriceEl.textContent = minPrice.toFixed(2);
                lowestCompanyNamesEl.textContent = "(" + minCompanies.join(', ') + ")";
                const avg = totalSum / count;
                averagePriceEl.textContent = avg.toFixed(2) + " ₾";

                // ტენდენციის გამოთვლა: წინა ჩანაწერს თუ ვპოულობთ (რეალურად ბოლო 24 სთ-ში)
                if (rawData.length > 1) {
                    const prevRecord = rawData[rawData.length - 2];
                    let prevSum = 0; let prevCount = 0;
                    activeCompanies.forEach(c => {
                        let pV = prevRecord.prices[c] && prevRecord.prices[c][selectedFuel];
                        if (pV !== null && pV !== undefined) {
                            prevSum += pV; prevCount++;
                        }
                    });
                    
                    if (prevCount > 0) {
                        const prevAvg = prevSum / prevCount;
                        if (avg > prevAvg) {
                            trendBadgeEl.textContent = `+${((avg-prevAvg)/prevAvg*100).toFixed(1)}% (გაძვირდა)`;
                            trendBadgeEl.className = "stat-badge badge-up";
                        } else if (avg < prevAvg) {
                            trendBadgeEl.textContent = `${((avg-prevAvg)/prevAvg*100).toFixed(1)}% (გაიაფდა)`;
                            trendBadgeEl.className = "stat-badge badge-down";
                        } else {
                            trendBadgeEl.textContent = "ფასი უცვლელია";
                            trendBadgeEl.className = "stat-badge badge-neutral";
                        }
                    }
                } else {
                    trendBadgeEl.textContent = "არასაკმარისი მონაცემები";
                }

            } else {
                lowestPriceEl.textContent = "N/A";
                lowestCompanyNamesEl.textContent = "";
                averagePriceEl.textContent = "- ₾";
            }
            
            const dateObj = new Date(lastRecord.timestamp);
            lastUpdatedEl.textContent = dateObj.toLocaleDateString('ka-GE') + " " + dateObj.getHours() + ":00";
        }

        // 3. გრაფიკის განახლება
        updateChart(selectedFuel, activeCompanies);
    };

    const updateChart = (selectedFuel, activeCompanies) => {
        const labels = rawData.map(d => {
            const dt = new Date(d.timestamp);
            return dt.toLocaleDateString("ka-GE", {day:"numeric", month:"short", hour:"numeric", minute:"2-digit"});
        });

        const datasets = [];

        activeCompanies.forEach(company => {
            const compData = rawData.map(d => d.prices[company] ? d.prices[company][selectedFuel] : null);
            
            datasets.push({
                label: company + ' ₾',
                data: compData,
                borderColor: companyColors[company] ? companyColors[company].border : '#fff',
                backgroundColor: companyColors[company] ? companyColors[company].bg : 'rgba(255,255,255,0.1)',
                borderWidth: 3,
                tension: 0.2, // ნაკლები tension უფრო ნათელი ვარდნებისთვის პირდაპირ მონაცემებზე
                fill: false,
                pointBackgroundColor: '#0d1117',
                pointBorderColor: companyColors[company] ? companyColors[company].border : '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
                spanGaps: true // დაკარგული წერტილების შეერთება
            });
        });

        if (priceChart) {
            priceChart.data.labels = labels;
            priceChart.data.datasets = datasets;
            priceChart.update();
        } else {
            const ctx = document.getElementById('priceChart').getContext('2d');
            
            Chart.defaults.color = '#94a3b8';
            Chart.defaults.font.family = "'Outfit', sans-serif";

            priceChart = new Chart(ctx, {
                type: 'line',
                data: { labels, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top', labels: { usePointStyle: true, padding: 20 } },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            titleColor: '#f8fafc',
                            bodyColor: '#e2e8f0',
                            borderColor: 'rgba(255,255,255,0.1)',
                            borderWidth: 1,
                            padding: 12
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
                            ticks: { callback: (value) => value.toFixed(2) + ' ₾' }
                        },
                        x: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false }
                        }
                    },
                    interaction: { mode: 'nearest', axis: 'x', intersect: false }
                }
            });
        }
    };

    fuelTypeSelect.addEventListener('change', updateDashboard);
    checkboxes.forEach(cb => cb.addEventListener('change', updateDashboard));

    // პირველადი ჩატვირთვა
    updateDashboard();
});
