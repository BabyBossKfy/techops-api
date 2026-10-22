"""Routes de gestion des incidents techniques."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident, Role, Severity, Status, User
from app.schemas import IncidentCreate, IncidentOut, IncidentStatusUpdate
from app.security import get_current_user, require_roles

router = APIRouter(prefix="/incidents", tags=["Incidents"])


def _get_incident_or_404(db: Session, incident_id: int) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident introuvable")
    return incident


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    status: Status | None = None,
    severity: Severity | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[Incident]:
    stmt = select(Incident).order_by(Incident.created_at.desc(), Incident.id.desc())
    if status is not None:
        stmt = stmt.where(Incident.status == status)
    if severity is not None:
        stmt = stmt.where(Incident.severity == severity)
    return list(db.scalars(stmt.offset(offset).limit(limit)))


@router.post("", response_model=IncidentOut, status_code=201)
def create_incident(
    data: IncidentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Incident:
    incident = Incident(**data.model_dump(), reporter_id=user.id)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Incident:
    return _get_incident_or_404(db, incident_id)


@router.patch("/{incident_id}/status", response_model=IncidentOut)
def update_status(
    incident_id: int,
    data: IncidentStatusUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(Role.SUPERVISEUR, Role.ADMIN)),
) -> Incident:
    incident = _get_incident_or_404(db, incident_id)
    incident.status = data.status
    db.commit()
    db.refresh(incident)
    return incident


@router.delete("/{incident_id}", status_code=204)
def delete_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(Role.ADMIN)),
) -> None:
    incident = _get_incident_or_404(db, incident_id)
    db.delete(incident)
    db.commit()
