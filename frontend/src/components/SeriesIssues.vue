<template>
  <div class="app series-page">

    <div class="series-header">
      <router-link to="/series" class="back">← Back to Series</router-link>
    <div
      v-if="issues.length && issues[0].image_url"
      class="fullscreen-cover-bg"
      :style="{ backgroundImage: `url(${issues[0].image_url})` }"
    ></div>

    <div class="title-stack">
      <h2>{{ issues.length ? issues[0].series_title : `Series ID: ${seriesId}` }}</h2>
      <p class="subtitle">Browse issues, filter and toggle variants.</p>
    </div>
  </div>


    <form @submit.prevent="searchIssues" class="search-form">
      <div class="filters-row main-search-row">
        <label class="search-title-label">
          <span class="label-text">Issue Title:</span>
          <input v-model="issueQuery" placeholder="e.g. Spider-Man #1" />
        </label>

        <button type="submit" :disabled="loading" class="search-btn">
          {{ loading ? "Searching..." : "Search" }}
        </button>

        <button
          type="button"
          @click="showAdvancedFilters = !showAdvancedFilters"
          class="toggle-advanced-btn"
        >
          {{ showAdvancedFilters ? "Hide Advanced Filters" : "Show Advanced Filters" }}
        </button>
      </div>

      <transition name="fade-slide">
        <div v-if="showAdvancedFilters" class="filters-row advanced-filters">
          <!-- <label>
            Year:
            <input type="number" v-model.number="filterYear" min="1900" />
          </label> -->

          <label>
            Sort By:
            <select v-model="sortBy">
              <option value="issue_number">Issue #</option>
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="title">Title (A–Z)</option>
            </select>
          </label>

          <label class="checkbox-label">
            <input type="checkbox" v-model="includeVariants" />
            Include Variants
          </label>

          <label class="checkbox-label">
            <input type="checkbox" v-model="filterMarvelUnlimited" />
            Marvel Unlimited
          </label>

          
        </div>
      </transition>
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
        @click="goToIssue(issue)"
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
            <div v-if="!issue.is_variant && hasVariants(issue)" class="chip variant-available">
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
          v-if="page !== '...' "
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
import api from "../axios";

export default {
  props: ["seriesId"],
  data() {
    return {
      filters: {
        year: null,
        dataset: "all",  
      },
      issues: [],
      allIssues: [],
      selectedIssue: null,
      variants: [],
      original: null,
      loading: false,
      error: null,
      currentPage: 1,
      pageSize: 20,

      issueQuery: "",
      showAdvancedFilters: false,
      filterYear: null,
      includeVariants: false,
      filterMarvelUnlimited: false,
      sortBy: 'issue_number',
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
    },
  },
  watch: {
    seriesId: {
      immediate: true,
      handler() {
        this.loadSeriesIssues();
      },
    },
    includeVariants() {
      this.filterIssuesByVariantCheckbox();
    },
    filterYear() {
      this.searchIssues();
    },
    filterMarvelUnlimited() {
      this.searchIssues();
    },
    sortBy() {
      this.sortIssues();
    }
  },
  methods: {
    sortIssues() {
      switch (this.sortBy) {
        case 'issue_number':
          this.issues.sort((a, b) => {
            const na = Number(a.issue_number);
            const nb = Number(b.issue_number);
            if (!isNaN(na) && !isNaN(nb)) return na - nb;
            return String(a.issue_number).localeCompare(String(b.issue_number));
          });
          break;
        case 'newest':
          this.issues.sort((a, b) => {
            const aDate = new Date(a.release_date || 0);
            const bDate = new Date(b.release_date || 0);
            return bDate - aDate;
          });
          break;
        case 'oldest':
          this.issues.sort((a, b) => {
            const aDate = new Date(a.release_date || 0);
            const bDate = new Date(b.release_date || 0);
            return aDate - bDate;
          });
          break;
        case 'title':
          this.issues.sort((a, b) => (a.title || "").localeCompare(b.title || ""));
          break;
      }
    },
    goToIssue(issue) {
      if (!issue) return;

      if (issue.is_variant && issue.original_issue_id) {
        this.$router.push({
          name: "IssueDetail",
          params: {
            originalIssueId: issue.original_issue_id,
            variantIssueId: issue.issue_id,
          },
        });
      } else {
        this.$router.push({
          name: "IssueDetail",
          params: {
            originalIssueId: issue.issue_id,
          },
        });
      }
    },
    async loadSeriesIssues() {
      if (!this.seriesId) return;
      this.loading = true;
      this.error = null;
      this.selectedIssue = null;
      this.variants = [];
      this.original = null;

      try {
        const params = { series_id: Number(this.seriesId), dataset: "all" };
        if (this.filterYear) params.year = this.filterYear;
        if (this.filterMarvelUnlimited) params.marvel_unlimited = true;
        if (this.issueQuery) params.title = this.issueQuery;

        const res = await api.get("/issues/", { params });
        let issues = res.data || [];
        
        issues.sort((a, b) => {
          const na = Number(a.issue_number);
          const nb = Number(b.issue_number);
          if (!isNaN(na) && !isNaN(nb)) return na - nb;
          return String(a.issue_number).localeCompare(String(b.issue_number));
        });

        this.allIssues = issues;
        this.filterIssuesByVariantCheckbox();
        this.currentPage = 1;
      } catch (e) {
        console.error(e);
        this.error = "Failed to fetch issues.";
      } finally {
        this.loading = false;
      }
    },
    async searchIssues() {
      await this.loadSeriesIssues();
    },
    filterIssuesByVariantCheckbox() {
      if (this.includeVariants) {
        this.issues = this.allIssues;
      } else {
        this.issues = this.allIssues.filter(issue => !issue.is_variant);
      }
    },
    formatDate(dateStr) {
      if (!dateStr) return "Unknown";
      return new Date(dateStr).toLocaleDateString();
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
    hasVariants(issue) {
      let variants = issue.variant_covers;

      if (typeof variants === 'string') {
        try {
          variants = JSON.parse(variants);
        } catch (e) {
          console.warn('Failed to parse variant_covers for issue', issue.issue_id, e);
          variants = [];
        }
      }

      return Array.isArray(variants) && variants.length > 0;
    }

  },
};
</script>

<style scoped>
.app {
  font-family: "Roboto Condensed", "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}
.app button,
.app select,
.app textarea {
  font-family: "Roboto Condensed", "Segoe UI", Tahoma, Geneva, Verdana, sans-serif !important;
}
.back-wrapper {
  max-width: 980px;
  margin: 20px auto 8px auto;
  padding: 0 20px;
}

.series-header {
  position: relative;
  max-width: 1980px;  
  margin: 0 auto 2rem auto;
  padding: 40px 20px;
  border-radius: 8px;
  color: white;
  overflow: hidden;
  background-color: transparent;

  display: flex;
  justify-content: center; 
  align-items: center;     
  min-height: 160px;       
}

.back {
  position: absolute;
  top: 20px;
  left: 20px;
  padding: 8px 16px;
  font-size: 1rem;
  border-radius: 8px;
  background-color: #007acc;
  color: white;
  text-decoration: none;
  cursor: pointer;
  user-select: none;
  box-shadow: 0 2px 6px rgba(0, 122, 204, 0.8);
  transition: background-color 0.2s ease;
  z-index: 10;  /* above background */
  white-space: nowrap;
}

.back:hover {
  background-color: #005fa3;
}

.title-stack {
  position: relative;
  z-index: 10;
  min-width: 250px;
  text-align: center;
}

.fullscreen-cover-bg {
  position: absolute; 
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover; /* this makes the image cover whole area */
  filter: blur(10px);
  opacity: 0.3;
  z-index: 1;
  pointer-events: none;
  border-radius: 8px; 
}


.cover-bg-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.15);  z-index: 1;
  pointer-events: none;
    background: transparent !important;

}

