document.addEventListener("DOMContentLoaded", function () {
    const passengersInput = document.querySelector("#id_no_of_passengers");
    const loadInput = document.querySelector("#id_load_kg");

    if (passengersInput && loadInput) {
        passengersInput.addEventListener("input", function () {
            const passengers = parseInt(passengersInput.value);
            if (!isNaN(passengers) && passengers > 0) {
                const autoValue = passengers * 68;
                loadInput.value = autoValue;
            }
        });
    }
});
