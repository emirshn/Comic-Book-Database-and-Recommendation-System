<template>
<div class="creator-topology-stats">
    <div
    class="section-header creator-header"
    @click="showGeneralData = !showGeneralData"
    role="button"
    tabindex="0"
    >
    VARIANT STATISTICS
    <div class="toggle-indicator">{{ showGeneralData ? "▲" : "▼" }}</div>
</div>

<transition name="slide-fade">
    <div v-show="showGeneralData" class="section-content">
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
import { Bar, Pie } from "vue-chartjs";
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
        PieChart: Pie
    },
    data() {
    return {
        showGeneralData: true,
        originalVsVariantData: { labels: [], datasets: [] },
        booksWithMostVariantsData: { labels: [], datasets: [] },
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
            this.prepareOriginalVsVariantChart();
            this.prepareBooksWithMostVariantsChart();
        },

        prepareOriginalVsVariantChart() {
            let originalCount = 0;
            let variantCount = 0;

            this.issues.forEach((issue) => {
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

            this.issues.forEach((issue) => {
                if (issue.is_variant && issue.original_issue_id) {
                variantCounts.set(issue.original_issue_id, (variantCounts.get(issue.original_issue_id) || 0) + 1);
                }
            });

            const topVariants = Array.from(variantCounts.entries())
                .sort((a, b) => b[1] - a[1])
                .slice(0, 20);

            const issueIdToTitle = new Map(this.issues.map((issue) => [issue.issue_id, issue.title]));

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

            const origIssue = this.issues.find(issue => issue.issue_id === topOrigId);

            this.topVariantBook.title = origIssue ? origIssue.title : 'N/A';
            this.topVariantBook.variantCount = topCount;
            this.topVariantBook.coverUrl = origIssue ? origIssue.image_url : '';
            } else {
            this.topVariantBook = { title: '', variantCount: 0, coverUrl: '' };
            }
            },
    },
};
</script>

<style scoped>
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
  min-width: 500px;
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
