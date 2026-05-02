import csv
import hashlib
import json
import os
from typing import List

import aiofiles
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_session
from models import Dataset, Experiment
from schemas import CreateDataset, DatasetResponse

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetResponse)
async def create_dataset(payload: CreateDataset, db: Session = Depends(get_session)):
    data = Dataset(
        name=payload.name,
        description=payload.description,
        file_path=payload.file_path,
    )
    if not os.path.exists(payload.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    if not payload.file_path.endswith((".json", ".csv")):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format (only .json or .csv allowed)",
        )
    try:
        async with aiofiles.open(payload.file_path, mode="rb") as f:
            content_bytes = await f.read()
        data.checksum = hashlib.sha256(content_bytes).hexdigest()
        content = content_bytes.decode("utf-8")

        if payload.file_path.endswith(".json"):
            parsed = json.loads(content)
            data.num_samples = len(parsed)
        elif payload.file_path.endswith(".csv"):
            reader = csv.reader(content.splitlines())
            data.num_samples = sum(1 for _ in reader) - 1

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process dataset file: {str(e)}",
        )
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("", response_model=List[DatasetResponse])
def list_datasets(
    skip: int = 0, limit: int = 50, db: Session = Depends(get_session)
):
    datasets = db.query(Dataset).offset(skip).limit(limit).all()
    return [
        DatasetResponse(
            id=dataset.id,
            name=dataset.name,
            file_path=dataset.file_path,
            num_samples=dataset.num_samples,
            created_at=dataset.created_at,
            checksum=dataset.checksum,
        )
        for dataset in datasets
    ]


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_session)):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(404, "Dataset not found")
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        file_path=dataset.file_path,
        description=dataset.description,
        num_samples=dataset.num_samples,
        created_at=dataset.created_at,
        checksum=dataset.checksum,
    )


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_session)):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(404, "Dataset not found")
    ref_count = (
        db.query(Experiment).filter(Experiment.dataset_id == dataset_id).count()
    )
    if ref_count > 0:
        raise HTTPException(
            400, "Cannot delete dataset that is referenced by experiments."
        )
    db.delete(dataset)
    db.commit()
    return {"success": True, "dataset_id": dataset_id}
