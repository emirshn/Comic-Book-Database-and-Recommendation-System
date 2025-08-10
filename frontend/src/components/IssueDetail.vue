<template>
  <div class="issue-detail-wrapper">
    <!-- Blurred fullscreen cover background -->
    <div
      v-if="effectiveIssue.image_url"
      class="fullscreen-cover-bg"
      :style="{ backgroundImage: `url(${effectiveIssue.image_url})` }"
    ></div>
    <!-- Dark overlay above blur for contrast -->
    <div class="cover-bg-overlay"></div>

    <!-- Left navigation arrow -->
    <button
      class="nav-arrow left"
      @click="goToIssue(prevIssueId)"
      :disabled="!prevIssueId"
      aria-label="Previous Issue"
    >
      ‹
    </button>

    <div class="app issue-detail-page">
      <router-link
        v-if="effectiveIssue"
        :to="`/series/${effectiveIssue.series_id}`"
        class="back"
      >
        ← Back to Series
      </router-link>

      <div v-if="loading" class="loading">Loading issue details...</div>
      <div v-else-if="error" class="error">{{ error }}</div>

      <div v-else-if="effectiveIssue">
        <!-- Top main info with transparent background -->
        <div class="issue-main-info">
          <img :src="effectiveIssue.image_url" alt="Cover" width="280" />

          <div class="issue-text-content">
            <h2>{{ effectiveIssue.title }}</h2>
            <div class="creator-column release-date">
              <strong>Release Date</strong>
              <p>{{ formatDate(effectiveIssue.release_date) }}</p>
            </div>

            <div class="creators-grid" v-if="Object.keys(parsedCreators).length">
              <div class="creator-column">
                <strong>Writer</strong>
                <p>{{ (parsedCreators.Writer || []).join(", ") || "N/A" }}</p>
              </div>
              <div class="creator-column">
                <strong>Penciller</strong>
                <p>{{ (parsedCreators.Penciller || []).join(", ") || "N/A" }}</p>
              </div>
            </div>

            <p><strong>Summary:</strong> {{ effectiveIssue.summary || "No summary available." }}</p>
          </div>
        </div>

        <!-- More Details & Stories & Cover Information -->
        <section class="more-details">
          <div class="top-row">
            <div class="more-details-left">
              <h3>More Details</h3>
              <div class="extended-info">
                <div><strong>Format:</strong> {{ effectiveIssue.format_type || "N/A" }}</div>
                <div><strong>Price:</strong> {{ effectiveIssue.price || "N/A" }}</div>
                <div><strong>Page Count:</strong> {{ effectiveIssue.page_count || "N/A" }}</div>
                <div><strong>Rating:</strong> {{ effectiveIssue.rating || "N/A" }}</div>
              </div>
            </div>

            <div class="stories-right">
              <h3>Stories</h3>
              <p v-for="(names, role) in storiesCreators" :key="role">
                <strong>{{ role }}:</strong> {{ names.join(", ") }}
              </p>
            </div>

            <div class="cover-info-small">
              <h3>Cover Information</h3>
              <p v-for="(names, role) in coverCreators" :key="role">
                <strong>{{ role }}:</strong> {{ names.join(", ") }}
              </p>
              <strong v-if="Object.keys(coverCreators).length === 0">Not Available</strong>
            </div>
          </div>
        </section>

        <!-- Variants section with white background -->
        <div v-if="variants.length" class="variants-section">
          <div class="creator-column">
                <strong>Variants</strong>
          </div>
          <div
            class="variant-list"
            ref="variantList"
            @mousedown="startDrag"
            @mouseup="stopDrag"
            @mouseleave="stopDrag"
            @mousemove="onDrag"
          >
            <div
              v-for="variant in variants"
              :key="variant.issue_id"
              class="variant-image-wrapper"
              @click="handleVariantClick(variant.issue_id)"
              :title="variant.is_original_variant ? 'Original Issue' : `${variant.variant_name}`"
            >
              <img :src="variant.image_url" alt="Variant cover" />
              <div class="variant-label">
                {{ variant.is_original_variant ? "Original" : `${variant.variant_name}` }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right navigation arrow -->
    <button
      class="nav-arrow right"
      @click="goToIssue(nextIssueId)"
      :disabled="!nextIssueId"
      aria-label="Next Issue"
    >
      ›
    </button>
  </div>
</template>

<script>
import axios from "axios";

export default {
  props: ["issueId"],
  data() {
    return {
      issue: null,
      variants: [],
      original: null,
      issuesInSeries: [],
      loading: false,
      error: null,
      isDragging: false,
      dragStartX: 0,
      scrollStartX: 0,
      dragMoved: false,
    };
  },
  mounted() {
    this.loadIssue();
  },
  watch: {
    issueId(newId, oldId) {
      if (newId !== oldId) {
        this.loadIssue();
      }
    },
  },
  computed: {
    effectiveIssue() {
      if (this.issue && this.issue.dataset === "variant" && this.original) {
        return {
          ...this.issue,
          summary: this.issue.summary || this.original.summary,
          creators: this.issue.creators || this.original.creators || "",
          format: this.issue.format || this.original.format || "",
          upc: this.issue.upc || this.original.upc || "",
          foc_date: this.issue.foc_date || this.original.foc_date || "",
          price: this.issue.price || this.original.price || "",
          page_count: this.issue.page_count || this.original.page_count || "",
        };
      }
      return this.issue || {};
    },
    parsedCreators() {
      if (!this.effectiveIssue.creators) return {};

      const entries = this.effectiveIssue.creators
        .split(";")
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

    storiesCreators() {
      if (!this.parsedCreators) return {};
      const filtered = {};
      for (const [role, names] of Object.entries(this.parsedCreators)) {
        if (!role.toLowerCase().includes("cover") && role.toLowerCase() !== "editor") {
          filtered[role] = names;
        }
      }
      return filtered;
    },

    coverCreators() {
      if (!this.parsedCreators) return {};
      const filtered = {};
      for (const [role, names] of Object.entries(this.parsedCreators)) {
        if (role.toLowerCase().includes("cover") || role.toLowerCase() === "editor") {
          filtered[role] = names;
        }
      }
      return filtered;
    },

    currentOriginalIssueId() {
      if (!this.issue) return null;
      if (this.issue.dataset === "original") {
        return this.issue.issue_id;
      }
      if (this.issue.dataset === "variant" && this.issue.original_issue_id) {
        return this.issue.original_issue_id;
      }
      return null;
    },

    currentIssueIndex() {
      const id = String(this.currentOriginalIssueId);
      return this.issuesInSeries.findIndex((i) => String(i.issue_id) === id);
    },
    prevIssueId() {
      if (this.currentIssueIndex > 0) {
        return this.issuesInSeries[this.currentIssueIndex - 1].issue_id;
      }
      return null;
    },
    nextIssueId() {
      if (
        this.currentIssueIndex >= 0 &&
        this.currentIssueIndex < this.issuesInSeries.length - 1
      ) {
        return this.issuesInSeries[this.currentIssueIndex + 1].issue_id;
      }
      return null;
    },
  },
  methods: {
    async loadIssue() {
      if (!this.issueId) return;

      this.loading = true;
      this.error = null;
      this.issue = null;
      this.variants = [];
      this.original = null;
      this.issuesInSeries = [];

      try {
        const res = await axios.get(`http://127.0.0.1:8000/issues/${this.issueId}`);
        this.issue = res.data;

        if (this.issue.dataset === "original") {
          const vres = await axios.get(
            `http://127.0.0.1:8000/issues/${this.issueId}/variants`
          );
          this.variants = vres.data || [];
          this.original = null;
        } else if (this.issue.dataset === "variant") {
          const ores = await axios.get(
            `http://127.0.0.1:8000/issues/${this.issue.original_issue_id}`,
            {
              params: { dataset: "original" },
            }
          );
          this.original = ores.data || null;

          if (this.original) {
            const vres = await axios.get(
              `http://127.0.0.1:8000/issues/${this.original.issue_id}/variants`
            );
            this.variants = vres.data || [];
          }
        }

        if (this.issue && this.issue.series_id) {
          const issuesRes = await axios.get(`http://127.0.0.1:8000/issues/`, {
            params: {
              series_id: this.issue.series_id,
              dataset: "original",
              ordering: "issue_number",
              limit: 1000,
            },
          });
          this.issuesInSeries = issuesRes.data || [];

          this.issuesInSeries.sort((a, b) => a.issue_number - b.issue_number);
        }
      } catch (e) {
        this.error = "Failed to load issue details.";
      } finally {
        this.loading = false;
      }
    },
    formatDate(dateStr) {
      if (!dateStr) return "Unknown";
      return new Date(dateStr).toLocaleDateString();
    },
    goToIssue(issueId) {
      if (!issueId) return;
      this.$router.push({ name: "IssueDetail", params: { issueId } });
    },

    startDrag(event) {
  this.isDragging = true;
  this.dragMoved = false;
  this.dragStartX = event.pageX;
  this.scrollStartX = this.$refs.variantList.scrollLeft;
  this.$refs.variantList.style.cursor = "grabbing";
    },
    stopDrag() {
      this.isDragging = false;
      this.$refs.variantList.style.cursor = "grab";
    },
    onDrag(event) {
      if (!this.isDragging) return;
      const dx = event.pageX - this.dragStartX;
      if (Math.abs(dx) > 3) {
        this.dragMoved = true;
      }
      this.$refs.variantList.scrollLeft = this.scrollStartX - dx;
    },
    handleVariantClick(issueId) {
    if (this.dragMoved) {
      return;
    }
    this.goToIssue(issueId);
  },
  },
};
</script>

<style scoped>
.fullscreen-cover-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
  filter: blur(10px);
  opacity: 0.3;
  z-index: -2;
  pointer-events: none;
}

.cover-bg-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.4);
  z-index: -1;
  pointer-events: none;
}

