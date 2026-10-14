from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

IpStatus = Literal["available", "in_use", "reserved", "disabled"]


class IpRecordBase(BaseModel):
    ip_address: str = Field(..., min_length=7, max_length=45, description="IP 地址")
    cidr: str | None = Field(None, max_length=50, description="网段，如 192.168.1.0/24")
    status: IpStatus = "in_use"
    hostname: str | None = Field(None, max_length=100)
    mac_address: str | None = Field(None, max_length=50)
    assignee: str | None = Field(None, max_length=100, description="使用人")
    department: str | None = Field(None, max_length=100, description="部门")
    location: str | None = Field(None, max_length=100, description="位置")
    description: str | None = None

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        value = value.strip()
        parts = value.split(".")
        if len(parts) != 4:
            raise ValueError("请输入有效的 IPv4 地址")
        try:
            if not all(0 <= int(p) <= 255 for p in parts):
                raise ValueError
        except ValueError as exc:
            raise ValueError("请输入有效的 IPv4 地址") from exc
        return value


class IpRecordCreate(IpRecordBase):
    pass


class IpRecordUpdate(BaseModel):
    ip_address: str | None = Field(None, min_length=7, max_length=45)
    cidr: str | None = Field(None, max_length=50)
    status: IpStatus | None = None
    hostname: str | None = Field(None, max_length=100)
    mac_address: str | None = Field(None, max_length=50)
    assignee: str | None = Field(None, max_length=100)
    department: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=100)
    description: str | None = None

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return IpRecordBase.validate_ip(value)


class IpRecordOut(IpRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PaginatedIpRecords(BaseModel):
    total: int
    items: list[IpRecordOut]


class StatsOut(BaseModel):
    total: int
    available: int
    in_use: int
    reserved: int
    disabled: int


class SubnetHostOut(BaseModel):
    ip_address: str
    host_num: int
    status: str
    record_id: int | None = None
    hostname: str | None = None
    assignee: str | None = None


class SubnetMapOut(BaseModel):
    cidr: str
    network_address: str
    broadcast_address: str
    prefixlen: int
    host_count: int
    free: int
    available: int
    in_use: int
    reserved: int
    disabled: int
    hosts: list[SubnetHostOut]
