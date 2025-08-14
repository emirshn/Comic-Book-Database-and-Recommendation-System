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
      <VariantStats :issues="issuesStore.issues"/>
      <GeneralStats :issues="issuesStore.issues" />
      <CreatorStats :issues="issuesStore.issues" />
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
import GeneralStats from "./stats/GeneralStats.vue";
import VariantStats from "./stats/VariantStats.vue";
export default {
  name: "DatasetStats",
  components: {
    CreatorStats,
    GeneralStats,
    VariantStats
  },
  data() {
    return {
      showCreatorStats: false,
      showGeneralStats: false,
      showVariantData: false,
      
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

