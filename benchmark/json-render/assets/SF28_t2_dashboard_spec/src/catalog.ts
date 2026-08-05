import { defineCatalog } from "@json-render/core";
import { dashboardSchema } from "./schema";
import { z } from "zod";

export const catalog = defineCatalog(dashboardSchema, {
  components: {
    Dashboard: {
      props: z.object({
        title: z.string(),
      }),
      description: "Top-level dashboard container",
    },
    MetricCard: {
      props: z.object({
        title: z.string(),
        value: z.any(),
        trend: z.any().optional(),
        icon: z.string().optional(),
      }),
      description: "Displays a single KPI metric with optional trend indicator",
    },
    Chart: {
      props: z.object({
        type: z.enum(["line", "bar", "pie", "donut"]),
        dataSource: z.any(),
        title: z.string().optional(),
      }),
      description: "Renders a chart visualization from data",
    },
    DataTable: {
      props: z.object({
        columns: z.array(z.object({ key: z.string(), label: z.string() })),
        rows: z.any(),
        sortable: z.boolean().optional(),
      }),
      description: "Tabular data display with optional sorting",
    },
    FilterBar: {
      props: z.object({
        value: z.any(),
        options: z.array(z.object({ label: z.string(), value: z.string() })),
        label: z.string(),
      }),
      description: "Dropdown filter that updates dashboard state",
    },
    TabGroup: {
      props: z.object({
        value: z.any(),
        tabs: z.array(z.object({ label: z.string(), value: z.string() })),
      }),
      description: "Tab navigation that controls which panel is visible",
    },
    Panel: {
      props: z.object({
        title: z.string().optional(),
      }),
      description: "A collapsible panel container for grouping content",
    },
    StatusBadge: {
      props: z.object({
        label: z.any(),
        color: z.any(),
      }),
      description: "Colored badge showing a status label",
    },
    Divider: {
      props: z.object({}),
      description: "Visual separator between sections",
    },
  },
  actions: {
    loadReport: {
      params: z.object({
        reportId: z.string(),
        timeRange: z.string(),
      }),
      description: "Load a specific report by ID within a time range",
    },
    exportCSV: {
      params: z.object({
        tableId: z.string(),
      }),
      description: "Export a data table as CSV download",
    },
  },
});
