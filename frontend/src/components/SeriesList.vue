<template>
  <div class="app">
      <router-link to="/" class="back">← Back to Series</router-link>
    <header class="app-header">
      <h1>Comic Book Database</h1>
    </header>

    <!-- Search + Filter Bar -->
    <form @submit.prevent="applyFilters" class="search-form">
      <div class="filters-row main-search-row">
        <label class="search-title-label">
          <span class="label-text">Series Title:</span>
          <input v-model="seriesQuery" placeholder="e.g. Astonishing X-Men" />
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
          <label>
            Start Year:
            <input type="number" v-model.number="filterStartYear" min="1900" />
          </label>

          <label>
            End Year:
            <input type="number" v-model.number="filterEndYear" max="2099" />
          </label>

          <label>
            Min Issues:
            <input type="number" v-model.number="filterMinIssues" min="1" />
          </label>

          <label>
            Sort By:
            <select v-model="sortBy">
              <option value="title">Title (A–Z)</option>
              <option value="count">Issue Count</option>
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
            </select>
          </label>

          <label class="checkbox-label">
              <input type="checkbox" v-model="filterUnlimited" />
              Marvel Unlimited
          </label>


          <label class="checkbox-label">
            <input type="checkbox" v-model="filterOneShot" />
            Hide One-Shots
          </label>

          <label class="checkbox-label">
            <input type="checkbox" v-model="filterComicFormats" />
            Comics Only (Exclude Hardcover, TPB, etc.)
          </label>
        </div>
      </transition>
    </form>

    <!-- Status messages -->
    <div v-if="loading" class="loading">Loading series...</div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!loading && !seriesList.length && !error" class="no-results">
      No series found.
    </div>

    <!-- Series Grid -->
    <div v-if="filteredSeries.length" class="series-grid">
      <router-link
        v-for="s in pagedSeries"
        :key="s.series_id"
        :to="{ name: 'Series', params: { seriesId: s.series_id } }"
        custom
      >
        <template #default="{ navigate, isExactActive }">
          <div
            class="series-card"
            @click="navigate"
            role="link"
            tabindex="0"
            @keydown.enter="navigate"
            :aria-current="isExactActive ? 'page' : null"
          >
            <img :src="s.thumb" alt="" />
            <div class="series-meta">
              <h3>{{ s.title }}</h3>
              <p>
                <strong>Issues:</strong> {{ s.count }}
                <span v-if="s.years"> • <strong>Years:</strong> {{ s.years }}</span>
              </p>
            </div>
          </div>
        </template>
      </router-link>
    </div>

    <!-- Pagination -->
    <div v-if="filteredSeries.length > pageSize" class="pagination">
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
import { seriesState } from "@/store/seriesState";
import { useIssuesStore } from '../store/issuesStore'

