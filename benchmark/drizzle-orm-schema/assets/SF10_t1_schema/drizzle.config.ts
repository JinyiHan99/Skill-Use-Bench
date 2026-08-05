import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./src/database/schemas/*",
  out: "./src/database/migrations",
  dialect: "postgresql",
  strict: true,
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
