import express from "express";
import { callHFModel } from "./services/hfService.js";

const router = express.Router();

router.post("/predict", async (req, res) => {
  try {
    const result = await callHFModel(req.body);
    res.json({ success: true, result });
  } catch (error) {
    res.status(500).json({ success: false, error: "Inference failed" });
  }
});

export default router;
