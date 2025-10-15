from wagtail import hooks

@hooks.register('insert_editor_js')
def add_dynamic_item_field_js():
    return """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const serviceTypeRadios = document.querySelectorAll('input[name="service_type"]');
        const taxPrefRadios = document.querySelectorAll('input[name="tax_preference"]');

        const gstField = document.querySelector('[data-contentpath="gst"]');
        const igstField = document.querySelector('[data-contentpath="igst"]');
        const sacField = document.querySelector('[data-contentpath="sac_code"]');

        function updateVisibility() {
            const serviceType = document.querySelector('input[name="service_type"]:checked')?.value;
            const taxPref = document.querySelector('input[name="tax_preference"]:checked')?.value;

            if (!gstField || !igstField || !sacField) return;

            // Hide/show based on service type
            if (serviceType === 'Goods') {
                gstField.style.display = '';
                igstField.style.display = '';
                sacField.style.display = 'none';
            } else if (serviceType === 'Services') {
                gstField.style.display = 'none';
                igstField.style.display = 'none';
                sacField.style.display = '';
            }

            // Override for non-taxable
            if (taxPref === 'Non-Taxable') {
                gstField.style.display = 'none';
                igstField.style.display = 'none';
                sacField.style.display = 'none';
            }
        }

        serviceTypeRadios.forEach(r => r.addEventListener('change', updateVisibility));
        taxPrefRadios.forEach(r => r.addEventListener('change', updateVisibility));

        updateVisibility();  // Initialize on page load
    });
    </script>
    """
