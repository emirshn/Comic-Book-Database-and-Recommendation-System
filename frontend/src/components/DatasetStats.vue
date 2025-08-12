<template>
  <div class="dataset-stats">
    <header class="app-header">
      <h1>Comic Book Database</h1>
    </header>
    <button @click="$router.push('/series')" class="btn-series">To Search Comics</button>

    <h2>Dataset Stats</h2>

    <div v-if="loading">Loading data...</div>
    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="!loading && !error">
      
       <CreatorStats :issues="issuesStore.issues" />

      <div
        class="section-header general-header"
        @click="showGeneralData = !showGeneralData"
        role="button"
        tabindex="0"
      >
        GENERAL STATISTICS
        <div class="toggle-indicator">{{ showGeneralData ? "▲" : "▼" }}</div>
      </div>
      <transition name="slide-fade">  
        <div v-show="showGeneralData" class="section-content">
          
          <div class="chart-container">
            <LineChart
              :data="lineChartData"
              :options="lineOptions"
              :style="{ width: '100%', height: '320px' }"
            />
          </div>

            <div v-show="showHeatmapData" class="section-content" style="height: 600px;">
              <canvas v-if="releaseDateHeatmapData" ref="heatmapCanvas"></canvas>
            </div>

          <div class="chart-container">
            <PieChart
              :data="seriesLengthPieData"
              :options="pieOptionsSeriesLength"
              :style="{ width: '100%', height: '360px' }"
            />
          </div>

            <div class="chart-container" style="height: 300px;">
              <BarChart
                :data="topSeriesByIssuesData"
                :options="barOptionsTopSeries"
              />
            </div>

        </div>
      </transition>

      <div
        class="section-header variant-header"
        @click="showVariantData = !showVariantData"
        role="button"
        tabindex="0"
      >
        VARIANT STATISTICS
        <div class="toggle-indicator">{{ showVariantData ? "▲" : "▼" }}</div>
      </div>
      <transition name="slide-fade">
        <div v-show="showVariantData" class="section-content">
          <div class="row pie-and-book">
        <div style="width: 320px; height: 320px;">
          <PieChart
            :data="originalVsVariantData"
            :options="pieOptions"
            :style="{ width: '320px', height: '320px' }"
          />
        </div>


        <div class="top-variant-book-container">
          <h3>Book with Most Variant Covers</h3>
          <p><strong>{{ topVariantBook.title || "N/A" }}</strong></p>
          <p>Variant Covers: {{ topVariantBook.variantCount || 0 }}</p>
          <img
            v-if="topVariantBook.coverUrl"
            :src="topVariantBook.coverUrl"
            alt="Cover Image"
            class="cover-image"
          />
          <p v-else>No cover image available</p>
        </div>
       </div>

      <div class="chart-container">
        <BarChart
          :data="booksWithMostVariantsData"
          :options="barOptionsBooksVariants"
          :style="{ width: '100%', height: '320px' }"
        />
      </div>
        </div>
        
      </transition>

      <div
        class="section-header other-header"
        @click="showOtherData = !showOtherData"
        role="button"
        tabindex="0"
      > 
        OTHER STATISTICS 
        <div class="toggle-indicator">{{ showOtherData ? "▲" : "▼" }}</div>
      </div>
      <transition name="slide-fade">
        <div v-show="showOtherData" class="section-content">
           <div class="chart-container">
          <BarChart
            :data="seriesLongestRunningData"
            :options="barOptionsLongestSeries"
            :style="{ width: '100%', height: '320px' }"
          />
        </div>
        </div>
       
      </transition>
  
    </div>
  </div>
</template>

<script>

import axios from "axios";
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
import CreatorStats from "@/components/stats/CreatorStats.vue";

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
import { useIssuesStore } from '../store/issuesStore'

