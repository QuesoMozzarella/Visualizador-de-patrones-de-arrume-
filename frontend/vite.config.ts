import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En desarrollo, Vite sirve React en :5173 y reenvia /api al backend Flask
// en :5000, asi el navegador ve un solo origen y no hace falta CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:5000" },
  },
  // Plotly va en su propio archivo (~4.6 MB) y se carga al abrir el 3D
  build: { chunkSizeWarningLimit: 5000 },
  test: { environment: "node" },
});
