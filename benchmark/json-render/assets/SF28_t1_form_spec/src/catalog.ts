import { defineCatalog } from "@json-render/core";
import { formSchema } from "./schema";
import { z } from "zod";

export const catalog = defineCatalog(formSchema, {
  components: {
    Form: {
      props: z.object({
        title: z.string(),
        submitLabel: z.string().optional(),
      }),
      description: "Top-level form container with title and submit button",
    },
    Section: {
      props: z.object({
        title: z.string(),
        collapsible: z.boolean().optional(),
      }),
      description: "Groups related form fields under a heading",
    },
    TextInput: {
      props: z.object({
        value: z.any(),
        label: z.string(),
        placeholder: z.string().optional(),
        disabled: z.boolean().optional(),
      }),
      description: "Single-line text input field",
    },
    TextArea: {
      props: z.object({
        value: z.any(),
        label: z.string(),
        rows: z.number().optional(),
        placeholder: z.string().optional(),
      }),
      description: "Multi-line text input",
    },
    Select: {
      props: z.object({
        value: z.any(),
        label: z.string(),
        options: z.array(z.union([z.string(), z.object({ label: z.string(), value: z.string() })])),
        placeholder: z.string().optional(),
      }),
      description: "Dropdown select field",
    },
    Checkbox: {
      props: z.object({
        checked: z.any(),
        label: z.string(),
      }),
      description: "Boolean checkbox toggle",
    },
    DatePicker: {
      props: z.object({
        value: z.any(),
        label: z.string(),
        minDate: z.string().optional(),
        maxDate: z.string().optional(),
      }),
      description: "Date selection input",
    },
    RadioGroup: {
      props: z.object({
        value: z.any(),
        label: z.string(),
        options: z.array(z.object({ label: z.string(), value: z.string() })),
      }),
      description: "Radio button group for single selection",
    },
    Alert: {
      props: z.object({
        message: z.any(),
        severity: z.enum(["info", "warning", "error", "success"]).optional(),
      }),
      description: "Informational alert banner",
    },
    Button: {
      props: z.object({
        label: z.string(),
        variant: z.enum(["primary", "secondary", "danger"]).optional(),
        action: z.any(),
      }),
      description: "Clickable button that triggers an action",
    },
  },
  actions: {
    submitForm: {
      params: z.object({
        endpoint: z.string(),
      }),
      description: "Submit the form data to the specified API endpoint",
    },
    resetForm: {
      params: z.object({}),
      description: "Reset all form fields to their initial values",
    },
    navigateStep: {
      params: z.object({
        step: z.number(),
      }),
      description: "Navigate to a specific step in a multi-step form",
    },
  },
});