export default {
  name: "DatasetStats",
  components: {
    LineChart: Line,
    BarChart: Bar,
    PieChart: Pie,
    CreatorStats
  },
  data() {
    return {
      minYear: null,
      maxYear: null,
      showGeneralData: true,
      showVariantData: true,
      showOtherData: true,
      lineChartData: { labels: [], datasets: [] },
      barChartData: { labels: [], datasets: [] },
      originalVsVariantData: { labels: [], datasets: [] },
      booksWithMostVariantsData: { labels: [], datasets: [] },
      issuesPerPublisherData: { labels: [], datasets: [] },
      seriesLongestRunningData: { labels: [], datasets: [] },
      topVariantBook: {
      title: '',
      variantCount: 0,
      coverUrl: ''
      },
      pieOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top" },
          title: { display: true, text: "Original vs Variant Issues" },
        },
      },
      barOptionsBooksVariants: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          title: { display: true, text: "Other Books with Most Variant Covers" },
        },
      },
      barOptionsLongestSeries: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          title: { display: true, text: "Longest Running Series (years)" },
        },
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
    loading() {
      return this.issuesStore.loading;
    },
    error() {
      return this.issuesStore.error;
    },
    issues() {
      return this.issuesStore.issues;
    }
  },
  created() {
    this.issuesStore = useIssuesStore();
    this.issuesStore.fetchIssues().then(() => {
      this.prepareCharts();
    });
  },
  methods: {
    async fetchIssues() {
      this.loading = true;
      this.error = null;
      try {
        const res = await axios.get("http://127.0.0.1:8000/issues/", {
          params: { dataset: "all", limit: 50000 }
        });
        this.issuesStore.issues = res.data || [];
        this.prepareCharts();
      } catch (e) {
        console.error(e);
        this.error = "Failed to fetch issues.";
      } finally {
        this.loading = false;
      }
    },

    prepareCharts() {
      this.prepareSeriesPerYearChart();
      this.prepareOriginalVsVariantChart();
      this.prepareBooksWithMostVariantsChart();
      this.prepareLongestRunningSeriesChart();
      this.prepareSeriesLengthDistributionPieChart();
      this.prepareTopSeriesByIssuesChart();
      this.prepareReleaseDateHeatmap();
      this.$nextTick(() => {
          this.renderHeatmap();
        });
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

      this.issuesStore.issues.forEach(issue => {
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

      // Second pass: count issues per decade/month
      this.issuesStore.issues.forEach(issue => {
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

            // Interpolate blue to red colors as before
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
            reverse: true,  // optional: newest decade on top
          },
        },
        plugins: {
          legend: { display: false },
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

      console.log("Heatmap year range:", minDecade, maxDecade, "data points:", data.length);
    },

    prepareTopSeriesByIssuesChart() {
      const seriesIssueCounts = new Map();

      this.issuesStore.issues.forEach(issue => {
        if (!issue.series_title) return;
        seriesIssueCounts.set(issue.series_title, (seriesIssueCounts.get(issue.series_title) || 0) + 1);
      });

      const sorted = Array.from(seriesIssueCounts.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

      this.topSeriesByIssuesData = {
        labels: sorted.map(([title]) => title),
        datasets: [
          {
            label: "Number of Issues",
            data: sorted.map(([, count]) => count),
            backgroundColor: "#2c7be5",
          },
        ],
      };
    },

    prepareSeriesPerYearChart() {
      const seriesYearsCount = new Map();

      this.issuesStore.issues.forEach((issue) => {
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

    this.issuesStore.issues.forEach(issue => {
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

    prepareOriginalVsVariantChart() {
      let originalCount = 0;
      let variantCount = 0;

      this.issuesStore.issues.forEach((issue) => {
        if (issue.is_variant) variantCount++;
        else originalCount++;
      });

      this.originalVsVariantData = {
        labels: ["Original Issues", "Variant Issues"],
        datasets: [
          {
            data: [originalCount, variantCount],
            backgroundColor: ["#2c7be5", "#ff7b9c"],
          },
        ],
      };
    },

    prepareBooksWithMostVariantsChart() {
      const variantCounts = new Map();

      this.issuesStore.issues.forEach((issue) => {
        if (issue.is_variant && issue.original_issue_id) {
          variantCounts.set(issue.original_issue_id, (variantCounts.get(issue.original_issue_id) || 0) + 1);
        }
      });

      const topVariants = Array.from(variantCounts.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 20);

      const issueIdToTitle = new Map(this.issuesStore.issues.map((issue) => [issue.issue_id, issue.title]));

      const labels = topVariants.map(([origId]) => issueIdToTitle.get(origId) || origId);
      const data = topVariants.map(([, count]) => count);

      this.booksWithMostVariantsData = {
        labels,
        datasets: [
          {
            label: "Variant covers",
            data,
            backgroundColor: "#9b7bff",
          },
        ],
      };

    if (topVariants.length) {
      const topOrigId = topVariants[0][0];
      const topCount = topVariants[0][1];

      const origIssue = this.issuesStore.issues.find(issue => issue.issue_id === topOrigId);

      this.topVariantBook.title = origIssue ? origIssue.title : 'N/A';
      this.topVariantBook.variantCount = topCount;
      this.topVariantBook.coverUrl = origIssue ? origIssue.image_url : '';
    } else {
      this.topVariantBook = { title: '', variantCount: 0, coverUrl: '' };
    }
    },

    prepareLongestRunningSeriesChart() {
      const currentYear = new Date().getFullYear();

      const seriesMap = new Map();

      this.issuesStore.issues.forEach((issue) => {
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
.app-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  padding: 1rem 0;
  user-select: none;
}

.app-header h1 {
  font-family: "Poppins", "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  font-weight: 900;
  font-size: 4rem;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  margin: 0;
  padding: 1rem 2rem;
  
  background-image: url('https://i.ebayimg.com/images/g/pbUAAOSwynZjoqIx/s-l1200.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  
  color: white;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.7);
  cursor: default;
}

.btn-series, .btn-new {
  font-family: "Roboto Condensed", "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  font-weight: 100;
  font-size: 1rem;
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  background-color: #2c7be5;
  color: white;
  transition: background-color 0.3s ease, transform 0.2s ease;
}
.btn-series:hover, .btn-new:hover {
  background-color: #1a4f9c;
  transform: translateY(-2px);
}

.dataset-stats > h2 {
  font-family: "Poppins", "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  font-weight: 900;
  font-size: 3rem;
  text-transform: uppercase;
  text-align: center;
  letter-spacing: 0.15em;
  margin-bottom: 2rem;
  user-select: none;
  cursor: default;
  color: rgb(214, 165, 237);             
  padding: 1rem 0;
  position: relative;
}

.section-header {
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
  transition: background-color 0.3s ease;
}
.section-header:hover {
  background-color: rgba(0,0,0,0.05);
}
.section-header.active {
  background-color: rgba(44,123,229,0.08);
  border-left: 4px solid currentColor;
}

.general-header { color: #2c7be5; }
.variant-header { color: #9b7bff; }
.other-header { color: chocolate; }

.toggle-indicator {
  font-size: 1.2rem;
  margin-top: 0.3rem;
  user-select: none;
  display: inline-block;
  transition: transform 0.3s ease;
}
.section-header.active .toggle-indicator {
  transform: rotate(180deg);
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

.row.pie-and-book {
  display: flex;
  align-items: stretch;    
  justify-content: center;  
  gap: 24px;
  margin-bottom: 30px;
  flex-wrap: wrap;
  width: 100%;
}

.pie-container {
  flex-shrink: 0;
  background: radial-gradient(circle at 30% 30%, #fff, #f7f7f7);
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.top-variant-book-container {
  max-width: 320px;
  text-align: left;
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.top-variant-book-container h3 {
  margin-bottom: 0.5rem;
}
.top-variant-book-container p {
  margin: 0.25rem 0;
}

.cover-image {
  max-width: 180px;
  max-height: 240px;
  object-fit: contain;
  border-radius: 8px;
  margin-top: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
  transition: transform 0.2s ease;
}
.cover-image:hover {
  transform: scale(1.05);
}

.dataset-stats {
  max-width: 1500px;
  margin: 1.5rem auto;
  padding: 0 12px;
  text-align: center;
}

.chart-container {
  height: 360px;
  margin: 30px auto;
  padding: 20px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  position: relative;
}
.chart-container > div {
  width: 100% !important;
  height: 320px !important;
}
.chart-container canvas {
  width: 100% !important;
  height: 320px !important;
  box-sizing: border-box;
  display: block;
}

.error {
  color: red;
  margin: 1rem;
}
</style>

