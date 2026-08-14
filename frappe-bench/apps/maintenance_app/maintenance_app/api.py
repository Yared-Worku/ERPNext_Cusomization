import json

import frappe


@frappe.whitelist(allow_guest=True)
def get_service_tickets_with_parts():
    """
    Fetches Service Tickets joined with their corresponding
    Spare Parts directly from MariaDB using raw SQL.
    """
    query = """
        SELECT
            st.name AS ticket_id,
            st.equipment_name,
            st.status,
            st.labor_fee,
            st.total_cost,
            sp.part_name,
            sp.qty,
            sp.unit_price,
            sp.amount
        FROM `tabService Ticket` st
        INNER JOIN `tabService Spare Part` sp
            ON sp.parent = st.name
        ORDER BY st.creation DESC;
    """

    records = frappe.db.sql(query, as_dict=True)

    return {
        "status": "success",
        "count": len(records),
        "data": records
    }

@frappe.whitelist(allow_guest=True)
def create_service_ticket(equipment_name: str, labor_fee: float = 0.0, spare_parts: list | str | None = None):
    """
    Inserts a new Service Ticket and associated Spare Parts into MariaDB using SQL.
    """
    labor_fee = float(labor_fee)

    # Parse spare_parts if passed as a JSON string
    if isinstance(spare_parts, str):
        spare_parts = json.loads(spare_parts)
    elif spare_parts is None:
        spare_parts = []

    # 1. Generate unique Ticket ID
    ticket_id = f"TICKET-{frappe.utils.random_string(5).upper()}"

    # 2. Calculate spare parts cost totals
    total_parts_cost = 0.0
    parsed_parts = []

    for item in spare_parts:
        qty = float(item.get("qty", 1))
        unit_price = float(item.get("unit_price", 0.0))
        amount = qty * unit_price
        total_parts_cost += amount

        parsed_parts.append({
            "part_name": item.get("part_name", "Unknown Part"),
            "qty": qty,
            "unit_price": unit_price,
            "amount": amount
        })

    total_cost = labor_fee + total_parts_cost

    # 3. Insert Parent Record into `tabService Ticket`
    insert_ticket_sql = """
        INSERT INTO `tabService Ticket`
        (name, creation, modified, modified_by, owner, docstatus, equipment_name, status, labor_fee, total_cost)
        VALUES (%s, NOW(), NOW(), 'Administrator', 'Administrator', 0, %s, 'Open', %s, %s);
    """
    frappe.db.sql(insert_ticket_sql, (ticket_id, equipment_name, labor_fee, total_cost))

    # 4. Insert Child Records into `tabService Spare Part`
    insert_part_sql = """
        INSERT INTO `tabService Spare Part`
        (name, creation, modified, modified_by, owner, docstatus, parent, parentfield, parenttype, part_name, qty, unit_price, amount)
        VALUES (%s, NOW(), NOW(), 'Administrator', 'Administrator', 0, %s, 'spare_parts', 'Service Ticket', %s, %s, %s, %s);
    """

    for part in parsed_parts:
        part_id = f"PART-{frappe.utils.random_string(5).upper()}"
        frappe.db.sql(insert_part_sql, (
            part_id, ticket_id, part["part_name"], part["qty"], part["unit_price"], part["amount"]
        ))

    # Commit changes to MariaDB
    frappe.db.commit()

    return {
        "status": "success",
        "message": "Service Ticket created successfully",
        "ticket_id": ticket_id,
        "total_cost": total_cost
    }
