"""
Keystone Bid Tracker - Data Models
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Customer:
    id: int = 0
    name: str = ""
    active: int = 1
    created_at: str = ""


@dataclass
class BidRevision:
    id: int = 0
    bid_id: int = 0
    revision_no: int = 1
    revision_date: str = ""
    bid_total: float = 0.0
    solid_surf_sf: float = 0.0
    stone_sf: float = 0.0
    reason: str = ""
    created_at: str = ""


@dataclass
class BidCustomer:
    id: int = 0
    bid_id: int = 0
    customer_id: int = 0


@dataclass
class Bid:
    id: int = 0
    bid_name: str = ""
    estimator: str = ""
    original_bid_date: str = ""
    status: str = "PENDING"
    won_customer_id: Optional[int] = None
    notes: str = ""
    created_at: str = ""
    # Joined fields from queries
    bid_total: float = 0.0
    solid_surf_sf: float = 0.0
    stone_sf: float = 0.0
    revision_no: int = 1
    customer_names: str = ""
