import ipaddress

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import IpRecord
from ..schemas import (
    IpRecordCreate,
    IpRecordOut,
    IpRecordUpdate,
    PaginatedIpRecords,
    StatsOut,
    SubnetHostOut,
    SubnetMapOut,
)

router = APIRouter(prefix="/api/ip-records", tags=["ip-records"])

MAX_SUBNET_HOSTS = 1024


@router.get("", response_model=PaginatedIpRecords)
def list_ip_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None, description="搜索 IP / 主机名 / 使用人 / 部门"),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(IpRecord)

    if keyword:
        like = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                IpRecord.ip_address.ilike(like),
                IpRecord.hostname.ilike(like),
                IpRecord.assignee.ilike(like),
                IpRecord.department.ilike(like),
                IpRecord.location.ilike(like),
                IpRecord.cidr.ilike(like),
            )
        )

    if status:
        query = query.filter(IpRecord.status == status)

    total = query.count()
    items = (
        query.order_by(IpRecord.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedIpRecords(total=total, items=items)


@router.get("/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    rows = (
        db.query(IpRecord.status, func.count(IpRecord.id))
        .group_by(IpRecord.status)
        .all()
    )
    counts = {status: count for status, count in rows}
    total = sum(counts.values())
    return StatsOut(
        total=total,
        available=counts.get("available", 0),
        in_use=counts.get("in_use", 0),
        reserved=counts.get("reserved", 0),
        disabled=counts.get("disabled", 0),
    )


@router.get("/cidrs", response_model=list[str])
def list_cidrs(db: Session = Depends(get_db)):
    rows = (
        db.query(IpRecord.cidr)
        .filter(IpRecord.cidr.is_not(None), IpRecord.cidr != "")
        .distinct()
        .order_by(IpRecord.cidr.asc())
        .all()
    )
    return [row[0] for row in rows]


@router.get("/subnet-map", response_model=SubnetMapOut)
def get_subnet_map(
    cidr: str = Query(..., description="网段，如 192.168.1.0/24"),
    db: Session = Depends(get_db),
):
    try:
        network = ipaddress.ip_network(cidr.strip(), strict=False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="网段格式无效") from exc

    if network.version != 4:
        raise HTTPException(status_code=400, detail="仅支持 IPv4 网段")

    hosts = list(network.hosts())
    if len(hosts) > MAX_SUBNET_HOSTS:
        raise HTTPException(
            status_code=400,
            detail=f"网段主机数过多（最多支持 {MAX_SUBNET_HOSTS} 个）",
        )

    records = db.query(IpRecord).all()
    record_map: dict[str, IpRecord] = {}
    for record in records:
        try:
            ip_obj = ipaddress.ip_address(record.ip_address)
        except ValueError:
            continue
        if ip_obj in network:
            record_map[str(ip_obj)] = record

    host_items: list[SubnetHostOut] = []
    counts = {
        "free": 0,
        "available": 0,
        "in_use": 0,
        "reserved": 0,
        "disabled": 0,
    }

    for index, host in enumerate(hosts, start=1):
        ip_str = str(host)
        record = record_map.get(ip_str)
        if record:
            status = record.status
            host_items.append(
                SubnetHostOut(
                    ip_address=ip_str,
                    host_num=index,
                    status=status,
                    record_id=record.id,
                    hostname=record.hostname,
                    assignee=record.assignee,
                )
            )
        else:
            status = "free"
            host_items.append(
                SubnetHostOut(
                    ip_address=ip_str,
                    host_num=index,
                    status=status,
                )
            )
        counts[status] = counts.get(status, 0) + 1

    return SubnetMapOut(
        cidr=str(network),
        network_address=str(network.network_address),
        broadcast_address=str(network.broadcast_address),
        prefixlen=network.prefixlen,
        host_count=len(hosts),
        free=counts["free"],
        available=counts["available"],
        in_use=counts["in_use"],
        reserved=counts["reserved"],
        disabled=counts["disabled"],
        hosts=host_items,
    )


@router.get("/{record_id}", response_model=IpRecordOut)
def get_ip_record(record_id: int, db: Session = Depends(get_db)):
    record = db.get(IpRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.post("", response_model=IpRecordOut, status_code=201)
def create_ip_record(payload: IpRecordCreate, db: Session = Depends(get_db)):
    exists = (
        db.query(IpRecord)
        .filter(IpRecord.ip_address == payload.ip_address)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="该 IP 地址已存在")

    record = IpRecord(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{record_id}", response_model=IpRecordOut)
def update_ip_record(
    record_id: int,
    payload: IpRecordUpdate,
    db: Session = Depends(get_db),
):
    record = db.get(IpRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    data = payload.model_dump(exclude_unset=True)
    if "ip_address" in data and data["ip_address"] != record.ip_address:
        exists = (
            db.query(IpRecord)
            .filter(
                IpRecord.ip_address == data["ip_address"],
                IpRecord.id != record_id,
            )
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="该 IP 地址已存在")

    for key, value in data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=204)
def delete_ip_record(record_id: int, db: Session = Depends(get_db)):
    record = db.get(IpRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
