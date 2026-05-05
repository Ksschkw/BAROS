from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.endpoints import auth, users, services, jobs, applications, vouches, disputes, messages, categories, location
from .core.database import init_db, engine, Base


app = FastAPI(title="BAROS API", version="1.0.0")
# app = FastAPI(
#     title="BAROS API",
#     version="1.0.0",
#     swagger_ui_init_oauth={
#         "usePkceWithAuthorizationCodeGrant": True,
#     },
#     # Add this to trigger the padlock icon
#     openapi_tags=[],
#     # Actually the simplest way:
# )

@app.on_event("startup")
async def on_startup():
    await init_db()

# CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173", "https://baros.onrender.com", "http://127.0.0.1:5500/*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # React dev server
        "http://localhost:5500",   # test HTML
        "http://127.0.0.1:5500",  # test HTML (IP variant)
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(services.router, prefix="/api/v1/services", tags=["services"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(vouches.router, prefix="/api/v1/vouches", tags=["vouches"])
app.include_router(disputes.router, prefix="/api/v1/disputes", tags=["disputes"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["messages"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(location.router, prefix="/api/v1/location", tags=["location"])

from .api.v1.endpoints import admin

app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])