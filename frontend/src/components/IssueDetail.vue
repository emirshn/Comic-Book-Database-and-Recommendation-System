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

        <!-- Recommended Series Section -->
        <div v-if="recommendedSeries && Object.keys(recommendedSeries).length" class="recommended-series-section">
          <h3>Recommended Series</h3>

          <!-- From Same Creators -->
          <div v-if="recommendedSeries.sameCreators && recommendedSeries.sameCreators.length">
            <h4>From Same Creators</h4>
            <div
              class="recommendation-list"
              @mousedown="startDragRec"
              @mouseup="stopDragRec"
              @mouseleave="stopDragRec"
              @mousemove="onDragRec"
            >
              <div
                v-for="rec in recommendedSeries.sameCreators"
                :key="rec.series_id"
                class="recommendation-card"
                @click="handleRecClick(rec, $event)"
              >
                <img :src="rec.image_url" alt="Series cover" />
                <p>{{ rec.title }}</p>
              </div>
            </div>
          </div>
          <div class="partial-divider"></div>
          <!-- From Summary Model -->
          <div v-if="recommendedSeries.fromSummary && recommendedSeries.fromSummary.length">
            <h4>Similar by Summary</h4>
            <div
              class="recommendation-list"
              @mousedown="startDragRec"
              @mouseup="stopDragRec"
              @mouseleave="stopDragRec"
              @mousemove="onDragRec"
            >
              <div
                v-for="rec in recommendedSeries.fromSummary"
                :key="rec.series_id"
                class="recommendation-card"
                @click="handleRecClick(rec, $event)"
              >
                <img :src="rec.image_url" alt="Series cover" />
                <p>{{ rec.title }}</p>
              </div>
            </div>
          </div>
          <div class="partial-divider"></div>
          <!-- Title Similarity -->
          <div v-if="recommendedSeries.titleSimilarity && recommendedSeries.titleSimilarity.length">
            <h4>Title Similarity</h4>
            <div
              class="recommendation-list"
              @mousedown="startDragRec"
              @mouseup="stopDragRec"
              @mouseleave="stopDragRec"
              @mousemove="onDragRec"
            >
              <div
                v-for="rec in recommendedSeries.titleSimilarity"
                :key="rec.series_id"
                class="recommendation-card"
                @click="handleRecClick(rec, $event)"
              >
                <img :src="rec.image_url" alt="Series cover" />
                <p>{{ rec.title }}</p>
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
  props: {
    originalIssueId: String,
    variantIssueId: { type: String, default: null }
  },  
  data() {
    return {
      original: null,
      variants: [],
      selectedVariant: null, 
      issuesInSeries: [],
      loading: false,
      error: null,
      isDragging: false,
      dragStartX: 0,
      scrollStartX: 0,
      dragMoved: false,
      recommendedSeries: {
        sameCreators: [],
        fromSummary: [],
        titleSimilarity: []
      },
      isDraggingRec: false,
      dragStartXRec: 0,
      scrollStartXRec: 0,
      dragMovedRec: false,
    };
  },
  mounted() {
    this.loadOriginalIssue(this.originalIssueId);
  },
  watch: {
    originalIssueId(newId) {
      this.loadOriginalIssue(newId);
    },
    variantIssueId(newVariantId) {
      this.selectVariant(newVariantId);
    }
  },
  computed: {
    effectiveIssue() {
      if (this.selectedVariant) {
        return {
          ...this.original,
          ...this.selectedVariant,
          summary: this.selectedVariant.summary || this.original.summary,
          creators: this.selectedVariant.creators || this.original.creators || "",
          format: this.selectedVariant.format || this.original.format || "",
          upc: this.selectedVariant.upc || this.original.upc || "",
          foc_date: this.selectedVariant.foc_date || this.original.foc_date || "",
          price: this.selectedVariant.price || this.original.price || "",
          page_count: this.selectedVariant.page_count || this.original.page_count || "",
        };
      }
      return this.original || {};
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
      return this.original ? this.original.issue_id : null;
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
    async loadOriginalIssue(originalId) {
      if (!originalId) return;
      this.loading = true;
      this.error = null;
      this.original = null;
      this.variants = [];
      this.selectedVariant = null;
      this.issuesInSeries = [];

      try {
        // Load original issue
        const originalRes = await axios.get(`http://127.0.0.1:8000/issues/${originalId}`, {
          params: { dataset: "original" }
        });
        this.original = originalRes.data;

        // Load variants for this original
        const variantsRes = await axios.get(`http://127.0.0.1:8000/issues/${originalId}/variants`);
        this.variants = variantsRes.data || [];

        // Load issues in series
        if (this.original.series_id) {
          const issuesRes = await axios.get(`http://127.0.0.1:8000/issues/`, {
            params: {
              series_id: this.original.series_id,
              dataset: "original",
              ordering: "issue_number",
              limit: 1000,
            },
          });
          this.issuesInSeries = issuesRes.data || [];
          this.issuesInSeries.sort((a, b) => a.issue_number - b.issue_number);
        }

        // Fetch recommendations
        const recRes = await axios.get(`http://127.0.0.1:8000/issues/${originalId}/recommended_series`);
        this.recommendedSeries = recRes.data || {};

        // Select variant based on current param
        this.selectVariant(this.variantIssueId);

      } catch (e) {
        this.error = "Failed to load issue details.";
        console.warn(e);
      } finally {
        this.loading = false;
      }
    },

    selectVariant(variantId) {
      if (!variantId || variantId === this.original.issue_id) {
        this.selectedVariant = null;
        this.issue = this.original;  // For backward compatibility in computed and template
      } else {
        const found = this.variants.find(v => String(v.issue_id) === String(variantId));
        this.selectedVariant = found || null;
        this.issue = this.selectedVariant || this.original;
      }
    },

    formatDate(dateStr) {
      if (!dateStr) return "Unknown";
      return new Date(dateStr).toLocaleDateString();
    },

    goToIssue(issueId) {
      if (!issueId) return;

      this.$router.push({ 
        name: "IssueDetail", 
        params: { originalIssueId: issueId } 
      });
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
      if (this.dragMoved) return;

      const originalId = this.original ? this.original.issue_id : null;
      if (!originalId) return;

      this.$router.push({
        name: "IssueDetail",
        params: { originalIssueId: originalId, variantIssueId: issueId }
      });
    },
    startDragRec(event) {
      this.isDraggingRec = true;
      this.dragMovedRec = false;
      this.dragStartXRec = event.pageX;
      event.currentTarget.style.cursor = "grabbing";
      this.scrollStartXRec = event.currentTarget.scrollLeft;
    },
    stopDragRec(event) {
      this.isDraggingRec = false;
      event.currentTarget.style.cursor = "grab";
    },
    onDragRec(event) {
      if (!this.isDraggingRec) return;
      const dx = event.pageX - this.dragStartXRec;
      if (Math.abs(dx) > 3) this.dragMovedRec = true;
      event.currentTarget.scrollLeft = this.scrollStartXRec - dx;
    },
    handleRecClick(rec) {
      if (this.dragMovedRec) return;
      this.$router.push({ path: `/series/${rec.series_id}` });
    },
  },
};
</script>

