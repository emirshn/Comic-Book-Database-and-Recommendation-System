<template>
  <div class="creator-topology-stats">
    <div
      class="section-header creator-header"
      @click="showTopologyData = !showTopologyData"
      role="button"
      tabindex="0"
    >
      CREATOR STATISTICS
      <div class="toggle-indicator">{{ showTopologyData ? "▲" : "▼" }}</div>
    </div>

    <transition name="slide-fade">
      <div v-show="showTopologyData" class="section-content">
        <div class="topology-wrapper">
          <div class="chart-container" style="flex: 1;">
            <div id="creator-topology-network" style="width: 100%; height: 100%;"></div>
          </div>

          <div class="creator-legend">
            <h3>Creator Details</h3>

            <div v-if="!selectedCreator" class="default-text">
              Click on a creator node to see details here.
            </div>

            <div v-else>
              <p><strong>{{ selectedCreator }}</strong></p>
              <p>Number of Issues Worked On: {{ getCollabCount(selectedCreator) }}</p>

              <h4>Series worked on:</h4>
              <ul v-if="creatorSeries.length" class="series-list">
                <li v-for="series in creatorSeries" :key="series">{{ series }}</li>
              </ul>
              <p v-else><em>No series info available.</em></p>
            </div>
          </div>
        </div>
          <div class="chart-container">
            <BarChart
              :data="mostCollaboratedCreatorsData"
              :options="barOptionsCreators"
              :style="{ width: '100%', height: '320px' }"
            />
          </div>

          <div class="chart-container">
            <BarChart
              :data="creatorsWithMostBooksData"
              :options="barOptionsCreatorsBooks"
              :style="{ width: '100%', height: '320px' }"
            />
        </div>
      </div>
    </transition>

  </div>
</template>

<script>
import { Network } from "vis-network/standalone";
import { Bar } from "vue-chartjs";

