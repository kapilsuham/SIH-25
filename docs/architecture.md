# System Architecture

## Overview

The FRA-DSS is a distributed system built on a microservices-inspired architecture, containerized with Docker for scalability and ease of deployment. The system is composed of three main services: a React frontend, a FastAPI backend, and a PostgreSQL database.

## Diagram

![High-Level Architecture Diagram](https://mermaid.ink/svg/...)
*(Note: You would replace this URL with a generated one from the mermaid chart we discussed earlier)*

## Component Details

### 1. Frontend (React Application)
- **Purpose:** Provides the user interface for interacting with the system.
- **Framework:** React 18
- **Key Libraries:**
  - `React Router` for navigation
  - `React Leaflet` for map visualization
  - `Axios` for HTTP requests to the backend API
  - `Recharts` for data visualization
- **State Management:** React Context API and Hooks (useState, useEffect)

### 2. Backend (FastAPI Application)
- **Purpose:** Serves as the central API, handling business logic, database interactions, and serving ML model predictions.
- **Framework:** FastAPI
- **Key Features:**
  - Automatic Interactive API Documentation (Swagger UI)
  - Data Validation via Pydantic models
  - Asynchronous request handling
  - JWT Token Authentication
- **Database ORM:** SQLAlchemy with GeoAlchemy2 for spatial queries.

### 3. Database (PostgreSQL with PostGIS)
- **Purpose:** Stores all application data, including user information, FRA claims, and most importantly, geospatial data.
- **Extension:** PostGIS is critical for storing and querying geographic objects (points, polygons).
- **Tables:** `users`, `fra_claims`, `communities`, `schemes`, `recommendations`.

### 4. AI/ML Module
- **Integration:** The trained models are packaged and loaded by the FastAPI backend.
- **Image Segmentation:** A TensorFlow/Keras U-Net model for analyzing satellite imagery. It is called via a dedicated API endpoint (`/api/v1/analyze-parcel`).
- **Scheme Recommendation:** An XGBoost classifier model that recommends schemes. It is called via the (`/api/v1/recommend-schemes`) endpoint.

## Data Flow

1.  **User** interacts with the React frontend (e.g., views a map, submits a community profile).
2.  **Frontend** makes an HTTP request to the relevant endpoint on the FastAPI backend.
3.  **Backend** receives the request, validates the data, and performs any necessary database operations using SQLAlchemy.
4.  **For ML requests,** the backend loads the appropriate model and performs inference on the input data.
5.  **Backend** formulates a response (JSON data, map tiles, prediction results) and sends it back to the frontend.
6.  **Frontend** receives the response and updates the UI accordingly.

## Deployment Architecture

The system is designed to be containerized using Docker:
- Each service (frontend, backend, database) runs in its own container.
- `docker-compose.yml` defines the services, their build configurations, and the network that allows them to communicate.
- The frontend is built as a static bundle and served via an Nginx web server in its container.
- The backend is served via Uvicorn (an ASGI server) in its container.
- All environment variables (e.g., database connection strings, secret keys) are injected via Docker Compose, keeping configuration separate from code.