export default {
  data() {
    return {
      pageSize: 20,
      showAdvancedFilters: false, 
    };
  },
  mounted() {
    this.searchSeries()
  },
  computed: {
    issuesStore() {
      return useIssuesStore()
    },

    loading() {
      return this.issuesStore.loading
    },
    error() {
      return this.issuesStore.error
    },
   seriesQuery: {
    get() {
      return seriesState.query;
    },
    set(val) {
      seriesState.query = val;
    },
  },
  seriesList: {
    get() {
      return seriesState.list;
    },
    set(val) {
      seriesState.list = val;
    },
  },

  filterStartYear: {
    get() {
      return seriesState.filterStartYear;
    },
    set(val) {
      seriesState.filterStartYear = val;
    },
  },
  filterEndYear: {
    get() {
      return seriesState.filterEndYear;
    },
    set(val) {
      seriesState.filterEndYear = val;
    },
  },
  filterMinIssues: {
    get() {
      return seriesState.filterMinIssues;
    },
    set(val) {
      seriesState.filterMinIssues = val;
    },
  },
  filterUnlimited: {
    get() {
      return seriesState.filterUnlimited;
    },
    set(val) {
      seriesState.filterUnlimited = val;
    },
  },
  filterOneShot: {
    get() {
      return seriesState.filterOneShot;
    },
    set(val) {
      seriesState.filterOneShot = val;
    },
  },
  filterComicFormats: {
    get() {
      return seriesState.filterComicFormats;
    },
    set(val) {
      seriesState.filterComicFormats = val;
    },
  },
  sortBy: {
    get() {
      return seriesState.sortBy;
    },
    set(val) {
      seriesState.sortBy = val;
    },
  },
  currentPage: {
    get() {
      return seriesState.currentPage;
    },
    set(val) {
      seriesState.currentPage = val;
    },
  },
    filteredSeries() {
      let list = [...this.seriesList];

      if (this.seriesQuery && this.seriesQuery.trim() !== "") {
        const query = this.seriesQuery.toLowerCase();
        list = list.filter((s) => s.title.toLowerCase().includes(query));
      }
      if (this.filterStartYear) {
        list = list.filter((s) => {
          const minYear = parseInt(s.years?.split("–")[0]) || null;
          return minYear && minYear >= this.filterStartYear;
        });
      }
      if (this.filterEndYear) {
        list = list.filter((s) => {
          const maxYear = parseInt(s.years?.split("–").slice(-1)[0]) || null;
          return maxYear && maxYear <= this.filterEndYear;
        });
      }

      // Issue count filter
      if (this.filterMinIssues) {
        list = list.filter((s) => s.count >= this.filterMinIssues);
      }

      // Sorting
      if (this.sortBy === "title") {
        list.sort((a, b) => a.title.localeCompare(b.title));
      } else if (this.sortBy === "count") {
        list.sort((a, b) => b.count - a.count);
      } else if (this.sortBy === "newest") {
        list.sort((a, b) => {
          const ay = parseInt(a.years?.split("–").slice(-1)[0]) || 0;
          const by = parseInt(b.years?.split("–").slice(-1)[0]) || 0;
          return by - ay;
        });
      } else if (this.sortBy === "oldest") {
        list.sort((a, b) => {
          const ay = parseInt(a.years?.split("–")[0]) || 0;
          const by = parseInt(b.years?.split("–")[0]) || 0;
          return ay - by;
        });
      }

      if (this.filterUnlimited) {
        list = list.filter((s) => s.hasUnlimited);
      }

      if (this.filterOneShot) {
        list = list.filter((s) => s.count > 1);
      }
      if (this.filterComicFormats) {
        list = list.filter((s) => {
          if (!s.formats) return false;
          return s.formats.some((f) =>
            ["comic", "comic book", "comic issue"].includes(f.toLowerCase())
          );
        });
      }

      return list;
    },
    totalPages() {
      return Math.ceil(this.filteredSeries.length / this.pageSize) || 1;
    },
    pagedSeries() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.filteredSeries.slice(start, start + this.pageSize);
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
  methods: {
    async searchSeries() {
      this.loading = true;
      this.error = null;
      this.currentPage = 1;
      try {

        await this.issuesStore.fetchIssues()
        const allIssues = this.issuesStore.issues || []
        console.log(allIssues.length)
        const issues = allIssues.filter(issue => !issue.is_variant || issue.is_variant === 0)

        const map = new Map();
        for (const it of issues) {
          const key = it.series_id ?? `no_id_${it.series_title || "Unknown Series"}`;
          if (!map.has(key)) map.set(key, []);
          map.get(key).push(it);
        }

        const list = Array.from(map.entries()).map(([series_id, list]) => {
          // Find issue #1 with image
          let issueOne = list.find((issue) => Number(issue.issue_number) === 1 && issue.image_url);
          if (!issueOne) {
            // fallback: lowest issue_number with image
            const sorted = list
              .filter((issue) => issue.image_url && !isNaN(Number(issue.issue_number)))
              .sort((a, b) => Number(a.issue_number) - Number(b.issue_number));
            issueOne = sorted.length ? sorted[0] : null;
          }
          const thumb = issueOne ? issueOne.image_url : "";
          const title = list[0].series_title || "Unknown Series";
          const years = this.computeYearRange(list.map((x) => x.release_date));
          const hasUnlimited = list.some((x) => x.marvel_unlimited === true);
          const formatsSet = new Set();
          for (const issue of list) {
            if (issue.format_type) {
              formatsSet.add(issue.format_type.toLowerCase());
            }
          }
          return {
            series_id,
            title,
            thumb,
            count: list.length,
            years,
            hasUnlimited,
            formats: Array.from(formatsSet),
          };
        });

        this.seriesList = list;
      } catch (e) {
        console.error(e);
        this.error = "Failed to fetch series.";
      } finally {
        this.loading = false;
      }
    },
    computeYearRange(dateStrs) {
      const years = dateStrs
        .map((d) => (d ? new Date(d).getFullYear() : null))
        .filter(Boolean);
      if (!years.length) return "";
      const min = Math.min(...years);
      const max = Math.max(...years);
      return min === max ? `${min}` : `${min}–${max}`;
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
    applyFilters() {
      this.currentPage = 1;
      this.error = null;
      this.searchSeries();
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
.app {
  font-family: "Roboto Condensed", "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}
.app input,
.app button,
.app select,
.app textarea {
  font-family: "Roboto Condensed", "Segoe UI", Tahoma, Geneva, Verdana, sans-serif !important;
}

body {
  font-family: "Roboto Condensed", "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  background: #f9f9f9;
  color: #333;
  margin: 0;
  padding: 0;
}

h1 {
  font-family: "Roboto Condensed", sans-serif;
  font-weight: 700;
  text-align: center;
  color: #1a1a1a;
  margin-bottom: 1.5rem;
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

.filters-row.advanced-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: center;
  margin-top: 0;
  padding-top: 8px;
  border-top: 1px solid #ddd;
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
  font-family: inherit
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

.loading,
.error,
.no-results {
  text-align: center;
  margin: 1rem 0;
  font-weight: 600;
}
.error {
  color: #d9534f;
}

.series-grid {
  display: grid;
  grid-template-columns: repeat(5, 237px);
  gap: 16px;
  justify-content: center;
}

.series-card {
  width: 237px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  background: none;
  border: none;
  box-shadow: none;
}

.series-card img {
  width: 237px;
  height: 355px;
  object-fit: cover;
  display: block;
}

.series-meta {
  padding: 8px 0;
  text-align: center;
  width: 100%;
  background: #fff;
}

.series-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgb(0 0 0 / 0.15);
}

.series-meta h3 {
  font-family: "Roboto Condensed", sans-serif;
  font-weight: 600;
  margin: 0 0 6px 0;
  font-size: 1.05rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
.series-meta p {
  font-family: "Roboto Condensed", sans-serif;
  font-weight: 400;
  margin: 0;
  color: #666;
  font-size: 0.95rem;
}

.pagination {
  margin: 15px 0;
  display: flex;
  justify-content: center;
  gap: 15px;
  align-items: center;
}
.pagination button {
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

/* Fade + slide transition */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  margin-top: 0;
}
.fade-slide-enter-to,
.fade-slide-leave-from {
  opacity: 1;
  max-height: 1000px;
  margin-top: 12px;
  padding-top: 8px;
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

</style>