.issue-detail-wrapper {
  position: relative;
  max-width: 1100px;
  margin: 20px auto;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 20px 0;
  z-index: 1;
}

.app.issue-detail-page {
  width: 100%;
  padding: 20px;
  background: transparent;
  border-radius: 10px;
  box-shadow: none;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  color: white;
  position: relative;
  pointer-events: auto;
}

.issue-main-info {
  display: flex;
  gap: 30px;
  align-items: flex-start;
  max-width: 100%;
  margin-bottom: 20px;
  color: white;
}

.issue-main-info h2 {
  margin-top: 0;
}

.issue-main-info img {
  flex-shrink: 0;
  width: 280px;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.8);
  object-fit: contain;
}

.creators-grid {
  display: flex;
  gap: 40px;
  margin-bottom: 20px;
  width: 100%;
}

.creator-column {
  flex: 1;
  min-width: 0;
}

.creator-column strong {
  display: block;
  font-weight: 700;
  margin-bottom: 6px;
  font-size: 1.1rem;
}

.creator-column p {
  margin: 0;
  font-size: 1rem;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: white;
}

.release-date {
  margin-bottom: 20px;
}

.release-date strong {
  font-weight: 700;
  font-size: 1.1rem;
  display: block;
  margin-bottom: 6px;
}

