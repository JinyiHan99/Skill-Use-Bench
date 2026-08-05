import { defineSchema } from "@json-render/core";

export const dashboardSchema = defineSchema((s) => ({
  spec: s.object({
    root: s.string(),
    elements: s.map({
      type: s.string(),
      props: s.zod(),
      content: s.array(s.string()),
      visible: s.any(),
      watch: s.any(),
    }),
    state: s.any(),
  }),
  catalog: s.object({
    components: s.map({
      props: s.zod(),
      description: s.string(),
    }),
    actions: s.map({
      params: s.zod(),
      description: s.string(),
    }),
  }),
}), {
  promptTemplate: `You are a dashboard builder AI. Generate JSON specs for data dashboards.
Components: {{components}}
Actions: {{actions}}
Use visibility conditions to show/hide panels based on state.`,
  builtInActions: [
    { name: "setState", description: "Update a value in the state model" },
    { name: "refreshData", description: "Re-fetch data from the API and update state" },
  ],
});
