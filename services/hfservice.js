// services/hfservice.js
const axios = require("axios");

/**
 * Calls your HuggingFace model endpoint.
 * Env:
 *  - HF_MODEL_URL: required
 *  - HF_API_TOKEN: optional (if private/protected endpoint)
 */
async function callHFModel(payload) {
  const hfUrl = process.env.HF_MODEL_URL;
  if (!hfUrl) {
  const e = new Error("HF_MODEL_URL is missing in .env");
  e.statusCode = 503; // Service Unavailable
  throw e;
  }

  const headers = {
    "Content-Type": "application/json",
  };

  if (process.env.HF_API_TOKEN) {
    headers.Authorization = `Bearer ${process.env.HF_API_TOKEN}`;
  }

  try {
    const resp = await axios.post(hfUrl, payload, { headers });
    return resp.data;
  } catch (err) {
    const status = err?.response?.status || 500;
    const data = err?.response?.data || { message: err.message };
    const e = new Error(`HF call failed (${status}): ${JSON.stringify(data)}`);
    e.statusCode = status;
    throw e;
  }
}

module.exports = { callHFModel };
