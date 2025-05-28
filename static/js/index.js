let sensorChart_temp_humidity;

function getMostRecentDate(timestamps) {
  if (!timestamps.length) return '';
  // Extract date part from the most recent timestamp
  const last = timestamps[timestamps.length - 1];
  return last ? last.split(' ')[0] : '';
}

function getTimesFromTimestamps(timestamps) {
  // Extract only the time part (HH:MM:SS) from each timestamp
  return timestamps.map(ts => {
    if (!ts) return '';
    // Try to match HH:MM:SS in the string
    const match = ts.match(/\\b(\\d{2}:\\d{2}:\\d{2})\\b/);
    return match ? match[1] : ts;
  });
}

async function fetchSensorData() {
  try {
    const response = await fetch('/sensor-data');
    const data = await response.json();

    if (data.length === 0) {
      return;
    }

    // Reverse data to show oldest first
    data.reverse();

    const timestamps = data.map(d => d.datetime);
    const temperatures = data.map(d => parseFloat(d.temperature));
    const humidities = data.map(d => parseFloat(d.humidity));

    // Update the sensor values displayed
    document.getElementById('temperature').textContent = temperatures[temperatures.length - 1];
    document.getElementById('humidity').textContent = humidities[humidities.length - 1];

    // Update chart title with the most recent date
    const dateTitle = document.getElementById('chart-date-title');
    if (dateTitle) {
      dateTitle.textContent = getMostRecentDate(timestamps);
    }

    // Update charts (X axis: only time)
    const times = getTimesFromTimestamps(timestamps);
    updateChart(times, temperatures, humidities);
  } catch (error) {
    console.error('Error fetching sensor data:', error);
  }
}

function createChart() {
  const ctx1 = document.getElementById('sensorChart_temp_humidity').getContext('2d');

  sensorChart_temp_humidity = new Chart(ctx1, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Temperature (°C)',
          data: [],
          borderColor: 'rgba(255, 99, 132, 1)',
          backgroundColor: 'rgba(255, 99, 132, 0.15)',
          borderWidth: 3,
          pointBackgroundColor: 'rgba(255, 99, 132, 1)',
          pointRadius: 5,
          tension: 0.3,
          fill: true
        },
        {
          label: 'Humidity (%)',
          data: [],
          borderColor: 'rgba(54, 162, 235, 1)',
          backgroundColor: 'rgba(54, 162, 235, 0.15)',
          borderWidth: 3,
          pointBackgroundColor: 'rgba(54, 162, 235, 1)',
          pointRadius: 5,
          tension: 0.3,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          labels: {
            font: { size: 16 }
          }
        },
        tooltip: {
          enabled: true,
          mode: 'index',
          intersect: false
        }
      },
      scales: {
        x: {
          ticks: { autoSkip: true, maxTicksLimit: 10 },
          title: { display: true, text: 'Time', font: { size: 16 } }
        },
        y: {
          beginAtZero: false,
          title: { display: true, text: 'Value', font: { size: 16 } },
          grid: { color: 'rgba(0,0,0,0.05)' }
        }
      }
    }
  });
}

function updateChart(labels, tempData, humData) {
  // Update Temperature & Humidity chart
  sensorChart_temp_humidity.data.labels = labels;
  sensorChart_temp_humidity.data.datasets[0].data = tempData;
  sensorChart_temp_humidity.data.datasets[1].data = humData;
  sensorChart_temp_humidity.update();
}

// Launch the graph and update every 2s
document.addEventListener('DOMContentLoaded', () => {
  createChart();
  fetchSensorData();
  setInterval(fetchSensorData, 2000);
});
