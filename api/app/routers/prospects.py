from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user, require_superuser
from app.models.client import Client
from app.models.prospect import (
    PIPELINE_STAGE_ORDER,
    PIPELINE_STAGES,
    TERMINAL_STAGES,
    Prospect,
)
from app.models.user import User
from app.schemas import (
    TERMINAL_PIPELINE_STAGES,
    VALID_PIPELINE_STAGES,
    ClientOut,
    ProspectCreate,
    ProspectListResponse,
    ProspectOut,
    ProspectStageChange,
    ProspectStageChangeResponse,
    ProjectOut,
    ProspectPromoteResponse,
    ProspectUpdate,
)
from app.services.pipeline_service import auto_scaffold_onboarding_project, promote_prospect_to_client


async def _enrich_client_id(db, prospect) -> uuid.UUID | None:
    """Look up the client_id for a given prospect, if any."""
    return await db.scalar(select(Client.id).where(Client.prospect_id == prospect.id))


async def _enrich_list_client_ids(db, prospects: list[Prospect]) -> dict[uuid.UUID, uuid.UUID | None]:
    """Batch-load client_ids for a list of prospects. Returns a dict of prospect_id → client_id."""
    ids = [p.id for p in prospects]
    if not ids:
        return {}
    rows = (await db.execute(select(Client.prospect_id, Client.id).where(Client.prospect_id.in_(ids)))).all()
    return {r.prospect_id: r.id for r in rows}

router = APIRouter(prefix="/v1/prospects", tags=["prospects"])


@router.get("", response_model=ProspectListResponse)
async def list_prospects(
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    stage: str | None = Query(default=None, max_length=20),
    source: str | None = Query(default=None, max_length=30),
    created_by: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    base = select(Prospect)
    if stage:
        if stage not in VALID_PIPELINE_STAGES:
            raise HTTPException(status_code=422, detail=f"Invalid stage filter: {stage}")
        base = base.where(Prospect.pipeline_stage == stage)
    if source:
        base = base.where(Prospect.source == source)
    if created_by:
        base = base.where(Prospect.created_by == created_by)

    total = (await db.scalar(base.with_only_columns(func.count()).order_by(None))) or 0

    q = base.order_by(Prospect.created_at.desc()).offset(offset).limit(limit)
    result = await db.scalars(q)
    rows = list(result.all())
    client_map = await _enrich_list_client_ids(db, rows)
    return ProspectListResponse(
        items=[
            ProspectOut.model_validate(r).model_copy(update={"client_id": client_map.get(r.id)})
            for r in rows
        ],
        total=total,
        has_more=(offset + len(rows)) < total,
    )


@router.post("", response_model=ProspectOut, status_code=status.HTTP_201_CREATED)
async def create_prospect(
    body: ProspectCreate,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = Prospect(
        company_name=body.company_name.strip(),
        pipeline_stage=body.pipeline_stage,
        pipeline_value=body.pipeline_value,
        source=body.source.strip() if body.source else None,
        first_contact_date=body.first_contact_date,
        notes=body.notes.strip() if body.notes else None,
        created_by=user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ProspectOut.model_validate(row)


@router.get("/{prospect_id}", response_model=ProspectOut)
async def get_prospect(
    prospect_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Prospect, prospect_id)
    if not row:
        raise HTTPException(status_code=404, detail="Prospect not found")
    client_id = await _enrich_client_id(db, row)
    return ProspectOut.model_validate(row).model_copy(update={"client_id": client_id})


@router.patch("/{prospect_id}", response_model=ProspectOut)
async def update_prospect(
    prospect_id: uuid.UUID,
    body: ProspectUpdate,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Prospect, prospect_id)
    if not row:
        raise HTTPException(status_code=404, detail="Prospect not found")
    if body.company_name is not None:
        row.company_name = body.company_name.strip()
    if body.pipeline_stage is not None:
        row.pipeline_stage = body.pipeline_stage
    if body.pipeline_value is not None:
        row.pipeline_value = body.pipeline_value
    if body.source is not None:
        row.source = body.source.strip() if body.source else None
    if body.first_contact_date is not None:
        row.first_contact_date = body.first_contact_date
    if body.notes is not None:
        row.notes = body.notes.strip() if body.notes else None
    await db.commit()
    await db.refresh(row)
    return ProspectOut.model_validate(row)


@router.delete("/{prospect_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prospect(
    prospect_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Prospect, prospect_id)
    if not row:
        raise HTTPException(status_code=404, detail="Prospect not found")
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{prospect_id}/stage", response_model=ProspectStageChangeResponse)
async def transition_prospect_stage(
    prospect_id: uuid.UUID,
    body: ProspectStageChange,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Prospect, prospect_id)
    if not row:
        raise HTTPException(status_code=404, detail="Prospect not found")
    if row.pipeline_stage in TERMINAL_STAGES:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot transition from terminal stage '{row.pipeline_stage}'",
        )

    current_stage = row.pipeline_stage
    target_stage = body.stage

    if target_stage == current_stage:
        raise HTTPException(
            status_code=422,
            detail=f"Prospect is already in stage '{current_stage}'",
        )

    stage_index = {s: i for i, s in enumerate(PIPELINE_STAGE_ORDER)}
    current_idx = stage_index[current_stage]
    target_idx = stage_index[target_stage]

    if target_stage == "lost":
        pass
    elif target_stage == "won":
        if current_stage != "negotiating":
            raise HTTPException(
                status_code=422,
                detail="Can only transition to 'won' from 'negotiating'",
            )
    elif target_idx < current_idx:
        pass
    elif target_idx == current_idx + 1:
        pass
    else:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot skip stages from '{current_stage}' to '{target_stage}'",
        )

    row.pipeline_stage = target_stage

    promoted_client = None
    promoted_project = None
    if target_stage == "won":
        client = await promote_prospect_to_client(db, row)
        await db.flush()
        await db.refresh(client)
        promoted_client = ClientOut.model_validate(client)
        project = await auto_scaffold_onboarding_project(db, client, row, user.id)
        await db.flush()
        await db.refresh(project)
        promoted_project = ProjectOut.model_validate(project)

    await db.commit()
    await db.refresh(row)
    client_id = await _enrich_client_id(db, row)
    return ProspectStageChangeResponse(
        **ProspectOut.model_validate(row).model_copy(update={"client_id": client_id}).model_dump(),
        promoted_client=promoted_client,
        promoted_project=promoted_project,
    )


@router.post("/{prospect_id}/promote", response_model=ProspectPromoteResponse)
async def promote_prospect(
    prospect_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    _admin: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Promote a won prospect to a client and auto-scaffold an onboarding project.

    Only works when:
      - prospect is in 'won' stage
      - no client record already exists for this prospect
    Returns the newly created Client and Project records.
    """
    row = await db.get(Prospect, prospect_id)
    if not row:
        raise HTTPException(status_code=404, detail="Prospect not found")
    if row.pipeline_stage != "won":
        raise HTTPException(
            status_code=422,
            detail="Only prospects in 'Won' stage can be promoted to client",
        )
    existing_client_id = await _enrich_client_id(db, row)
    if existing_client_id:
        raise HTTPException(
            status_code=409,
            detail="This prospect already has a client record",
        )
    client = await promote_prospect_to_client(db, row)
    await db.flush()
    await db.refresh(client)
    project = await auto_scaffold_onboarding_project(db, client, row, user.id)
    await db.flush()
    await db.refresh(project)
    await db.commit()
    return ProspectPromoteResponse(
        client=ClientOut.model_validate(client),
        project=ProjectOut.model_validate(project),
    )
