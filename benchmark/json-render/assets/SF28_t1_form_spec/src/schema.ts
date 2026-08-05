import { defineSchema } from "@json-render/core";

export const formSchema = defineSchema((s) => ({
  spec: s.object({
    root: s.string(),
    elements: s.map({
      type: s.string(),
      props: s.zod(),
      content: s.array(s.string()),
      visible: s.any(),
      watch: s.any(),
      validation: s.array(s.any()),
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
  promptTemplate: `You are a form builder AI. Generate JSON specs for form UIs.
Components available: {{components}}
Actions available: {{actions}}
State model: Always initialize form field state under /form/ paths.
Validation: Specify form validation constraints according to schema requirements.`,
});
