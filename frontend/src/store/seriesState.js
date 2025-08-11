import { reactive } from "vue";

export const seriesState = reactive({
  query: "",
  list: [],
  
  filterStartYear: 1900,
  filterEndYear: new Date().getFullYear(),
  filterMinIssues: null,
  filterUnlimited: false,
  filterOneShot: false,
  filterComicFormats: true,
  sortBy: "title",
  
  currentPage: 1,
});
