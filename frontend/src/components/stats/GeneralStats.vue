<template>
<div class="creator-topology-stats">
    <div
    class="section-header creator-header"
    @click="showGeneralData = !showGeneralData"
    role="button"
    tabindex="0"
    >
    GENERAL STATISTICS
    <div class="toggle-indicator">{{ showGeneralData ? "▲" : "▼" }}</div>
</div>

<transition name="slide-fade">
    <div v-if="showGeneralData" class="section-content">
        <div class="chart-container">
            <LineChart
                :data="lineChartData"
                :options="lineOptions"
                :style="{ width: '100%', height: '400px' }"
            />
        </div>
        <div class="chart-container">
            <PieChart
                :data="seriesLengthPieData"
                :options="pieOptionsSeriesLength"
                :style="{ width: '100%', height: '350px' }"
            />
        </div>
        <div class="chart-container">
            <BarChart
                :data="topSeriesByIssuesData"
                :options="barOptionsTopSeries"
                :style="{ width: '100%', height: '320px' }"
            />
        </div>
            <div class="chart-container">
            <BarChart
                :data="seriesLongestRunningData"
                :options="barOptionsLongestSeries"
                :style="{ width: '100%', height: '320px' }"
            />
        </div>
        <div class="chart-container" style="height: 400px;">
            <canvas v-if="releaseDateHeatmapData" ref="heatmapCanvas"></canvas>
        </div>
    </div>
</transition>

</div>
</template>

<script>
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Filler,
} from "chart.js";
import { Line, Bar, Pie } from "vue-chartjs";
import { MatrixController, MatrixElement } from 'chartjs-chart-matrix';

ChartJS.register(MatrixController, MatrixElement);

