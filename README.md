# 🧩 Coderr Backend API

## 📌 Description
Coderr is a freelance marketplace backend built with Django and Django REST
Framework. Business users can create service offers with multiple pricing
tiers, customers can browse offers, place orders, and leave reviews.

**Note:** This repository contains the backend only. The matching frontend is
provided separately here:
[Developer-Akademie-Backendkurs/project.Coderr](https://github.com/Developer-Akademie-Backendkurs/project.Coderr).
Clone and run it independently (see the CORS note below for connecting them).

---

## ⚙️ Tech Stack
- Python 3.14
- Django 6.1.1
- Django REST Framework 3.18.1
- django-filter 26.1
- django-cors-headers 4.9.0
- Pillow 11.3.0
- SQLite

---

## 🚀 Quickstart Instructions

- Clone the repository:
```bash
git clone https://github.com/PatrickSchuette/Coderr.git
```

- Create a virtual environment:
```bash
python -m venv env
```

- Activate the virtual environment:
```bash
# Windows
env\Scripts\activate

# macOS/Linux
source env/bin/activate
```

- Install dependencies:
```bash
pip install -r requirements.txt
```

- Create a `.env` file in the project root:
```bash
SECRET_KEY='your-secret-key-here'
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

  Generate a secure key with:
```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

- Run database migrations:
```bash
python manage.py migrate
```

- Create a superuser:
```bash
python manage.py createsuperuser
```

- Run the server:
```bash
python manage.py runserver
```

---

# 📡 API Overview

## 🔐 Authentication
- `POST /api/registration/` → register user (customer or business)
- `POST /api/login/` → login user + get token
- `POST /api/logout/` → logout user (invalidates token)

## 👤 Profile
- `GET /api/profile/{id}/` → get profile details
- `PATCH /api/profile/{id}/` → update own profile (owner only)
- `GET /api/profiles/business/` → list all business profiles
- `GET /api/profiles/customer/` → list all customer profiles

## 💼 Offers
- `GET /api/offers/` → list offers (filterable, paginated)
- `POST /api/offers/` → create offer with 3 pricing tiers (business only)
- `GET /api/offers/{id}/` → get offer details
- `PATCH /api/offers/{id}/` → update offer (owner only)
- `DELETE /api/offers/{id}/` → delete offer (owner only)
- `GET /api/offerdetails/{id}/` → get a single pricing tier

## 📦 Orders
- `GET /api/orders/` → list own orders (as customer or business)
- `POST /api/orders/` → place an order from an offer detail (customer only)
- `PATCH /api/orders/{id}/` → update order status (assigned business user only)
- `DELETE /api/orders/{id}/` → delete order (admin only)
- `GET /api/order-count/{business_user_id}/` → count of in-progress orders
- `GET /api/completed-order-count/{business_user_id}/` → count of completed orders

## ⭐ Reviews
- `GET /api/reviews/` → list reviews (filterable)
- `POST /api/reviews/` → create a review for a business user (customer only)
- `PATCH /api/reviews/{id}/` → update own review (owner only)
- `DELETE /api/reviews/{id}/` → delete own review (owner only)

## 📊 Base Info
- `GET /api/base-info/` → aggregated platform stats (review count, average
  rating, business profile count, offer count)

---

## ⚠️ Notes

- Authentication uses DRF Token Authentication. Include the token in every
  authenticated request as:
  
  Authorization: Token <your_token>
- CORS is currently allowed for all origins during development
  (`CORS_ALLOW_ALL_ORIGINS = True` in `core/settings.py`) — restrict this
  before any real deployment.
- An offer must always include exactly 3 details: one `basic`, one
  `standard`, and one `premium` tier.
- Only users with a `business` profile can create offers; only users with a
  `customer` profile can place orders and write reviews.
- Orders freeze a snapshot of the referenced offer detail at creation time —
  later changes to the original offer do not retroactively affect existing
  orders.
- Image uploads (profile picture, offer image) use `multipart/form-data`
  `PATCH` requests, e.g. via the `file`/`image` field alongside the other
  profile/offer fields.
- The `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` values are loaded from a
  `.env` file, which is **not** included in this repository (see
  `.env.example` for the required format). Set `DEBUG=False` and a real
  `ALLOWED_HOSTS` value before any production deployment.

---

# 🧪 Testing

## Automated Test Suite
The project includes automated tests across all apps 
```bash
python manage.py test auth_app.tests profile_app.tests offers_app.tests orders_app.tests reviews_app.tests base_info_app.tests
```

## Postman Collection
A Postman Collection and Environment file covering both happy-path and
unhappy-path scenarios across all endpoints:

- [Coderr.postman_collection.json](./postmanJson/Coderr.postman_collection.json)
- [Coderr.postman_environment.json](./postmanJson/Coderr.postman_environment.json)

To use them:
1. Import both files into Postman
2. Select the "Coderr" environment
3. Run the full collection top-to-bottom via the Collection Runner (later
   requests depend on tokens/IDs set by earlier ones)