// routes/modelRoutes.js
const express = require("express");
const router = express.Router();

// Correct relative path: routes/ -> services/
const { callHFModel } = require("../services/hfservice");

/**
 * POST /api/model/predict
 * Body: { inputs: ..., parameters?: ... }
 */
router.post("/predict", async (req, res, next) => {
  try {
    const result = await callHFModel(req.body);
    return res.status(200).json(result);
  } catch (err) {
    return next(err);
  }
});

module.exports = router;