ChartJS.register(
    Title,
    Tooltip,
    Legend,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Filler
);
export default {
    name: "GeneralStats",
    props: {
        issues: {
        type: Array,
        required: true,
        },
    },
    components: {
        BarChart: Bar,
        LineChart: Line,
        PieChart: Pie,
    },
    data() {
    return {
        minYear: null,
        maxYear: null,
        showGeneralData: false,
        lineChartData: { labels: [], datasets: [] },
        barChartData: { labels: [], datasets: [] },
        seriesLongestRunningData: { labels: [], datasets: [] },
        barOptionsLongestSeries: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
            legend: { display: false },
            title: { display: true, text: "Longest Running Series (years)" },
            },
            scales: {
    x: {
        ticks: {
            callback: function(value) {
                const str = this.getLabelForValue(value);
                const maxLength = 15; 
                if (str.length <= maxLength) return str;

                const words = str.split(' ');
                const lines = [];
                let currentLine = '';

                for (let word of words) {
                    if ((currentLine + ' ' + word).trim().length > maxLength) {
                        lines.push(currentLine.trim());
                        currentLine = word;
                    } else {
                        currentLine += ' ' + word;
                    }
                }
                if (currentLine) lines.push(currentLine.trim());

                return lines;
            }
        }
    }
            }


        },
        seriesLengthPieData: { labels: [], datasets: [] },
        pieOptionsSeriesLength: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
            padding: 20,  
            },
            plugins: {
            title: {
                display: true,
                text: "Distribution of Series by Number of Issues",
            },
            },
        },
        topSeriesByIssuesData: { labels: [], datasets: [] },
        barOptionsTopSeries: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
            legend: { display: false },
            title: { display: true, text: "Top Series by Number of Issues" },
            },
            indexAxis: 'y', 
        },
        releaseDateHeatmapData: null,
        heatmapOptions: {}, 
        showHeatmapData: true,
    };
    },
    computed: {
        creatorSeries() {
        if (!this.selectedCreator) return [];
        const seriesSet = this.creatorSeriesMap[this.selectedCreator];
        if (!seriesSet) return [];
        return Array.from(seriesSet).sort();
        },
    },
    watch: {
        issues: {
        immediate: true,
        handler() {
            if (this.issues && this.issues.length) {
            this.prepareCharts();
            }
        },
        },
        showGeneralData(val) {
            if (val) {
            this.$nextTick(() => {
                this.renderHeatmap();
            });
            }
        }
    },
    methods: {
        parseCreatorsDetailed(creatorsStr) {
        if (!creatorsStr) return {};

        const entries = creatorsStr
            .split(/[,;]+/)
            .map((s) => s.trim())
            .filter(Boolean);

        const creatorsByRole = {};

        for (let entry of entries) {
            entry = entry.replace(/\s*(\(\d+\)|\[\d+\])$/, "").trim();

            let match = entry.match(/^([^:]+):\s*(.+)$/);
            if (match) {
            const role = match[1].trim();
            const name = match[2].trim();
            if (!creatorsByRole[role]) creatorsByRole[role] = [];
            creatorsByRole[role].push(name);
            continue;
            }

            match = entry.match(/^(.+?)\s*\(([^)]+)\)$/);
            if (match) {
            const name = match[1].trim();
            const role = match[2].trim();
            if (!creatorsByRole[role]) creatorsByRole[role] = [];
            creatorsByRole[role].push(name);
            continue;
            }

            if (!creatorsByRole["Unknown"]) creatorsByRole["Unknown"] = [];
            creatorsByRole["Unknown"].push(entry);
        }

        return creatorsByRole;
        },
        prepareCharts() {
            this.prepareSeriesPerYearChart();
            this.prepareLongestRunningSeriesChart();
            this.prepareSeriesLengthDistributionPieChart();
            this.prepareTopSeriesByIssuesChart();
            this.prepareReleaseDateHeatmap();
        },
        prepareSeriesPerYearChart() {
            const seriesYearsCount = new Map();

            this.issues.forEach((issue) => {
                const startYear = issue.series_start_year;
                if (!startYear) return;
                seriesYearsCount.set(startYear, (seriesYearsCount.get(startYear) || 0) + 1);
            });

            const yearsSorted = Array.from(seriesYearsCount.keys()).sort((a, b) => a - b);
            if (yearsSorted.length === 0) {
                this.lineChartData.labels = [];
                this.lineChartData.datasets = [];
                return;
            }

            const minYear = yearsSorted[0];
            const maxYear = yearsSorted[yearsSorted.length - 1];
            const allYears = [];
            for (let y = minYear; y <= maxYear; y++) allYears.push(y);

            const counts = allYears.map((year) => seriesYearsCount.get(year) || 0);

            this.lineChartData = {
                labels: allYears.map(String),
                datasets: [
                {
                    label: "Series created",
                    data: counts,
                    borderColor: "#2c7be5",
                    backgroundColor: "rgba(44,123,229,0.12)",
                    tension: 0.35,
                    fill: true,
                    pointRadius: 4,
                },
                ],
            };
        },
        prepareSeriesLengthDistributionPieChart() {
            const seriesIssueCounts = new Map();

            this.issues.forEach(issue => {
            const sid = issue.series_id;
            if (!sid) return;
            seriesIssueCounts.set(sid, (seriesIssueCounts.get(sid) || 0) + 1);
            });

            const buckets = {
            '1': 0,
            '2-10': 0,
            '11-50': 0,
            '51-100': 0,
            '101-200': 0,
            '201+': 0,
            };

            seriesIssueCounts.forEach(count => {
            if (count <= 1) buckets['1']++;
            else if (count <= 10) buckets['2-10']++;
            else if (count <= 50) buckets['11-50']++;
            else if (count <= 100) buckets['51-100']++;
            else if (count <= 200) buckets['101-200']++;
            else buckets['201+']++;
            });

            this.seriesLengthPieData = {
            labels: Object.keys(buckets),
            datasets: [{
                data: Object.values(buckets),
                backgroundColor: [
                '#f6c85f',
                '#7bd389',
                '#63a4ff',
                '#9b7bff',
                '#ff7b9c',
                '#f9499d'
                ],
                hoverOffset: 30,
            }],
            };
        },
        renderHeatmap() {
            if (!this.releaseDateHeatmapData) return;
            if (this.heatmapChart) this.heatmapChart.destroy();

            const ctx = this.$refs.heatmapCanvas.getContext('2d');
            this.heatmapChart = new ChartJS(ctx, {
                type: 'matrix',
                data: this.releaseDateHeatmapData,
                options: this.heatmapOptions,
            });
        },
        prepareReleaseDateHeatmap() {
        const counts = {};
        let minYear = 9999;
        let maxYear = 0;

        this.issues.forEach(issue => {
            if (!issue.release_date || issue.is_variant) return;
            const dateParts = issue.release_date.split('-');
            if (dateParts.length < 2) return;
            const y = parseInt(dateParts[0], 10);
            const month = parseInt(dateParts[1], 10) - 1;
            if (isNaN(y) || isNaN(month) || month < 0 || month > 11) return;
            if (y < minYear) minYear = y;
            if (y > maxYear) maxYear = y;
        });

        if (minYear === 9999 || maxYear === 0) {
            console.warn("No valid release dates found.");
            this.releaseDateHeatmapData = { datasets: [] };
            return;
        }

        const minDecade = Math.floor(minYear / 5) * 5;
        const maxDecade = Math.floor(maxYear / 5) * 5;

        this.issues.forEach(issue => {
            if (!issue.release_date || issue.is_variant) return;
            const dateParts = issue.release_date.split('-');
            if (dateParts.length < 2) return;
            const y = parseInt(dateParts[0], 10);
            const month = parseInt(dateParts[1], 10) - 1;
            if (isNaN(y) || isNaN(month) || month < 0 || month > 11) return;
            const decade = Math.floor(y / 5) * 5;
            const key = `${decade}-${month}`;
            counts[key] = (counts[key] || 0) + 1;
        });

        const monthLabels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        const decadesCount = (maxDecade - minDecade) / 5 + 1;
        const decadeLabels = Array.from(
            { length: decadesCount },
            (_, i) => `${minDecade + i * 5}-${minDecade + i * 5 + 4}`
        );

        
        const data = [];
        for (let i = 0; i < decadesCount; i++) {
            const decade = minDecade + i * 5  ;
            const decadeLabel = decadeLabels[i];
            for (let month = 0; month < 12; month++) {
            const monthLabel = monthLabels[month];
            const key = `${decade}-${month}`;
            data.push({ x: monthLabel, y: decadeLabel, v: counts[key] || 0 });
            }
        }
        
        const minCount = 1;    
        const maxCount = Math.max(...Object.values(counts));

        this.releaseDateHeatmapData = {
            datasets: [{
            label: "Issues Released",
            data,
            backgroundColor: ctx => {
                const value = ctx.dataset.data[ctx.dataIndex].v;
                if (value === 0) return 'rgba(0,0,0,0)';  

                const logMin = Math.log(minCount);
                const logMax = Math.log(maxCount);
                const logVal = Math.log(value);

                const ratio = (logVal - logMin) / (logMax - logMin);

                const r = Math.round(44 + ratio * (229 - 44));
                const g = Math.round(123 + ratio * (44 - 123));
                const b = Math.round(229 + ratio * (44 - 229));

                return `rgba(${r},${g},${b},1)`;
            },
            borderWidth: 1,
            borderColor: "white",
            width: ctx => {
                const chartArea = ctx.chart.chartArea;
                if (!chartArea) return 0;
                return (chartArea.right - chartArea.left) / 12 - 2;
            },
            height: ctx => {
                const chartArea = ctx.chart.chartArea;
                if (!chartArea) return 0;
                return (chartArea.bottom - chartArea.top) / decadeLabels.length - 2;
            },
            }],
        };

        this.heatmapOptions = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
            x: {
                type: "category",
                labels: monthLabels,
                offset: true,
                grid: { display: false },
            },
            y: {
                type: "category",
                labels: decadeLabels,
                offset: true,
                grid: { display: false },
                reverse: true,  
            },
            },
            plugins: {
            legend: { display: false },
            title: {
                display: true,
                text: "Issues Released Over Time",
                font: { size: 18, weight: "bold" },
                padding: { top: 10, bottom: 20 }
            },
            tooltip: {
                callbacks: {
                title(ctx) {
                    const month = ctx[0].label;
                    const decade = ctx[0].dataset.data[ctx[0].dataIndex].y;
                    return `${month} (${decade})`;
                },
                label(ctx) {
                    return `Issues: ${ctx.raw.v}`;
                },
                },
            },
            },
        };

        },
        prepareTopSeriesByIssuesChart() {
    const seriesMap = new Map();

    this.issues.forEach(issue => {
        const sid = issue.series_id;
        if (!sid) return;

        if (!seriesMap.has(sid)) {
            seriesMap.set(sid, {
                title: issue.series_title || "Unknown",
                startYear: issue.series_start_year || null,
                count: 0,
            });
        }
        seriesMap.get(sid).count++;
    });

    const sorted = Array.from(seriesMap.values())
        .sort((a, b) => b.count - a.count)
        .slice(0, 10);

    this.topSeriesByIssuesData = {
        labels: sorted.map(s => `${s.title} (${s.startYear || "N/A"})`),
        datasets: [
            {
                label: "Number of Issues",
                data: sorted.map(s => s.count),
                backgroundColor: "#2c7be5",
            },
        ],
    };
        },

        prepareLongestRunningSeriesChart() {
            const currentYear = new Date().getFullYear();

            const seriesMap = new Map();

            this.issues.forEach((issue) => {
                const sid = issue.series_id;
                if (!sid) return;

                if (!seriesMap.has(sid)) {
                const startYear = issue.series_start_year;
                let endYear = issue.series_end_year;

                const validStart = startYear && startYear >= 1900 && startYear <= currentYear;
                if (!validStart) return;

                if (!endYear || endYear > currentYear) {
                    endYear = currentYear;
                }

                seriesMap.set(sid, {
                    title: issue.series_title + " (" + startYear + ")" || "Unknown",
                    startYear,
                    endYear,
                    originalEndYear: issue.series_end_year || null, 
                });
                }
            });

            const finishedSeries = [];
            const ongoingSeries = [];

            for (const series of seriesMap.values()) {
                const yearsRunning = series.endYear - series.startYear + 1;

                if (yearsRunning <= 0 || yearsRunning > 200) continue;

                if (series.originalEndYear && series.originalEndYear < 2099) {
                finishedSeries.push({ ...series, yearsRunning });
                } else {
                ongoingSeries.push({ ...series, yearsRunning });
                }
            }

            finishedSeries.sort((a, b) => b.yearsRunning - a.yearsRunning);
            ongoingSeries.sort((a, b) => b.yearsRunning - a.yearsRunning);

            const combined = finishedSeries.concat(ongoingSeries).slice(0, 20);

            this.seriesLongestRunningData = {
                labels: combined.map(s => s.title),
                datasets: [
                {
                    label: "Years Running",
                    data: combined.map(s => s.yearsRunning),
                    backgroundColor: combined.map(s => (s.originalEndYear && s.originalEndYear < 2099 ? "#ff7b9c" : "#7bd389")),
                },
                ],
            };
        },

    },
};
</script>