.release-date p {
  margin: 0;
  font-size: 1rem;
  line-height: 1.4;
  color: white;
}

.more-details {
  margin-bottom: 30px;
  background: white;
  padding: 16px;
  border-radius: 8px;
  font-size: 1rem;
  color: #333;
}

.top-row {
  display: flex;
  gap: 40px;
  margin-bottom: 20px;
  align-items: flex-start;
}

.more-details-left,
.stories-right,
.cover-info-small {
  flex: 1;
  min-width: 0;
}

.cover-info-small {
  font-size: 1rem;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

.stories-right p,
.cover-info-small p {
  margin: 0;
  line-height: 1.4;
  padding: 2px 0;
  color: #333;
}

.more-details-left h3,
.stories-right h3,
.cover-info-small h3 {
  font-weight: 700;
  margin-bottom: 12px;
  font-size: 1.3rem;
  color: #222;
}

.extended-info > div {
  margin-bottom: 8px;
}

.creator-column {
  margin-bottom: 12px;
}

.creator-column strong {
  font-weight: 700;
  margin-right: 6px;
}

.variants-section {
  margin-top: 20px;
  user-select: none;
  cursor: grab;
  overflow-x: auto;
  overflow-y: visible;
  white-space: nowrap;
  padding: 10px 20px; 
  border-bottom: 1px solid #ccc;
  display: flex;
  flex-direction: column;
  max-height: none;
  box-sizing: border-box;
  background: white;
  border-radius: 8px;
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.1);
  color: #333;
}
.variants-section .creator-column strong {
  font-size: 1.3rem;  
  font-weight: 700;
  color: #222; 
}
.variant-list {
  display: flex;
  gap: 15px;
  align-items: center;
  overflow-x: auto;
  overflow-y: visible;
  scrollbar-width: none;
  -ms-overflow-style: none;
  max-height: none;
  box-sizing: border-box;
  padding-bottom: 10px;
  margin-left: 10px;  
  margin-right: 10px; 
}


.variant-list::-webkit-scrollbar {
  display: none;
}

.variant-image-wrapper {
  flex: 0 0 auto;
  width: auto;
  height: 320px;
  position: relative;
  cursor: pointer;
  border-radius: 8px;
  overflow: visible;
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.1);
  background: transparent;
  transition: transform 0.2s ease;
  display: flex;
  justify-content: center;
  align-items: center;
}

.variant-image-wrapper:hover {
  transform: scale(1.05);
  box-shadow: 0 0 15px rgba(0, 122, 204, 0.6);
  z-index: 10;
}

.variant-image-wrapper img {
  height: 320px;
  width: auto;
  object-fit: contain;
  display: block;
  user-select: none;
  pointer-events: none;
  margin-bottom: 0;
}

.variant-label {
  position: absolute;
  bottom: 6px;
  left: 6px;
  background-color: rgba(0, 122, 204, 0.8);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 600;
  user-select: none;
  pointer-events: none;
}

.back {
  display: inline-block;
  margin-bottom: 1rem;
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
}

.back:hover {
  background-color: #005fa3;
}

.loading,
.error {
  text-align: center;
  margin: 1rem 0;
  font-weight: 600;
}

.error {
  color: #d9534f;
}
.nav-arrow {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12rem; 
  color: rgba(0, 122, 204, 0.3);
  background: transparent;
  border: none;
  cursor: pointer;
  user-select: none;
  z-index: 10000; 
  height: 80vh;
  width: auto;
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: auto;
  color: rgba(0, 122, 204, 0.7); 
  transition: color 0.3s ease;
}


.nav-arrow:hover:not(:disabled) {
  color: rgba(0, 122, 204, 1);
  filter: drop-shadow(0 0 5px rgba(0, 122, 204, 0.8));
}

.nav-arrow:disabled {
  color: rgba(0, 122, 204, 0.3); 
  cursor: default;
  pointer-events: none;
  filter: none;
}

.nav-arrow.left {
  left: 5px;
}

.nav-arrow.right {
  right: 5px;
}

</style>
