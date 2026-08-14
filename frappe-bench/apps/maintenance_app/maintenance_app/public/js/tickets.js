document.addEventListener("DOMContentLoaded", function () {
    fetchTickets();

    const form = document.getElementById("create-ticket-form");
    if (form) {
        form.addEventListener("submit", handleFormSubmit);
    }
});

// 1. Fetch & Render Tickets from GET API
function fetchTickets() {
    fetch("/api/method/maintenance_app.api.get_service_tickets_orm")
        .then(response => response.json())
        .then(res => {
            const tbody = document.getElementById("tickets-tbody");
            tbody.innerHTML = "";

            if (!res.message || !res.message.data || res.message.data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4">No service tickets found.</td></tr>`;
                return;
            }

            res.message.data.forEach(ticket => {
                let partsSummary = ticket.spare_parts.map(
                    p => `${p.part_name} (x${p.qty} @ $${p.unit_price})`
                ).join("<br>") || "<em>None</em>";

                let row = `
                    <tr>
                        <td><strong>${ticket.name}</strong></td>
                        <td>${ticket.equipment_name}</td>
                        <td><span class="badge bg-info text-dark">${ticket.status}</span></td>
                        <td>$${parseFloat(ticket.labor_fee).toFixed(2)}</td>
                        <td><strong>$${parseFloat(ticket.total_cost).toFixed(2)}</strong></td>
                        <td><small>${partsSummary}</small></td>
                    </tr>
                `;
                tbody.innerHTML += row;
            });
        })
        .catch(err => {
            console.error("Error fetching tickets:", err);
        });
}

// 2. Add dynamic Spare Part Row
function addSparePartRow() {
    const container = document.getElementById("spare-parts-list");
    const newRow = document.createElement("div");
    newRow.className = "row g-2 mb-2 part-row";
    newRow.innerHTML = `
        <div class="col-md-5">
            <input type="text" class="form-control part-name" placeholder="Part Name" required>
        </div>
        <div class="col-md-3">
            <input type="number" class="form-control part-qty" placeholder="Qty" value="1" min="1" required>
        </div>
        <div class="col-md-4">
            <input type="number" step="0.01" class="form-control part-price" placeholder="Unit Price ($)" value="0.00" required>
        </div>
    `;
    container.appendChild(newRow);
}

// 3. Handle Form POST Submission
function handleFormSubmit(e) {
    e.preventDefault();

    const equipmentName = document.getElementById("equipment_name").value;
    const laborFee = parseFloat(document.getElementById("labor_fee").value);

    const partRows = document.querySelectorAll(".part-row");
    const spareParts = [];

    partRows.forEach(row => {
        const name = row.querySelector(".part-name").value;
        const qty = parseFloat(row.querySelector(".part-qty").value);
        const unitPrice = parseFloat(row.querySelector(".part-price").value);

        if (name) {
            spareParts.push({
                part_name: name,
                qty: qty,
                unit_price: unitPrice
            });
        }
    });

    const payload = {
        equipment_name: equipmentName,
        labor_fee: laborFee,
        spare_parts: spareParts
    };

    fetch("/api/method/maintenance_app.api.create_service_ticket_orm", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(res => {
        if (res.message && res.message.status === "success") {
            alert(`Success! Ticket created: ${res.message.ticket_id}`);
            document.getElementById("create-ticket-form").reset();
            fetchTickets();
        } else {
            alert("Error creating ticket.");
        }
    })
    .catch(err => console.error("Error submitting ticket:", err));
}