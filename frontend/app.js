const token = localStorage.getItem("access_token");

if (!token) {
  window.location.href = "login.html";
}

function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem("access_token");

  return fetch(url, {
    ...options,
    headers: {
      ...(options.headers || {}),
      "Authorization": `Bearer ${token}`
    }
  });
}

function parseJwt(token) {
  const base64Payload = token.split('.')[1];
  const payload = atob(base64Payload);
  return JSON.parse(payload);
}

const user = parseJwt(token);

// Populate profile
document.getElementById("profileEmail").innerText = user.email;
document.getElementById("profileName").innerText = "Admin";
document.getElementById("avatar").innerText =
  user.email.charAt(0).toUpperCase();

const API_BASE = "http://localhost:8000";
let uploadChart;

function showTab(tabId) {
  document.querySelectorAll('.tab').forEach(t => t.classList.add('hidden'));
  document.getElementById(tabId).classList.remove('hidden');

  if (tabId === 'dashboard') loadDashboardMetrics();
  if (tabId === 'documents') loadDocuments();
}

async function uploadPDF() {
  const file = document.getElementById("pdfInput").files[0];
  const uploadStatus = document.getElementById("uploadStatus");
  
  if (!file) {
    uploadStatus.innerHTML = '<span style="color: var(--warning)"><i class="fas fa-exclamation-circle"></i> Please select a PDF file first</span>';
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  // Show uploading status
  uploadStatus.innerHTML = '<span style="color: var(--primary)"><i class="fas fa-spinner fa-spin"></i> Uploading and processing PDF...</span>';
  uploadStatus.style.display = 'block';

  try {
    const response = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`
      },
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      
      if (response.status === 400 && errorData.detail === "File already processed successfully") {
        uploadStatus.innerHTML = '<span style="color: var(--warning)"><i class="fas fa-exclamation-triangle"></i> File already in database</span>';
        return;
      }
      
      throw new Error(errorData.detail || 'Upload failed');
    }

    const data = await response.json();
    uploadStatus.innerHTML = `<span style="color: var(--success)"><i class="fas fa-check-circle"></i> ${data.message}</span>`;
    
    // Clear the file input
    document.getElementById("pdfInput").value = '';
    
    // Refresh the dashboard and documents
    loadDashboardMetrics();
    setTimeout(() => loadDocuments(), 1000); // Small delay to ensure processing started

  } catch (error) {
    console.error('Upload error:', error);
    uploadStatus.innerHTML = `<span style="color: var(--danger)"><i class="fas fa-times-circle"></i> Error: ${error.message}</span>`;
  }
}

async function loadDocuments() {
  const res = await fetch(`${API_BASE}/documents`, {
    headers: {
      "Authorization": `Bearer ${token}`
    }
  });
  const docs = await res.json();

  const table = document.getElementById("pdfTable");
  table.innerHTML = "";

  docs.forEach(d => {
    // Format the date to be user-friendly
    const uploadDate = new Date(d.uploaded_at);
    const formattedDate = uploadDate.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });

    // Add status badge with appropriate styling
    let statusBadge = '';
    if (d.status === 'completed') {
      statusBadge = `<span class="status-completed"><i class="fas fa-check"></i> ${d.status}</span>`;
    } else if (d.status === 'failed') {
      statusBadge = `<span class="status-failed"><i class="fas fa-times"></i> ${d.status}</span>`;
    } else if (d.status === 'processing') {
      statusBadge = `<span class="status-processing"><i class="fas fa-spinner fa-spin"></i> ${d.status}</span>`;
    } else {
      statusBadge = `<span>${d.status}</span>`;
    }

    table.innerHTML += `
      <tr>
        <td>${d.filename}</td>
        <td>${statusBadge}</td>
        <td>${formattedDate}</td>
        <td>${d.uploaded_by_email}</td>
      </tr>
    `;
  });
}

async function loadDashboardMetrics(startDate = null, endDate = null) {
  let url = `${API_BASE}/metrics`;

  const params = new URLSearchParams();
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  if (params.toString()) {
    url += `?${params.toString()}`;
  }

  const res = await fetchWithAuth(url);
  const data = await res.json();

  document.getElementById("totalPdfs").innerText = data.total;
  document.getElementById("processedPdfs").innerText = data.processed;
  document.getElementById("failedPdfs").innerText = data.failed;

  renderChart(data.daily_uploads);
}

function applyDateFilter() {
  const startDate = document.getElementById("startDate").value;
  const endDate = document.getElementById("endDate").value;

  loadDashboardMetrics(startDate, endDate);
}

function resetDateFilter() {
  document.getElementById("startDate").value = "";
  document.getElementById("endDate").value = "";

  loadDashboardMetrics();
}

function renderChart(dailyData) {
  const ctx = document.getElementById("uploadChart");

  if (uploadChart) {
    uploadChart.destroy();
  }

  uploadChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: dailyData.map(d => d.date),
      datasets: [
        {
          label: "PDF Uploads",
          data: dailyData.map(d => d.count),
          borderColor: "#000000ff",
          backgroundColor: "#2563eb",
          borderRadius: 6,
          fill: true,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: "top",
          labels: {
            usePointStyle: true
          }
        },
        tooltip: {
          backgroundColor: "#0f172a",
          titleColor: "#ffffff",
          bodyColor: "#e5e7eb",
          padding: 12
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: "#475569"
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: "#e5e7eb"
          },
          ticks: {
            color: "#475569",
            precision: 0
          }
        }
      }
    }
  });
}

function logout() {
  localStorage.removeItem("access_token");
  window.location.href = "login.html";
}

// Default view
showTab('dashboard');