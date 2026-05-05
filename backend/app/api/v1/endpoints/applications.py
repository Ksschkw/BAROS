from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.dependencies import get_db, get_current_user
from ....crud.application import (
    get_application_by_id,
    create_application,
    delete_application,
    get_applications_for_job,
)
from ....crud.job import get_job_by_id
from ....schemas.application import ApplicationCreate, ApplicationOut
from ....models.user import User
import uuid

router = APIRouter()


@router.post("/", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def apply(
    app_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await get_job_by_id(db, app_data.job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status != "open":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is not open for applications")
    application = await create_application(db, current_user.id, app_data)
    return application


@router.get("/job/{job_id}", response_model=list[ApplicationOut])
async def list_applications_for_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    applications = await get_applications_for_job(db, job_id)
    return applications


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw_application(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app = await get_application_by_id(db, application_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if app.applicant_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only withdraw your own application")
    await delete_application(db, app)
    return None