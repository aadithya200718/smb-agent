"""
Phase 4 — Automated API endpoint tester.

Registers a business, logs in, and exercises every Phase 4 endpoint.
Requires: MongoDB running, server on http://localhost:8000
"""

import asyncio
import sys
import httpx

BASE = "http://localhost:8000"

EMAIL = "testowner@restaurant.com"
PASSWORD = "SecurePass123"
BIZ_NAME = "Test Restaurant"
PHONE = "+919876543210"


async def main():
    passed = 0
    failed = 0
    token = ""
    item_id = ""

    async with httpx.AsyncClient(base_url=BASE, timeout=15.0) as c:

        # ── 1. Register ────────────────────────────────────────────
        print("\n1. POST /auth/register")
        r = await c.post("/auth/register", json={
            "email": EMAIL, "password": PASSWORD,
            "business_name": BIZ_NAME, "phone": PHONE,
        })
        if r.status_code == 200 and r.json().get("success"):
            token = r.json()["data"]["access_token"]
            print(f"   PASS  (token={token[:20]}...)")
            passed += 1
        elif r.status_code == 400 and "already registered" in r.text.lower():
            # already registered from a previous run — login instead
            print("   SKIP  (already registered, will login)")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 2. Login ───────────────────────────────────────────────
        print("2. POST /auth/login")
        r = await c.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
        if r.status_code == 200 and r.json().get("success"):
            token = r.json()["data"]["access_token"]
            print(f"   PASS  (token={token[:20]}...)")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1
            # can't continue without token
            print("\n*** Cannot continue without auth token ***")
            return

        headers = {"Authorization": f"Bearer {token}"}

        # ── 3. GET /auth/me ────────────────────────────────────────
        print("3. GET  /auth/me")
        r = await c.get("/auth/me", headers=headers)
        if r.status_code == 200 and r.json().get("success"):
            print(f"   PASS  (business={r.json()['data'].get('name')})")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 4. POST /menu (create) ─────────────────────────────────
        print("4. POST /menu")
        r = await c.post("/menu", headers=headers, json={
            "name": "Veg Biryani", "price": 180,
            "category": "Main Course", "description": "Fragrant rice", "available": True,
        })
        if r.status_code == 200 and r.json().get("success"):
            item_id = r.json()["data"]["item_id"]
            print(f"   PASS  (item_id={item_id})")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 5. GET /menu ───────────────────────────────────────────
        print("5. GET  /menu")
        r = await c.get("/menu", headers=headers)
        if r.status_code == 200 and r.json().get("success"):
            print(f"   PASS  ({len(r.json()['data'])} items)")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 6. PUT /menu/{item_id} ─────────────────────────────────
        print(f"6. PUT  /menu/{item_id}")
        r = await c.put(f"/menu/{item_id}", headers=headers, json={"price": 200})
        if r.status_code == 200 and r.json().get("success"):
            print(f"   PASS  (price updated)")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 7. PATCH /menu/{item_id}/availability ──────────────────
        print(f"7. PATCH /menu/{item_id}/availability")
        r = await c.patch(f"/menu/{item_id}/availability", headers=headers, json={"available": False})
        if r.status_code == 200 and r.json().get("success"):
            print(f"   PASS  (disabled)")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 8. GET /orders ─────────────────────────────────────────
        print("8. GET  /orders")
        r = await c.get("/orders", headers=headers)
        if r.status_code == 200 and r.json().get("success"):
            print(f"   PASS  ({r.json()['pagination']['total']} orders)")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 9. GET /orders/stats ───────────────────────────────────
        print("9. GET  /orders/stats")
        r = await c.get("/orders/stats", headers=headers)
        if r.status_code == 200 and r.json().get("success"):
            print(f"   PASS  (stats={r.json()['data']})")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 10. GET /business/profile ──────────────────────────────
        print("10. GET  /business/profile")
        r = await c.get("/business/profile", headers=headers)
        if r.status_code == 200 and r.json().get("success"):
            print(f"   PASS  (name={r.json()['data'].get('name')})")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 11. PUT /business/profile ──────────────────────────────
        print("11. PUT  /business/profile")
        r = await c.put("/business/profile", headers=headers, json={
            "address": "123 Test Street", "timings": {"mon-sat": "9am-10pm"}
        })
        if r.status_code == 200 and r.json().get("success"):
            print(f"   PASS  (address updated)")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 12. GET /business/chats ────────────────────────────────
        print("12. GET  /business/chats")
        r = await c.get("/business/chats", headers=headers)
        if r.status_code == 200 and r.json().get("success") is not None:
            print(f"   PASS  ({r.json().get('pagination', {}).get('total', 0)} chats)")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 13. GET /analytics/overview ────────────────────────────
        print("13. GET  /analytics/overview")
        r = await c.get("/analytics/overview", headers=headers)
        if r.status_code == 200 and r.json().get("success"):
            print(f"   PASS  (data={r.json()['data']})")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 14. GET /analytics/orders-by-day ───────────────────────
        print("14. GET  /analytics/orders-by-day")
        r = await c.get("/analytics/orders-by-day", headers=headers)
        if r.status_code == 200 and r.json().get("success"):
            print(f"   PASS  ({len(r.json()['data'])} days)")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 15. GET /analytics/top-items ───────────────────────────
        print("15. GET  /analytics/top-items")
        r = await c.get("/analytics/top-items", headers=headers)
        if r.status_code == 200 and r.json().get("success"):
            print(f"   PASS  ({len(r.json()['data'])} items)")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 16. GET /analytics/customer-stats ──────────────────────
        print("16. GET  /analytics/customer-stats")
        r = await c.get("/analytics/customer-stats", headers=headers)
        if r.status_code == 200 and r.json().get("success"):
            print(f"   PASS  (data={r.json()['data']})")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

        # ── 17. DELETE /menu/{item_id} (cleanup) ───────────────────
        print(f"17. DELETE /menu/{item_id}")
        r = await c.delete(f"/menu/{item_id}", headers=headers)
        if r.status_code == 200 and r.json().get("success"):
            print(f"   PASS  (deleted)")
            passed += 1
        else:
            print(f"   FAIL  {r.status_code} {r.text[:120]}")
            failed += 1

    # ── Summary ────────────────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"  RESULTS:  {passed} passed,  {failed} failed")
    print(f"{'='*50}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    asyncio.run(main())
