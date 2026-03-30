from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# ── Temporary data — acting as our database for now ──────────────
products = [
    {'id': 1, 'name': 'Wireless Mouse',      'price': 499,  'category': 'Electronics', 'in_stock': True },
    {'id': 2, 'name': 'Notebook',            'price':  99,  'category': 'Stationery',  'in_stock': True },
    {'id': 3, 'name': 'USB Hub',             'price': 799,  'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set',             'price':  49,  'category': 'Stationery',  'in_stock': True },
    {'id': 5, 'name': 'Laptop Stand',        'price': 1299, 'category': 'Electronics', 'in_stock': True },
    {'id': 6, 'name': 'Mechanical Keyboard', 'price': 2499, 'category': 'Electronics', 'in_stock': False},
    {'id': 7, 'name': 'Webcam',              'price': 1899, 'category': 'Electronics', 'in_stock': True },
]

orders = []
feedback = []

# ── Endpoint 0 — Home ────────────────────────────────────────────
@app.get('/')
def home():
    return {'message': 'Welcome to our E-commerce API'}

# ── Endpoint 1 — Return all products ─────────────────────────────
@app.get('/products')
def get_all_products():
    return {'products': products, 'total': len(products)}

# ── Product fileter ────────────────────────────────────────────
@app.get('/products/filter')
def filter_products(
    category:  str  = Query(None, description='Electronics or Stationery'),
    max_price: int  = Query(None, description='Maximum price'),
    min_price: int = Query(None, description='Minimum price'),
    in_stock:  bool = Query(None, description='True = in stock only')
):
    result = products          # start with all products

    if category:
        result = [p for p in result if p['category'] == category]

    if max_price:
        result = [p for p in result if p['price'] <= max_price]

    if in_stock is not None:
        result = [p for p in result if p['in_stock'] == in_stock]

    if min_price:
        result = [p for p in result if p['price'] >= min_price]

    return {'filtered_products': result, 'count': len(result)}

# ── Endpoint 3 — Return products of a particular category ─────────
@app.get('/products/category/{category_name}')
def get_by_category(category_name: str):
    result= [p for p in products if p['category'] == category_name]
    if not result:
        return {'error': 'No products found in this category'}
    return {'category': category_name, 'products': result, 'count': len(result)}

# ── Endpoint 4 — Return products in stock ─────────────────────────
@app.get("/products/instock") 
def get_instock():
     available = [p for p in products if p["in_stock"] == True] 
     return {"in_stock_products": available, "count": len(available)}

# ── Endpoint 5 — Store summary ────────────────────────────────────
@app.get("/products/summary")
def product_summary():
    in_stock   = [p for p in products if     p["in_stock"]]
    out_stock  = [p for p in products if not p["in_stock"]]
    expensive  = max(products, key=lambda p: p["price"])
    cheapest   = min(products, key=lambda p: p["price"])
    categories = list(set(p["category"] for p in products))
    return {
        "total_products":     len(products),
        "in_stock_count":     len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive":     {"name": expensive["name"], "price": expensive["price"]},
        "cheapest":           {"name": cheapest["name"],  "price": cheapest["price"]},
        "categories":         categories,
    }

# ── Endpoint 6 — Search products ─────────────────────────────────
@app.get('/products/search/{query}')
def search_products(query: str):
    result = [p for p in products if query.lower() in p['name'].lower()]
    return {'search_query': query, 'results': result, 'count': len(result)}

# ── Endpoint 7 — Deals ────────────────────────────────────────────
@app.get("/products/deals")
def get_deals():
     cheapest = min(products, key=lambda p: p["price"])
     expensive = max(products, key=lambda p: p["price"])
     return { "best_deal": cheapest, "premium_pick": expensive, }

# ── Endpoint 2 — Return one product by its ID ─────────────────────
@app.get('/products/{product_id}')
def get_product(product_id: int):
    for product in products:
        if product['id'] == product_id:
            return {'product': product}
    return {'error': 'Product not found'}


# Week 2
# ── Endpoint 8 ─ Get only price of product ──────────────────────── 
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return {"name": product["name"], "price": product["price"]}
    return {"error": "Product not found"}

# ── Endpoint 9 ─ Customer feedback ───────────────────────────────── 
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return {"name": product["name"], "price": product["price"]}
    return {"error": "Product not found"}

# ── Order requests ───────────────────────────────────────────────
class OrderItem(BaseModel):
    product_id: int
    quantity: int

class BulkOrder(BaseModel):
    company_name:  str           = Field(..., min_length=2)
    contact_email: str           = Field(..., min_length=5)
    items:         List[OrderItem] = Field(..., min_items=1)

# ── orders one post
@app.post("/orders")
def place_order(order: OrderItem):
    order_id = len(orders) + 1

    new_order = {
        "order_id": order_id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": "pending"
    }
    orders.append(new_order)

    return {
        "message": "Order placed successfully",
        "order": new_order
    }

# ── order in bulk post
@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):
    confirmed, failed, grand_total = [], [], 0
    for item in order.items:
        product = next((p for p in products if p["id"] == item.product_id), None)
        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})
        elif not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})
        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal
            confirmed.append({"product": product["name"], "qty": item.quantity, "subtotal": subtotal})
    return {"company": order.company_name, "confirmed": confirmed,
            "failed": failed, "grand_total": grand_total}

# ── retyrn using order id
@app.get("/orders/{order_id}")
def get_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}

    return {"error": "Order not found"}

# ── order using order id
@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {
                "message": "Order confirmed",
                "order": order
            }

    return {"error": "Order not found"}

# ── Customer feedback ────────────────────────────────────────────
class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

# ── feedback post 
@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):

    feedback.append(data.dict())

    return {
        "message": "Feedback submitted successfully",
        "feedback": data.dict(),
        "total_feedback": len(feedback)
    }