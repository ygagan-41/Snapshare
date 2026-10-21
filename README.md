# 📸 SnapShare — Photo/Video Sharing Application

SnapShare is a photo-sharing web application that allows users to upload photos and explore a feed of shared posts. It uses **Streamlit** for the frontend, **FastAPI** for the backend, and **ImageKit** for image storage and delivery.

The project demonstrates how to build and deploy a full-stack Python application by integrating a user interface, REST API, authentication, database operations, and cloud-based image handling.

**Try SnapShare here:** [Open SnapShare](https://snapshare-z90.streamlit.app/)

## ✨ Features

- 📷 **Photo Upload:** Upload images with captions.
- 📰 **Photo Feed:** Retrieve and display shared posts.
- 🔐 **User Authentication:** Manage user authentication using FastAPI Users.
- ☁️ **Cloud Image Storage:** Upload and serve images using ImageKit.
- ⚡ **REST API:** Handle frontend requests using FastAPI.
- 🗄️ **Database Integration:** Store post information and application data using SQLAlchemy and SQLite.
- 🌐 **Cloud Deployment:** Deploy the frontend and backend as separate services.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Streamlit | Frontend interface |
| FastAPI | Backend REST API |
| SQLAlchemy | Database operations and ORM |
| SQLite / aiosqlite | Database and asynchronous database access |
| FastAPI Users | Authentication and user management |
| ImageKit | Image upload, storage, and delivery |
| Uvicorn | ASGI server |
| Git & GitHub | Version control and source code hosting |
| Render | Backend deployment |
| Streamlit Community Cloud | Frontend deployment |

## 📁 Project Structure

```text
SnapShare/
│
├── app/
│   ├── __init__.py
│   ├── app.py
│   ├── images.py
│   ├── users.py
│   └── ...
│
├── frontend.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## 🔌 API Overview

The backend exposes endpoints for the application's operations.

| Endpoint | Purpose |
|---|---|
| `POST /upload` | Upload an image with a caption |
| `GET /feed` | Retrieve posts for the photo feed |
| Authentication routes | Handle user authentication through the configured FastAPI Users setup |

Refer to `/docs` on your running backend for the exact available routes, request formats, and response schemas.


## What I Learned

This project provides practical experience with:

- Building a frontend and backend using Python.
- Designing REST APIs with FastAPI.
- Integrating cloud image storage with ImageKit.
- Working with asynchronous database access.
- Implementing authentication with FastAPI Users.
- Managing secrets through environment variables.
- Connecting a frontend to a separately deployed backend.
- Deploying Python applications to cloud hosting platforms.

## 🔮 Future Improvements

- Add likes, comments, and post interactions.
- Add user profiles and profile pictures.
- Implement photo search and filtering.
- Add pagination to the feed.
- Improve image validation and upload error handling.
- Add automated tests and more robust error responses.


