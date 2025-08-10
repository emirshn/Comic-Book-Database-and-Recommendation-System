<template>
  <div class="app series-page">
    <div class="series-header">
      <router-link to="/series" class="back">← Back to Series</router-link>
      <div class="title-stack">
        <h2>{{ issues.length ? issues[0].series_title : `Series ID: ${seriesId}` }}</h2>
        <p class="subtitle">Browse issues, filter by year, and toggle variants.</p>
      </div>
    </div>

    <form @submit.prevent="loadSeriesIssues" class="filter-bar">
      <label>
        Year:
        <input type="number" v-model.number="filters.year" placeholder="e.g. 2013" />
      </label>

      <label>
        Dataset:
        <select v-model="filters.dataset">
          <option value="original">Original</option>
          <option value="variant">Variant</option>
          <option value="all">All</option>
        </select>
      </label>

      <button type="submit" :disabled="loading">
        {{ loading ? "Filtering..." : "Apply" }}
      </button>
    </form>

    <div v-if="loading" class="loading">Loading issues...</div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!loading && !issues.length && !error" class="no-results">
      No issues found for this series.
    </div>

    <div v-if="issues.length" class="issues-grid">
      <div
        class="issue-card"
        v-for="issue in pagedIssues"
        :key="issue.issue_id"
        @click="$router.push({ path: `/issue/${issue.issue_id}` })"
        :class="{ selected: selectedIssue && selectedIssue.issue_id === issue.issue_id }"
      >
        <img :src="issue.image_url" alt="Cover" />
        <div class="issue-meta">
          <div class="title-row">
            <strong>{{ issue.title || ("Issue #" + issue.issue_number) }}</strong>
            <img
              v-if="issue.marvel_unlimited"
              src="/mu_logo.png"
              alt="Marvel Unlimited"
              class="mu-logo"
              title="Available in Marvel Unlimited"
            />
          </div>
          <div class="small">{{ issue.creators_shortlist || "Unknown creators" }}</div>
          <div class="small">{{ formatDate(issue.release_date) }}</div>
          <div class="chips-row">
            <div class="chip" :class="issue.is_variant ? 'variant' : 'original'">
              {{ issue.is_variant ? "Variant" : "Original" }}
            </div>
            <div v-if="!issue.is_variant && issue.has_variants" class="chip variant-available">
              Variant Available
            </div>
          </div>

        </div>
      </div>
    </div>

    <div v-if="issues.length > pageSize" class="pagination">
      <button @click="prevPage" :disabled="currentPage === 1">&lt; Prev</button>

      <span v-for="page in pageNumbers" :key="page">
        <button
          v-if="page !== '...'"
          @click="goToPage(page)"
          :class="{ active: currentPage === page }"
        >
          {{ page }}
        </button>
        <span v-else class="dots">...</span>
      </span>

      <button @click="nextPage" :disabled="currentPage === totalPages">Next &gt;</button>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  props: ["seriesId"],
  data() {
    return {
      filters: {
        year: null,
        dataset: "original",
      },
      issues: [],
      selectedIssue: null,
      variants: [],
      original: null,
      loading: false,
      error: null,
      currentPage: 1,
      pageSize: 20,
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
    pageNumbers() {
    const total = this.totalPages;
    const current = this.currentPage;
    const delta = 2;
    let range = [];
    let rangeWithDots = [];
    let l;

    for (let i = 1; i <= total; i++) {
      if (i === 1 || i === total || (i >= current - delta && i <= current + delta)) {
        range.push(i);
      }
    }

    for (let i of range) {
      if (l) {
        if (i - l === 2) {
          rangeWithDots.push(l + 1);
        } else if (i - l > 2) {
          rangeWithDots.push("...");
        }
      }
      rangeWithDots.push(i);
      l = i;
    }

    return rangeWithDots;
  }
  },
  watch: {
    seriesId: {
      immediate: true,
      handler() {
        this.loadSeriesIssues();
      },
    },
  },
  methods: {
    async loadSeriesIssues() {
  if (!this.seriesId) return;
  this.loading = true;
  this.error = null;
  this.selectedIssue = null;
  this.variants = [];
  this.original = null;

  try {
    const params = { series_id: Number(this.seriesId) };
    if (this.filters.year) params.year = this.filters.year;
    params.dataset = this.filters.dataset; // can be "original", "variant", or "all"

    const res = await axios.get("http://127.0.0.1:8000/issues/", { params });
    let issues = res.data || [];

    // If dataset === "original", add has_variants flags by fetching variants count for each original issue
    if (this.filters.dataset === "original" || this.filters.dataset === "all") {
      // Build a map original_issue_id -> variant count for has_variants flag
      const originalIds = issues
        .filter(issue => !issue.is_variant)
        .map(issue => issue.issue_id);

      if (originalIds.length) {
        // Fetch variants for all originals in one go (optional optimization)
        // Or do variant fetching on demand per issue to keep simple
        // Here, let's just mark has_variants false for simplicity
        issues = issues.map(issue => ({
          ...issue,
          has_variants: false // or true if you want to implement checking here
        }));
      }
    }

    // Sort by issue_number
    issues.sort((a, b) => {
      const na = Number(a.issue_number);
      const nb = Number(b.issue_number);
      if (!isNaN(na) && !isNaN(nb)) return na - nb;
      return String(a.issue_number).localeCompare(String(b.issue_number));
    });

    this.issues = issues;
    this.currentPage = 1;
  } catch (e) {
    console.error(e);
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
    goToPage(page) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
    }
  },
  },
};
</script>