export default {
  name: "CreatorTopology",
  props: {
    issues: {
      type: Array,
      required: true,
    },
  },
  components: {
    BarChart: Bar,
  },
  data() {
    return {
      showTopologyData: false,
      creatorTopologyData: {
        nodes: [],
        edges: [],
      },
      creatorNetwork: null,
      selectedCreator: null,
      collaborationCountsByCreator: new Map(),
      creatorSeriesMap: {}, 
      mostCollaboratedCreatorsData: { labels: [], datasets: [] },
      creatorsWithMostBooksData: { labels: [], datasets: [] },
      barOptionsCreators: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          title: { display: true, text: "Most Collaborated Creators (by issues)" },
        },
      },
      barOptionsCreatorsBooks: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          title: { display: true, text: "Creators with Most Books (series count)" },
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
    prepareCharts() {
      this.prepareCreatorTopologyData();
      this.prepareMostCollaboratedCreatorsChart();
      this.prepareCreatorsWithMostBooksChart();
    },
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

    prepareCreatorTopologyData() {
    const collaborationCounts = new Map();
    const creatorCollabCounts = new Map();
    const creatorSeriesMap = {};
    const rolesMap = {}; 

    this.issues.forEach((issue) => {
        if (issue.is_variant) return;
        if (issue.format_type !== "Comic") return;

        const creatorsByRole = this.parseCreatorsDetailed(issue.creators);

        const relevantRoles = Object.entries(creatorsByRole).filter(([role]) => {
        const r = role.toLowerCase();
        return r === "writer" || r === "penciller";
        });

        relevantRoles.forEach(([role, names]) => {
        names.forEach((creator) => {
            if (!rolesMap[creator]) rolesMap[creator] = new Set();
            rolesMap[creator].add(role.toLowerCase());
        });
        });

        const relevantCreatorsSet = new Set();
        relevantRoles.forEach(([, names]) => {
        names.forEach((name) => relevantCreatorsSet.add(name));
        });

        const uniqueCreators = Array.from(relevantCreatorsSet).sort();

        uniqueCreators.forEach((creator) => {
        if (!creatorSeriesMap[creator]) creatorSeriesMap[creator] = new Set();
        if (issue.series_title) {
            creatorSeriesMap[creator].add(issue.series_title);
        }
        });

        for (let i = 0; i < uniqueCreators.length; i++) {
        creatorCollabCounts.set(
            uniqueCreators[i],
            (creatorCollabCounts.get(uniqueCreators[i]) || 0) + 1
        );

        for (let j = i + 1; j < uniqueCreators.length; j++) {
            const pairKey = uniqueCreators[i] + " & " + uniqueCreators[j];
            collaborationCounts.set(pairKey, (collaborationCounts.get(pairKey) || 0) + 1);
        }
        }
    });

    const filteredCreators = Array.from(creatorCollabCounts.entries())
        .filter(([, count]) => count >= 3)
        .map(([name]) => name);

    let filteredEdges = Array.from(collaborationCounts.entries()).filter(([pairKey]) => {
        const [from, to] = pairKey.split(" & ");
        return filteredCreators.includes(from) && filteredCreators.includes(to);
    });

    filteredEdges = filteredEdges.sort((a, b) => b[1] - a[1]).slice(0, 500);

    const connectedCreators = new Set();
    filteredEdges.forEach(([pairKey]) => {
        pairKey.split(" & ").forEach((name) => connectedCreators.add(name));
    });

    const nodes = Array.from(connectedCreators).map((name) => {
        const roles = rolesMap[name] || new Set();

        let color = "#7bd389"; // default greenish
        if (roles.has("writer") && roles.has("penciller")) {
        color = "#a259ff"; // purple if both roles
        } else if (roles.has("writer")) {
        color = "#2c7be5"; // blue for writers
        } else if (roles.has("penciller")) {
        color = "#3ac47d"; // green for pencilers
        }

        const seriesCount = creatorSeriesMap[name]?.size || 1;
        const size = Math.min(50, 16 + Math.floor(seriesCount / 5));

        return {
        id: name,
        label: name,
        color,
        size,
        };
    });

    const edges = filteredEdges.map(([pairKey, count]) => {
        const [from, to] = pairKey.split(" & ");
        return {
        from,
        to,
        value: count,
        title: `${count} collaborations`,
        width: Math.min(10, Math.max(1, count / 3)),
        };
    });

    this.creatorTopologyData = { nodes, edges };
    this.collaborationCountsByCreator = creatorCollabCounts;
    this.creatorSeriesMap = creatorSeriesMap;

    this.$nextTick(() => {
        this.renderCreatorTopologyNetwork();
    });
    },

    renderCreatorTopologyNetwork() {
      const container = document.getElementById("creator-topology-network");
      if (!container) return;

      const data = {
        nodes: this.creatorTopologyData.nodes,
        edges: this.creatorTopologyData.edges,
      };

      const options = {
        nodes: {
          shape: "dot",
          size: 16,
          font: {
            size: 14,
            color: "#000",
          },
          borderWidth: 2,
          borderWidthSelected: 4,
          color: {
            border: "#2c7be5",
            background: "#7bd389",
          },
        },
        edges: {
          color: "#7b9fff",
          width: 1,
          smooth: {
            enabled: true,
            type: "continuous",
          },
          arrows: {
            to: false,
            from: false,
          },
        },
        physics: {
          enabled: true,
          barnesHut: {
            gravitationalConstant: -3500,
            springLength: 300,
            springConstant: 0.02,
            },
            stabilization: {
            iterations: 400,
            updateInterval: 50,
            fit: true
            },

        },
        interaction: {
          hover: true,
          tooltipDelay: 100,
          hideEdgesOnDrag: true,
          multiselect: false,
          selectable: true,
        },
      };

      if (this.creatorNetwork) {
        this.creatorNetwork.destroy();
      }
      this.creatorNetwork = new Network(container, data, options);
      
      this.selectedCreator = null;

      this.creatorNetwork.on("click", (params) => {
        if (params.nodes.length === 1) {
          this.selectedCreator = params.nodes[0];
        } else {
          this.selectedCreator = null;
        }
      });
    },

    getCollabCount(creatorName) {
      return this.collaborationCountsByCreator.get(creatorName) || 0;
    },
    prepareMostCollaboratedCreatorsChart() {
      const pairCounts = new Map();

      function parseCreatorsDetailed(creatorsStr) {
        if (!creatorsStr) return {};

        const entries = creatorsStr
          .split(";")
          .map(s => s.trim())
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
      }

      this.issues.forEach(issue => {
        const creatorsByRole = parseCreatorsDetailed(issue.creators);

        const relevantRoles = Object.entries(creatorsByRole).filter(
          ([role]) => {
            const r = role.toLowerCase();
            return r === "writer" || r === "penciller";
          }
        );

        const creators = relevantRoles.flatMap(([, names]) => names);

        const uniqueCreators = Array.from(new Set(creators)).sort();

        for (let i = 0; i < uniqueCreators.length; i++) {
          for (let j = i + 1; j < uniqueCreators.length; j++) {
            const pairKey = uniqueCreators[i] + " & " + uniqueCreators[j];
            pairCounts.set(pairKey, (pairCounts.get(pairKey) || 0) + 1);
          }
        }
      });

      const sortedPairs = Array.from(pairCounts.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 20);
      
      this.mostCollaboratedCreatorsData = {
        labels: sortedPairs.map(([pair]) => pair),
        datasets: [
          {
            label: "Number of Issues Together",
            data: sortedPairs.map(([, count]) => count),
            backgroundColor: "#7bd389",
          },
        ],
      };
    },

   prepareCreatorsWithMostBooksChart() {
  const creatorSeries = new Map();

  this.issues.forEach((issue) => {
    const creatorsByRole = this.parseCreatorsDetailed(issue.creators);
    if (!issue.series_id) return;

    // Get only writers and pencilers
    const relevantRoles = ['writer', 'penciller'];

    // Collect all relevant creators in one array
    const creators = Object.entries(creatorsByRole)
      .filter(([role]) => relevantRoles.includes(role.toLowerCase()))
      .flatMap(([, names]) => names);

    // For each relevant creator, add this series id
    creators.forEach((name) => {
      if (!creatorSeries.has(name)) creatorSeries.set(name, new Set());
      creatorSeries.get(name).add(issue.series_id);
    });
  });

  // Transform map to array [creatorName, numberOfSeries]
  const creatorSeriesCount = Array.from(creatorSeries.entries())
    .map(([name, seriesSet]) => [name, seriesSet.size]);

  // Sort descending by number of series and take top 20
  const sortedCreators = creatorSeriesCount.sort((a, b) => b[1] - a[1]).slice(0, 20);

  this.creatorsWithMostBooksData = {
    labels: sortedCreators.map(([name]) => name),
    datasets: [
      {
        label: "Number of Series",
        data: sortedCreators.map(([, count]) => count),
        backgroundColor: "#63a4ff",
      },
    ],
  };
},


  },
};
</script>

<style scoped>
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
  color: #7bd389;
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
  height: 600px;
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
