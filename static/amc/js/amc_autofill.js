document.addEventListener("DOMContentLoaded", function () {
    const customerSelect = document.querySelector('select[name="customer"]');
    const siteField = document.querySelector('input[name="latitude"]');
    const jobField = document.querySelector('input[name="equipment_no"]');
    const startDateInput = document.querySelector('input[name="start_date"]');
    const endDateInput = document.querySelector('input[name="end_date"]');

    // ---- Auto-set End Date (+1 year) ----
    if (startDateInput && endDateInput) {
        startDateInput.addEventListener("change", () => {
            const start = new Date(startDateInput.value);
            if (isNaN(start)) return;
            const end = new Date(start);
            end.setFullYear(start.getFullYear() + 1);
            endDateInput.value = end.toISOString().split("T")[0];
        });
    }

    // ---- Auto-fetch Site Address & Job No ----
    if (customerSelect) {
        customerSelect.addEventListener("change", async function () {
            const id = this.value;
            if (!id) return;

            try {
                const resp = await fetch(`/customer/customer/${id}/`);
                if (!resp.ok) return;
                const data = await resp.json();

                if (data.site_address && siteField) siteField.value = data.site_address;
                if (data.job_no && jobField) jobField.value = data.job_no;

            } catch (err) {
                console.error("Failed to fetch customer info:", err);
            }
        });
    }
});