<style scoped>
.app {
  max-width: auto;
  margin: 20px auto;
  padding: 20px;
  font-family: "Roboto Condensed", "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  color: #333;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
}

h1,
h2 {
  font-family: "Roboto Condensed", sans-serif;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 1.5rem;
}

.search-form,
.filter-bar {
  font-family: "Roboto Condensed", sans-serif;
  font-weight: 600;
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 1.2rem;
  justify-content: center;
}

.search-form label,
.filter-bar label {
  font-family: "Roboto Condensed", sans-serif;
  font-weight: 600;
  display: flex;
  flex-direction: column;
  color: #555;
  min-width: 180px;
}

.search-form input,
.filter-bar input,
.filter-bar select {
  margin-top: 6px;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #ccc;
  font-family: "Roboto Condensed", sans-serif;
  font-weight: 400;
  font-size: 1rem;
}

button[type="submit"],
.back {
  font-family: "Roboto Condensed", sans-serif;
  font-weight: 400;
  padding: 8px 16px;
  font-size: 1rem;
  border-radius: 8px;
  border: none;
  background-color: #007acc;
  color: white;
  cursor: pointer;
}

button[type="submit"]:disabled {
  background-color: #7abaff;
  cursor: not-allowed;
}

.loading,
.error,
.no-results {
  font-family: "Roboto Condensed", sans-serif;
  font-weight: 600;
  text-align: center;
  margin: 1rem 0;
}

.error {
  color: #d9534f;
}

.series-header {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.back {
  align-self: flex-start;
  margin-bottom: 0.5rem;  
}
.chips-row {
  display: flex;
  gap: 6px; 
  flex-wrap: wrap; 
}

/* Issues grid */
.issues-grid {
  display: grid;
  grid-template-columns: repeat(5, 237px);
  gap: 16px;
  justify-content: center;
}

.issue-card {
  width: 250px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  background: none; 
  border: none;
  box-shadow: none;
  transition: transform 0.1s ease, box-shadow 0.2s ease;
}

.issue-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgb(0 0 0 / 0.15);
}

.issue-card img {
  width: 237px;
  height: 355px;
  object-fit: cover;
  display: block;
  background: none; 
}

.issue-meta {
  padding: 8px 0;
  text-align: left;
  width: 100%;
  background: transparent;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding-left: 8px; 
  padding-right: 8px;
  width: calc(100% - 16px); 
}

.issue-meta strong {
  font-family: "Roboto Condensed", sans-serif;
  font-weight: 600;
  font-size: 1.05rem;
  margin: 0;
}

.issue-meta .small {
  font-family: "Roboto Condensed", sans-serif;
  font-weight: 400;
  color: #666;
  font-size: 0.95rem;
  margin: 0;
}

/* Title row with Marvel Unlimited logo */
.title-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mu-logo {
  height: 32px !important;
  width: auto !important;
  vertical-align: middle;
  user-select: none;
  margin: 0;
  padding: 0;
  display: inline-block;
}

.chip {
  display: inline-block;
  font-family: "Roboto Condensed", sans-serif;
  font-weight: 400;
  font-size: 0.8rem;
  padding: 2px 8px;
  border-radius: 999px;
  width: max-content;
}

.chip.original {
  background: #e6f4ff;
  color: #005a9e;
}

.chip.variant {
  background: #fff2e6;
  color: #b05a00;
}

.chip.variant-available {
  background: #f2dfdf;
  color: #d04bd7;
  margin-left: 6px;
}

.pagination {
  margin: 15px 0;
  display: flex;
  justify-content: center;
  gap: 15px;
  align-items: center;
}

.pagination button {
  font-family: "Roboto Condensed", sans-serif;
  font-weight: 400;
  padding: 6px 14px;
  font-size: 1rem;
  border-radius: 6px;
  border: 1px solid #007acc;
  background-color: white;
  color: #007acc;
  cursor: pointer;
}
.pagination button.active {
  background-color: #007acc;
  color: white;
  border-color: #007acc;
}
.pagination .dots {
  padding: 6px 10px;
  color: #666;
}

.pagination button:disabled {
  border-color: #ccc;
  color: #ccc;
  cursor: not-allowed;
}
</style>
