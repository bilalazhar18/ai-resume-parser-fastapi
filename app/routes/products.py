
from fastapi import APIRouter
from app.schemas.products import ProductModel

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.post("")
def create_product(product: ProductModel):
    return {
        "message": "Product created successfully",
        "name": product.name,
        "price": product.price,
        "color": product.color
    }
