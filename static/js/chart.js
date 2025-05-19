document.addEventListener("DOMContentLoaded", function () {
    try {
        const salesLabels = JSON.parse(document.getElementById("salesLabels").textContent);
        const salesData = JSON.parse(document.getElementById("salesData").textContent);
        const productLabels = JSON.parse(document.getElementById("productLabels").textContent);
        const productData = JSON.parse(document.getElementById("productData").textContent);
        const categoryLabels = JSON.parse(document.getElementById("categoryLabels").textContent);
        const categoryData = JSON.parse(document.getElementById("categoryData").textContent);

        console.log("Parsed Sales Labels:", salesLabels);
        console.log("Parsed Sales Data:", salesData);

        // Ensure no empty data before rendering charts
        if (salesLabels.length > 0 && salesData.length > 0) {
            var ctxSales = document.getElementById('salesChart').getContext('2d');
            new Chart(ctxSales, {
                type: 'bar',
                data: {
                    labels: salesLabels,
                    datasets: [{
                        label: 'Total Sales Amount',
                        data: salesData,
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        if (productLabels.length > 0 && productData.length > 0) {
            var ctxProducts = document.getElementById('productsPieChart').getContext('2d');
            new Chart(ctxProducts, {
                type: 'pie',
                data: {
                    labels: productLabels,
                    datasets: [{
                        data: productData,
                        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#8D6E63', '#D4E157', '#00E676', '#651FFF']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        if (categoryLabels.length > 0 && categoryData.length > 0) {
            var ctxCategories = document.getElementById('categoriesPieChart').getContext('2d');
            new Chart(ctxCategories, {
                type: 'pie',
                data: {
                    labels: categoryLabels,
                    datasets: [{
                        data: categoryData,
                        backgroundColor: ['#FF5733', '#33FF57', '#3357FF', '#FF33A1', '#A133FF', '#FFAA33', '#33FFD5', '#FFD433', '#33A1FF', '#FF3333']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    } catch (error) {
        console.error("Error parsing JSON data:", error);
    }
});
