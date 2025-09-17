# API Guide

## Base URL

All API endpoints are prefixed with `/api/v1`.
- **Local Development:** `http://localhost:8000/api/v1`
- **Production:** `https://your-production-domain.com/api/v1`

## Authentication

Most endpoints require authentication via JWT Bearer tokens.

1.  **Login** to `POST /api/v1/auth/login` to receive a token.
2.  **Include** the token in the header of subsequent requests:
    ```
    Authorization: Bearer <your-token>
    ```

## Key Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/login` | Login and retrieve access token | No |

### FRA Claims

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/claims` | Get a list of all FRA claims | Yes |
| `POST` | `/claims` | Create a new FRA claim | Yes |
| `GET` | `/claims/{id}` | Get a specific claim by ID | Yes |
| `PUT` | `/claims/{id}` | Update a specific claim | Yes |
| `DELETE` | `/claims/{id}` | Delete a specific claim | Yes |
| `GET` | `/claims/geojson` | **Get all claims as GeoJSON** (for maps) | Yes |

### AI/ML Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/analyze-parcel` | Analyze a satellite image (requires image file) | Yes |
| `POST` | `/recommend-schemes` | Get scheme recommendations for a community | Yes |

### Scheme Recommendations

**Request Body for `POST /recommend-schemes`:**
```json
{
  "population": 1200,
  "primary_livelihood": "agriculture",
  "state": "odisha",
  "forest_area_hectares": 450,
  "has_community_forest_rights": true
}