import ipaddress

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import IpRecord
from ..scanner import scan_subnet

router = APIRouter(
    prefix="/api/scan",
    tags=["scan"],
    dependencies=[Depends(get_current_user)],
)


class ScanRequest(BaseModel):
    cidr: str = Field(..., description="网段，如 192.168.1.0/24")
    timeout_ms: int = Field(800, ge=200, le=3000)
    concurrency: int = Field(64, ge=1, le=128)


class ScanHostOut(BaseModel):
    ip_address: str
    alive: bool
    latency_ms: int | None = None
    record_id: int | None = None
    hostname: str | None = None
    assignee: str | None = None
    status: str | None = None
    registered: bool = False


class ScanResultOut(BaseModel):
    cidr: str
    scanned: int
    alive: int
    offline: int
    duration_ms: int
    hosts: list[ScanHostOut]


@router.post("/subnet", response_model=ScanResultOut)
def scan_network(payload: ScanRequest, db: Session = Depends(get_db)):
    try:
        raw = scan_subnet(
            payload.cidr,
            timeout_ms=payload.timeout_ms,
            concurrency=payload.concurrency,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        network = ipaddress.ip_network(raw["cidr"], strict=False)
    except ValueError:
        network = None

    records = db.query(IpRecord).all()
    record_map: dict[str, IpRecord] = {}
    for record in records:
        try:
            ip_obj = ipaddress.ip_address(record.ip_address)
        except ValueError:
            continue
        if network is None or ip_obj in network:
            record_map[str(ip_obj)] = record

    hosts: list[ScanHostOut] = []
    for item in raw["hosts"]:
        record = record_map.get(item["ip_address"])
        hosts.append(
            ScanHostOut(
                ip_address=item["ip_address"],
                alive=item["alive"],
                latency_ms=item["latency_ms"],
                record_id=record.id if record else None,
                hostname=record.hostname if record else None,
                assignee=record.assignee if record else None,
                status=record.status if record else None,
                registered=record is not None,
            )
        )

    return ScanResultOut(
        cidr=raw["cidr"],
        scanned=raw["scanned"],
        alive=raw["alive"],
        offline=raw["offline"],
        duration_ms=raw["duration_ms"],
        hosts=hosts,
    )