<style scoped>
.creator-topology-stats {
  max-width: 100%;
  margin: 1.5rem auto;
  padding: 0 12px;
  text-align: center;
}

.creator-header {
  cursor: pointer;
  font-weight: 900;
  font-size: 1.8rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  text-align: center;
  user-select: none;
  padding: 1rem 0;
  position: relative;
  margin: 2rem 0 1rem 0;
  font-family: "Poppins", "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(240,240,240,0.8) 100%);
  border-radius: 8px;
  color: #2c7be5;
  transition: background-color 0.3s ease;
}
.topology-header:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.toggle-indicator {
  font-size: 1.2rem;
  margin-top: 0.3rem;
  user-select: none;
  display: inline-block;
  transition: transform 0.3s ease;
}

.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
}
.slide-fade-enter-to,
.slide-fade-leave-from {
  max-height: 1000px;
  opacity: 1;
  overflow: hidden;
}

.topology-wrapper {
  display: flex;
  gap: 20px;
  align-items: stretch;
  justify-content: center;
}

.chart-container {
  margin: 30px auto;
  padding: 20px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  position: relative;
  flex: 1;
  min-width: unset;
}

.creator-legend {
  width: 300px;
  background: #f4f9f4;
  border: 1px solid #7bd389;
  border-radius: 8px;
  padding: 20px;
  overflow-y: auto;
  font-size: 14px;
  user-select: text;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
  height: 650px; 
}

.default-text {
  color: #666;
  font-style: italic;
  margin-top: 1rem;
  user-select: none;
}

.series-list {
  margin: 0;
  padding-left: 20px;
  max-height: 500px;
  overflow-y: auto;
  user-select: text;
}
</style>
