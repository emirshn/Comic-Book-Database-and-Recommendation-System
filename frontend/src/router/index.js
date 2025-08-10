import { createRouter, createWebHistory } from "vue-router";

import SeriesList from "@/components/SeriesList.vue";
import SeriesIssues from "@/components/SeriesIssues.vue";
import IssueDetail from '@/components/IssueDetail.vue';

const routes = [
  { path: "/series", component: SeriesList, name: "SeriesList" },
  { path: "/series/:seriesId", component: SeriesIssues, props: true, name: "Series" },
  { 
  path: '/issue/:issueId', 
  name: 'IssueDetail', 
  component: IssueDetail, 
  props: true 
  },
  { path: "/", redirect: "/series" },
];


const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
