<template>
  <div id="app">
    <keep-alive>
      <router-view />
    </keep-alive>
  </div>
</template>


<script>
import axios from "axios";

export default {
  data() {
    return {
      mode: "series",
      seriesQuery: "",
      seriesList: [],

      filters: {
        year: null,
        dataset: "original", 
      },
      selectedSeriesTitle: null,
      issues: [],
      selectedIssue: null,
      variants: [],
      original: null,

      loading: false,
      error: null,

      currentPage: 1,
      pageSize: 12,
    };
  },
  computed: {
    totalPages() {
      return Math.ceil(this.issues.length / this.pageSize) || 1;
    },
    pagedIssues() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.issues.slice(start, start + this.pageSize);
    },
  },
  methods: {
    // 1) Search series: fetch issues by series_title, keep only originals to avoid duplicates,
    //    then group by series_title to build a "series" list.
    async searchSeries() {
      this.loading = true;
      this.error = null;
      this.seriesList = [];
      this.mode = "series";
      this.selectedSeriesTitle = null;
      this.issues = [];
      this.selectedIssue = null;

      try {
        const params = {};
        if (this.seriesQuery) params.series_title = this.seriesQuery;
        // Keep only originals so a series doesn’t double-count via variants
        params.dataset = "original";

        const res = await axios.get("http://127.0.0.1:8000/issues/", { params });
        const issues = res.data || [];

        // Group by series_title
        const map = new Map();
        for (const it of issues) {
          const key = it.series_title || "Unknown Series";
          if (!map.has(key)) {
            map.set(key, []);
          }
          map.get(key).push(it);
        }

        // Build series list with a thumbnail, count, and year range
        this.seriesList = Array.from(map.entries()).map(([title, list]) => {
          const thumb = list.find(x => !!x.image_url)?.image_url || "";
          const years = this.computeYearRange(list.map(x => x.release_date));
          return {
            title,
            thumb,
            count: list.length,
            years,
          };
        });
      } catch (e) {
        this.error = "Failed to fetch series.";
      } finally {
        this.loading = false;
      }
    },

    computeYearRange(dateStrs) {
      const years = dateStrs
        .map(d => (d ? new Date(d).getFullYear() : null))
        .filter(Boolean);
      if (!years.length) return "";
      const min = Math.min(...years);
      const max = Math.max(...years);
      return min === max ? `${min}` : `${min}–${max}`;
    },

    // 2) Enter a series and load issues
    async openSeries(s) {
      this.selectedSeriesTitle = s.title;
      this.mode = "issues";
      this.currentPage = 1;
      await this.loadSeriesIssues();
    },

    // 3) Load issues for the selected series using filters
    async loadSeriesIssues() {
      if (!this.selectedSeriesTitle) return;
      this.loading = true;
      this.error = null;
      this.selectedIssue = null;
      this.variants = [];
      this.original = null;

      try {
        const params = {
          series_title: this.selectedSeriesTitle,
        };
        if (this.filters.year) params.year = this.filters.year;

        // dataset filter:
        // - "all": do not send dataset param
        // - otherwise: send dataset=original/variant
        if (this.filters.dataset !== "all") {
          params.dataset = this.filters.dataset;
        }

        const res = await axios.get("http://127.0.0.1:8000/issues/", { params });
        // Optional: sort by issue_number ascending
        const sorted = (res.data || []).slice().sort((a, b) => {
          const na = Number(a.issue_number);
          const nb = Number(b.issue_number);
          if (!isNaN(na) && !isNaN(nb)) return na - nb;
          return String(a.issue_number).localeCompare(String(b.issue_number));
        });
        this.issues = sorted;
      } catch (e) {
        this.error = "Failed to fetch issues.";
      } finally {
        this.loading = false;
      }
    },

    formatDate(dateStr) {
      if (!dateStr) return "Unknown";
      return new Date(dateStr).toLocaleDateString();
    },

    async selectIssue(issue) {
      this.selectedIssue = issue;

      if (issue.dataset === "original") {
        try {
          const res = await axios.get(`http://127.0.0.1:8000/issues/${issue.issue_id}/variants`);
          this.variants = res.data || [];
        } catch {
          this.variants = [];
        }
        this.original = null;
      } else if (issue.dataset === "variant") {
        try {
          const res = await axios.get(`http://127.0.0.1:8000/issues/${issue.issue_id}/original`);
          this.original = res.data || null;
        } catch {
          this.original = null;
        }
        this.variants = [];
      }
    },

    backToSeries() {
      this.mode = "series";
      this.selectedSeriesTitle = null;
      this.issues = [];
      this.selectedIssue = null;
      this.variants = [];
      this.original = null;
      this.error = null;
      this.currentPage = 1;
    },

    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
      }
    },
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
      }
    },
  },
  // Optional: auto-load a popular query on mount for demo
  mounted() {
    // this.seriesQuery = "Astonishing X-Men";
    // this.searchSeries();
  },
};
</script>