<style scoped>
.recommended-series-section {
  margin-top: 20px;
  background: white;
  padding: 16px;
  border-radius: 8px;
  color: #333;
}


.recommended-series-section h4 {
  font-size: 1.2rem;
  margin: 10px 0;
}

.recommendation-list {
  display: flex;
  gap: 15px;
  overflow-x: auto;      
  overflow-y: hidden;    
  white-space: nowrap;  
  cursor: grab;
  scrollbar-width: none; 
  -ms-overflow-style: none; 
}

.recommendation-list::-webkit-scrollbar {
  display: none; 
}

.recommendation-card {
  flex: 0 0 auto;
  width: 150px; 
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  user-select: none;
  padding: 0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.1);
  background: white;
  transition: transform 0.2s ease;
  color: #333;
}

.recommendation-card img {
  height: 240px;
  width: auto;
  object-fit: contain;
  margin-bottom: 6px; 
  border-radius: 6px;
  user-select: none;
  pointer-events: none;
}

.recommendation-card p {
  margin: 0;
  padding: 0 6px; 
  font-weight: 600;
  font-size: 0.95rem;
  width: 100%;
  text-align: center;
  line-height: 1.2em;
  
  display: -webkit-box;
  -webkit-line-clamp: 4; 
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal; 
}

.partial-divider {
  border: none;
  border-top: 1px solid #ccc;
  width: 60%;
  margin-left: 20%;  
  margin-top: 12px;
  margin-bottom: 12px;
}

.recommendation-card:hover {
  transform: scale(1.05);
  box-shadow: 0 0 15px rgba(0, 122, 204, 0.6);
  z-index: 10;
}

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
