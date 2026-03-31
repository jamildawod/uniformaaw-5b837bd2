import requests
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.product import Product

BASE = "https://image-pim.cottongroup.org/HEJ/Fullscreen"

def find_image(item_no: str):
    if not item_no:
        return None

    candidates = [
        f"{BASE}/{item_no}-1.webp",
        f"{BASE}/{item_no}.webp",
        f"{BASE}/{item_no}-1.jpg",
        f"{BASE}/{item_no}.jpg",
    ]

    for url in candidates:
        try:
            r = requests.head(url, timeout=3)
            if r.status_code == 200:
                return url
        except:
            pass

    return None


def main():
    db: Session = SessionLocal()

    products = db.query(Product).all()

    total = len(products)
    fixed = 0
    skipped = 0

    print(f"Total products: {total}")

    for p in products:
        if p.image_url:
            continue

        item_no = p.item_no or p.article_number

        image = find_image(item_no)

        if image:
            print(f"FIXED: {item_no} -> {image}")
            p.image_url = image
            fixed += 1
        else:
            print(f"NO IMAGE: {item_no}")
            skipped += 1

    db.commit()
    db.close()

    print("\nDONE")
    print(f"Fixed: {fixed}")
    print(f"No image found: {skipped}")


if __name__ == "__main__":
    main()