.title-stack {
  flex-grow: 1; 
  text-align: center;
  position: relative;
  z-index: 10;
  min-width: 250px;
}

.title-stack h2 {
  margin: 0 0 8px 0;
  font-weight: 800;
  font-family: "Roboto Condensed", sans-serif;
  font-size: 3rem;
  line-height: 1.1;
  text-transform: uppercase;
  color: rgb(44, 42, 42); 
}

.title-stack .subtitle {
  margin: 0;
  font-weight: 600;
  font-size: 1.1rem;
  color: #3c3636;
}


.search-form {
  background: #fff;
  padding: 15px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgb(0 0 0 / 0.1);
  max-width: 980px;
  margin: 0 auto 2rem auto;
  font-weight: 600;
}

.filters-row.main-search-row {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 12px;
  justify-content: center;
  margin-bottom: 1rem;
}

.filters-row.advanced-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: center;
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid #ddd;
  width: 100%;
  box-sizing: border-box;
}

.search-title-label {
  position: relative;
  width: 220px;
  margin: 0;
  user-select: none;
  display: flex;
  flex-direction: column;
}

.search-title-label .label-text {
  position: absolute;
  top: -18px;
  left: 0;
  font-weight: 600;
  font-size: 0.85rem;
  color: #444;
  user-select: none;
}

.search-title-label input {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #ccc;
  font-size: 0.9rem;
  width: 100%;
  box-sizing: border-box;
  height: 36px;
}

.search-btn,
.toggle-advanced-btn {
  padding: 8px 16px;
  font-weight: 600;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  background-color: #007acc;
  color: white;
  transition: background-color 0.3s ease;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-btn:disabled {
  background-color: #7abaff;
  cursor: not-allowed;
}

.search-btn:hover:not(:disabled),
.toggle-advanced-btn:hover {
  background-color: #005fa3;
}

.search-form label {
  display: flex;
  flex-direction: column;
  min-width: 180px;
  font-weight: 600;
  color: #444;
}

.search-form input[type="text"],
.search-form input[type="number"],
.search-form select {
  margin-top: 6px;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #ccc;
  font-size: 1rem;
  width: 100%;
  max-width: 350px;
  box-sizing: border-box;
  font-family: inherit;
}

.search-form input[type="checkbox"] {
  margin-right: 6px;
  align-self: center;
}

.search-form label input[type="checkbox"] {
  width: auto;
  margin-top: 0;
}
.checkbox-label {
  flex-direction: row !important;
  align-items: center;
  min-width: auto;
}

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
.loading,
.error,
.no-results {
  text-align: center;
  margin: 1rem 0;
  font-weight: 600;
  width: 100%;
  max-width: 980px;
  margin-left: auto;
  margin-right: auto;
}
</style>
