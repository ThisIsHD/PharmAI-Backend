// agentRoutes.js
const express = require("express");
const axios = require("axios");
const router = express.Router();

// Python FastAPI backend URL
const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || "http://localhost:7860";

/**
 * POST /api/agent/run
 * Proxy to Python FastAPI /run endpoint
 */
router.post("/run", async (req, res, next) => {
  try {
    const { session_id, query } = req.body;

    if (!query) {
      return res.status(400).json({ error: "query is required" });
    }

    // Call Python backend
    const response = await axios.post(
      `${PYTHON_BACKEND_URL}/run`,
      {
        session_id: session_id || null,
        query: query,
      },
      {
        headers: { "Content-Type": "application/json" },
        timeout: 120000, // 2 minutes timeout for LLM calls
      }
    );

    return res.status(200).json(response.data);
  } catch (err) {
    console.error("Agent run error:", err.message);
    
    if (err.response) {
      // Python backend returned an error
      return res.status(err.response.status).json({
        error: err.response.data?.detail || err.response.data?.error || "Agent execution failed",
        details: err.response.data,
      });
    }
    
    if (err.code === "ECONNREFUSED") {
      return res.status(503).json({
        error: "Python backend is not running. Start it with: uvicorn app:app --port 7860",
      });
    }

    return next(err);
  }
});

/**
 * GET /api/agent/session/:session_id/history
 * Get conversation history for a session
 */
router.get("/session/:session_id/history", async (req, res, next) => {
  try {
    const { session_id } = req.params;

    const response = await axios.get(
      `${PYTHON_BACKEND_URL}/session/${session_id}/history`,
      { timeout: 5000 }
    );

    return res.status(200).json(response.data);
  } catch (err) {
    console.error("Get history error:", err.message);
    
    if (err.response) {
      return res.status(err.response.status).json({
        error: "Failed to retrieve session history",
        details: err.response.data,
      });
    }

    return next(err);
  }
});

/**
 * DELETE /api/agent/session/:session_id
 * Clear a session's history
 */
router.delete("/session/:session_id", async (req, res, next) => {
  try {
    const { session_id } = req.params;

    const response = await axios.delete(
      `${PYTHON_BACKEND_URL}/session/${session_id}`,
      { timeout: 5000 }
    );

    return res.status(200).json(response.data);
  } catch (err) {
    console.error("Clear session error:", err.message);
    
    if (err.response) {
      return res.status(err.response.status).json({
        error: "Failed to clear session",
        details: err.response.data,
      });
    }

    return next(err);
  }
});

/**
 * GET /api/agent/health
 * Check if Python backend is healthy
 */
router.get("/health", async (req, res) => {
  try {
    const response = await axios.get(`${PYTHON_BACKEND_URL}/health`, {
      timeout: 3000,
    });

    return res.status(200).json({
      status: "ok",
      python_backend: response.data,
      backend_url: PYTHON_BACKEND_URL,
    });
  } catch (err) {
    return res.status(503).json({
      status: "error",
      error: "Python backend unreachable",
      backend_url: PYTHON_BACKEND_URL,
      message: err.message,
    });
  }
});

module.exports = router;
