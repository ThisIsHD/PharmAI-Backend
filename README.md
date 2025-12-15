# PharmAI Backend 

A **Node.js + Express backend** powering the PharmAI platform. This service acts as the core API layer and an **ML inference gateway** that forwards requests to a Dockerised Hugging Face model.

---

##  Features

- RESTful APIs using **Express.js**
- **MVC-style folder structure** (routes, controllers, models)
- MongoDB integration (via Mongoose)
- External ML model integration (Hugging Face – Dockerised)
- Environment-based configuration
- Production-ready structure for deployment (Railway / Render / AWS)

---

##  Project Structure

```
PHARMAI-BACKEND/
│── controllers/        # Business logic for each route
│── models/             # Mongoose schemas
│── routes/             # API route definitions
│── services/           # External services (HF ML model, APIs)
│   └── hfService.js
│── db.js               # MongoDB connection
│── server.js           # App entry point
│── .env                # Environment variables
│── .gitignore
│── package.json
│── package-lock.json
```

---

##  Tech Stack

- **Runtime:** Node.js
- **Framework:** Express.js
- **Database:** MongoDB + Mongoose
- **ML Inference:** Hugging Face (Docker container)
- **HTTP Client:** Axios
- **Config:** dotenv

---

##  Installation & Setup

###  Clone the Repository

```bash
git clone https://github.com/your-username/pharmai-backend.git
cd pharmai-backend
```

---

###  Install Dependencies

```bash
npm install
```

---

###  Environment Variables

Create a `.env` file in the root:

```
PORT=5000
MONGO_URI=mongodb://localhost:27017/pharmai
HF_MODEL_URL=https://your-hf-space.hf.space/predict
HF_API_KEY=your_huggingface_token
```

> ⚠️ `HF_API_KEY` is optional if your Hugging Face space is public.

---

###  Start the Server

```bash
npm start
```

or (with nodemon):

```bash
npm run dev
```

Server will run at:

```
http://localhost:5000
```

---

##  Database Connection

MongoDB is initialized in `db.js` and connected in `server.js`.

```js
import mongoose from "mongoose";

const connectDB = async () => {
  await mongoose.connect(process.env.MONGO_URI);
  console.log("MongoDB Connected");
};

export default connectDB;
```

---

##  ML Model Integration (Hugging Face)

The backend does **NOT** run ML locally.
Instead, it forwards inference requests to a **Dockerised Hugging Face model API**.

### Flow

```
Frontend → Node.js Backend → Hugging Face ML API → Backend → Frontend
```

### Service Layer

`services/hfService.js`

```js
import axios from "axios";

export const callHFModel = async (payload) => {
  const response = await axios.post(
    process.env.HF_MODEL_URL,
    payload,
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.HF_API_KEY}`
      }
    }
  );

  return response.data;
};
```

---

##  API Routes

###  ML Prediction

**POST** `/api/model/predict`

#### Request Body

```json
{
  "input": "sample medical text"
}
```

#### Response

```json
{
  "success": true,
  "result": {
    "prediction": "example output"
  }
}
```

---

##  Testing with Postman / cURL

```bash
curl -X POST http://localhost:5000/api/model/predict \
  -H "Content-Type: application/json" \
  -d '{"input": "test text"}'
```

---

### Required Config in Production

- Add `.env` variables in hosting dashboard
- Ensure CORS is enabled
- Use HTTPS Hugging Face endpoint

---

##  Security Best Practices

- Do NOT expose Hugging Face API key to frontend
- Always route ML calls via backend
- Add request validation before inference
- Add rate-limiting for `/predict`

---

##  Future Enhancements

- Authentication & role-based access
- Request logging
- Caching ML responses
- Async job queue for long-running inference
- Swagger API documentation

---

##  Author

**PharmAI Backend**  
Built for scalable AI-driven healthcare applications.

---

##  Contribution

PRs are welcome! Feel free to fork and improve the project.

---

##  License

MIT License


