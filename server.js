// server.js
require("dotenv").config();

const express = require("express");
const cors = require("cors");

const connectDB = require("./db");
const modelRoutes = require("./routes/modelRoutes");

// NOTE: We'll create this file next (agentic AI endpoints).
// Keep this require here so your structure is ready.
let agentRoutes;
try {
  agentRoutes = require("./agentRoutes");
} catch (e) {
  agentRoutes = null; // Allows server to boot even before agentRoutes exists
}

const app = express();

// --- Middleware ---
app.use(cors());
app.use(express.json({ limit: "2mb" })); // adjust if you send big payloads
app.use(express.urlencoded({ extended: true }));

// --- Health check (HF Spaces likes this) ---
app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok" });
});

// --- Base route ---
app.get("/", (req, res) => {
  res.status(200).json({
    message: "Backend is running",
    routes: {
      health: "/health",
      model_predict: "/api/model/predict",
      agent: "/api/agent/*",
    },
  });
});

// --- Routes ---
app.use("/api/model", modelRoutes);

if (agentRoutes) {
  app.use("/api/agent", agentRoutes);
} else {
  // Temporary: until agentRoutes.js exists
  app.use("/api/agent", (req, res) => {
    res.status(501).json({
      error: "Agent routes not implemented yet. Next step: add agentRoutes.js",
    });
  });
}

// --- Error handler (last) ---
app.use((err, req, res, next) => {
  console.error("Unhandled error:", err);
  res.status(err.statusCode || 500).json({
    error: err.message || "Internal Server Error",
  });
});

// --- Start server ---
const PORT = process.env.PORT || 5000;

(async () => {
  try {
    await connectDB();
    app.listen(PORT, () => {
      console.log(`✅ Server running on port ${PORT}`);
    });
  } catch (err) {
    console.error("❌ Failed to start server:", err);
    process.exit(1);
  }
})();
