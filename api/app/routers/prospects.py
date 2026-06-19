from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
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
    ProspectCreate,
    ProspectListResponse,
    ProspectOut,
    ProspectStageChange,
    ProspectUpdate,
)
from app.services.pipeline_service import promote_prospect_to_client

router = APIRouter(prefix="/v1/prospects", tags=["prospects"])


@router.get("", response_model=ProspectListResponse)
async def list_prospects(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    stage: str | None = Query(default=None, max_length=20),
    source: str | None = Query(default=None, max_length=30),
    created_by: uuid.UUID | None = Query(default=None),
):
    q = select(Prospect).order_by(Prospect.created_at.desc())
    if stage:
        if stage not in VALID_PIPELINE_STAGES:
            raise HTTPException(status_code=422, detail=f"Invalid stage filter: {stage}")
        q = q.where(Prospect.pipeline_stage == stage)
    if source:
        q = q.where(Prospect.source == source)
    if created_by:
        q = q.where(Prospect.created_by == created_by)
    result = await db.scalars(q)
    rows = list(result.all())
    return ProspectListResponse(items=[ProspectOut.model_validate(r) for r in rows])


@router.post("", response_model=ProspectOut, status_code=status.HTTP_201_CREATED)
async def create_prospect(
    body: ProspectCreate,
    user: Annotated[User, Depends(get_current_user)],
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
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Prospect, prospect_id)
    if not row:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return ProspectOut.model_validate(row)


@router.patch("/{prospect_id}", response_model=ProspectOut)
async def update_prospect(
    prospect_id: uuid.UUID,
    body: ProspectUpdate,
    user: Annotated[User, Depends(get_current_user)],
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
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(Prospect, prospect_id)
    if not row:
        raise HTTPException(status_code=404, detail="Prospect not found")
    await db.delete(row)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{prospect_id}/stage", response_model=ProspectOut)
async def transition_prospect_stage(
    prospect_id: uuid.UUID,
    body: ProspectStageChange,
    user: Annotated[User, Depends(get_current_user)],
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
        # 'lost' is terminal and can be reached from any non-terminal stage.
        pass
    elif target_stage == "won":
        # 'won' is terminal and must follow 'negotiating'.
        if current_stage != "negotiating":
            raise HTTPException(
                status_code=422,
                detail="Can only transition to 'won' from 'negotiating'",
            )
    else:
        # Non-terminal stages must advance exactly one step at a time.
        if target_idx != current_idx + 1:
            raise HTTPException(
                status_code=422,
                detail=f"Cannot skip stages from '{current_stage}' to '{target_stage}'",
            )

    row.pipeline_stage = target_stage

    if target_stage == "won":
        await promote_prospect_to_client(db, row)

    await db.commit()
    await db.refresh(row)
    return ProspectOut.model_validate(row)
