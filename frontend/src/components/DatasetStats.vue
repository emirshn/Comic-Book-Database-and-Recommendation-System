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
      <GeneralStats :issues="issuesStore.issues" />
      <CreatorStats :issues="issuesStore.issues" />
            <VariantStats :issues="issuesStore.issues"/>

    </div>
  </div>
</template>

<script>

import api from "../axios";
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
        const res = await api.get("/issues/", {
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

.dataset-stats {
  max-width: 1500px;
  margin: 1.5rem auto;
  padding: 0 12px;
  text-align: center;
}

.error {
  color: red;
  margin: 1rem;
}
</style>

