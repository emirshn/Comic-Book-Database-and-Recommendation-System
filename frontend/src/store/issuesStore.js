import { defineStore } from 'pinia'
import api from "../axios";

export const useIssuesStore = defineStore('issues', {
  state: () => ({
    issues: [],
    loading: false,
    error: null,
  }),
  actions: {
    async fetchIssues() {
      if (this.issues.length) return 

      this.loading = true
      this.error = null
      try {
        const res = await api.get('/issues/', {
          params: { dataset: 'all', limit: 100000 },
        })
        this.issues = res.data || []
      } catch (e) {
        this.error = 'Failed to fetch issues.'
      } finally {
        this.loading = false
      }
    },
  },
})
