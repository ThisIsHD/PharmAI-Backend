import axios from "axios";

export const callHFModel = async (input) => {
  try {
    const response = await axios.post(
      process.env.HF_MODEL_URL,   // you will add this in .env later
      { input },
      {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${process.env.HF_API_KEY || ""}`,
        },
      }
    );

    return response.data;
  } catch (error) {
    console.error("HF model error:", error.message);
    throw error;
  }
};
