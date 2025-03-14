from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Category:
    """Модель категории eBay"""

    category_id: str
    category_name: str
    parent_id: Optional[str] = None
    level: int = 0
    leaf: bool = False
    children: List["Category"] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Category":
        """Создание объекта Category из словаря"""
        return cls(
            category_id=data.get("categoryId", ""),
            category_name=data.get("categoryName", ""),
            parent_id=data.get("parentCategoryId"),
            level=data.get("categoryLevel", 0),
            leaf=data.get("leafCategory", False),
            children=[],
        )


@dataclass
class Item:
    """Модель товара eBay"""

    item_id: str
    title: str
    price: float
    currency: str
    condition: str = "Unknown"
    image_url: Optional[str] = None
    listing_url: Optional[str] = None
    location: Optional[str] = None
    shipping_cost: Optional[float] = None
    seller_username: Optional[str] = None
    seller_feedback: Optional[float] = None
    listing_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Item":
        """Создание объекта Item из словаря"""
        price_info = data.get("price", {})
        seller_info = data.get("seller", {})
        image_urls = data.get("image", {}).get("imageUrl", [])

        return cls(
            item_id=data.get("itemId", ""),
            title=data.get("title", ""),
            price=float(price_info.get("value", 0)),
            currency=price_info.get("currency", "USD"),
            condition=data.get("condition", ""),
            image_url=image_urls[0] if image_urls else None,
            listing_url=data.get("itemWebUrl"),
            location=data.get("itemLocation", {}).get("country"),
            shipping_cost=(
                float(
                    data.get("shippingOptions", [{}])[0]
                    .get("shippingCost", {})
                    .get("value", 0)
                )
                if data.get("shippingOptions")
                else None
            ),
            seller_username=seller_info.get("username"),
            seller_feedback=seller_info.get("feedbackPercentage"),
            listing_type=data.get("listingType"),
            start_time=(
                datetime.fromisoformat(
                    data.get("listingStartDate").replace("Z", "+00:00")
                )
                if data.get("listingStartDate")
                else None
            ),
            end_time=(
                datetime.fromisoformat(
                    data.get("listingEndDate").replace("Z", "+00:00")
                )
                if data.get("listingEndDate")
                else None
            ),
            raw_data=data,
        )


@dataclass
class SearchResult:
    """Модель результатов поиска"""

    total: int
    items: List[Item]
    next_page_token: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        """Создание объекта SearchResult из словаря"""
        items = []
        for item_data in data.get("itemSummaries", []):
            items.append(Item.from_dict(item_data))

        return cls(
            total=data.get("total", 0), items=items, next_page_token=data.get("next")
        )
