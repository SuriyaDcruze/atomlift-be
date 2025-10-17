document.addEventListener('DOMContentLoaded', function() {
    // Find the checkbox and address fields
    const sameAsSiteCheckbox = document.querySelector('input[name="same_as_site_address"]');
    const siteAddressField = document.querySelector('textarea[name="site_address"]');
    const officeAddressField = document.querySelector('textarea[name="office_address"]');

    if (sameAsSiteCheckbox && siteAddressField && officeAddressField) {
        // Add event listener for checkbox change
        sameAsSiteCheckbox.addEventListener('change', function() {
            if (this.checked) {
                // Copy site_address to office_address when checkbox is checked
                officeAddressField.value = siteAddressField.value;
                // Disable office_address field to prevent manual edits
                officeAddressField.disabled = true;
            } else {
                // Enable office_address field when checkbox is unchecked
                officeAddressField.disabled = false;
            }
        });

        // Sync office_address with site_address on input if checkbox is checked
        siteAddressField.addEventListener('input', function() {
            if (sameAsSiteCheckbox.checked) {
                officeAddressField.value = this.value;
            }
        });

        // Initialize: if checkbox is checked on page load, sync and disable
        if (sameAsSiteCheckbox.checked) {
            officeAddressField.value = siteAddressField.value;
            officeAddressField.disabled = true;
        }
    }
});