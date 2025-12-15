const express = require("express");
const connectDB = require("./db");
require("dotenv").config();

const app = express();
app.use(express.json());


connectDB();

app.get("/", (req, res) => {
  res.send("Backend running, MongoDB connected!");
});

app.listen(3000, () => console.log("Server running on port 3000"));
