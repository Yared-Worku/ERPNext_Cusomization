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
@frappe.whitelist(allow_guest=True)
def update_ticket_status(ticket_id: str, status: str):
    """
    [UPDATE] Updates the status of an existing Service Ticket using raw SQL.
    """
    # Verify existence
    check_sql = "SELECT name FROM `tabService Ticket` WHERE name = %s;"
    if not frappe.db.sql(check_sql, (ticket_id,)):
        return {"status": "error", "message": f"Ticket {ticket_id} not found."}

    update_sql = """
        UPDATE `tabService Ticket`
        SET status = %s, modified = NOW()
        WHERE name = %s;
    """
    frappe.db.sql(update_sql, (status, ticket_id))
    frappe.db.commit()

    return {
        "status": "success",
        "message": f"Ticket {ticket_id} status updated to '{status}'",
        "ticket_id": ticket_id,
        "new_status": status
    }


@frappe.whitelist(allow_guest=True)
def delete_service_ticket(ticket_id: str):
    """
    [DELETE] Removes a Service Ticket and its child Spare Parts from MariaDB.
    """
    # Verify existence
    check_sql = "SELECT name FROM `tabService Ticket` WHERE name = %s;"
    if not frappe.db.sql(check_sql, (ticket_id,)):
        return {"status": "error", "message": f"Ticket {ticket_id} not found."}

    # 1. Delete Child Records first (Relational Integrity)
    delete_parts_sql = "DELETE FROM `tabService Spare Part` WHERE parent = %s;"
    frappe.db.sql(delete_parts_sql, (ticket_id,))

    # 2. Delete Parent Record
    delete_ticket_sql = "DELETE FROM `tabService Ticket` WHERE name = %s;"
    frappe.db.sql(delete_ticket_sql, (ticket_id,))

    frappe.db.commit()

    return {
        "status": "success",
        "message": f"Service Ticket {ticket_id} and its associated spare parts deleted successfully",
        "deleted_ticket_id": ticket_id
    }
