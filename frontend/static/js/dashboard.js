// SightFlow Dashboard JavaScript

async function loadSessions() {
  const tbody = document.getElementById("sessionsTable");
  tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Loading...</td></tr>';

  try {
    const data = await apiGet("/api/session/list");
    const sessions = data.sessions;

    if (sessions.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No sessions yet. Start a new proctoring session.</td></tr>';
      return;
    }

    tbody.innerHTML = "";
    sessions.forEach(s => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><code style="color:#06b6d4">${s.session_id}</code></td>
        <td>${s.candidate_name}</td>
        <td><span class="badge ${getRiskBadgeClass(s.risk_level)}">${s.risk_level}</span></td>
        <td>
          <div style="display:flex;align-items:center;gap:0.5rem;">
            <div style="flex:1;background:#1e293b;border-radius:4px;height:8px;overflow:hidden;">
              <div style="width:${s.risk_score}%;height:100%;background:${getRiskBarColor(s.risk_score)};border-radius:4px;"></div>
            </div>
            <span style="font-size:0.8rem;width:30px;">${s.risk_score}</span>
          </div>
        </td>
        <td>
          <span class="status-dot ${s.active ? 'dot-green' : 'dot-red'}" style="margin-right:0.3rem;"></span>
          ${s.active ? "Active" : "Ended"}
        </td>
        <td>
          <button class="btn btn-outline" style="padding:0.3rem 0.7rem;font-size:0.8rem;" onclick="viewSession('${s.session_id}')">View</button>
          <button class="btn btn-accent" style="padding:0.3rem 0.7rem;font-size:0.8rem;margin-left:0.3rem;" onclick="downloadReport('${s.session_id}')">PDF</button>
          <button class="btn btn-danger" style="padding:0.3rem 0.7rem;font-size:0.8rem;margin-left:0.3rem;" onclick="deleteSession('${s.session_id}')">Delete</button>
        </td>
      `;
      tbody.appendChild(row);
    });

    // Update stat cards
    document.getElementById("totalSessions").textContent = sessions.length;
    document.getElementById("activeSessions").textContent = sessions.filter(s => s.active).length;
    document.getElementById("highRiskCount").textContent = sessions.filter(s => s.risk_level === "HIGH RISK").length;
    document.getElementById("avgRisk").textContent = sessions.length
      ? Math.round(sessions.reduce((a, s) => a + s.risk_score, 0) / sessions.length)
      : 0;

  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-danger">Error: ${e.message}</td></tr>`;
  }
}

async function viewSession(sid) {
  const modal = document.getElementById("sessionModal");
  const content = document.getElementById("modalContent");
  modal.classList.remove("hidden");
  content.innerHTML = '<div class="text-center mt-2"><span class="spinner"></span> Loading...</div>';

  try {
    const data = await apiGet(`/api/session/${sid}/status`);
    const s = data.session;
    const r = data.risk;

    content.innerHTML = `
      <div class="flex-between mb-2">
        <h3 style="font-size:1.2rem;">${s.candidate_name}</h3>
        <span class="badge ${getRiskBadgeClass(r.level)}">${r.level}</span>
      </div>
      <div class="grid-2" style="margin-bottom:1rem;">
        <div><span class="text-muted" style="font-size:0.8rem;">SESSION ID</span><br><code style="color:#06b6d4">${s.session_id}</code></div>
        <div><span class="text-muted" style="font-size:0.8rem;">START TIME</span><br>${s.start_time}</div>
        <div><span class="text-muted" style="font-size:0.8rem;">DURATION</span><br>${s.duration_seconds}s</div>
        <div><span class="text-muted" style="font-size:0.8rem;">FRAMES ANALYZED</span><br>${s.total_frames}</div>
      </div>

      <div class="risk-meter-container">
        <div class="flex-between mb-1">
          <span style="font-size:0.85rem;color:#94a3b8;">Risk Score</span>
          <strong style="font-size:1.1rem;">${r.score}/100</strong>
        </div>
        <div class="risk-bar-bg">
          <div class="risk-bar-fill" style="width:${r.score}%;background:${getRiskBarColor(r.score)};"></div>
        </div>
      </div>

      <div class="grid-4 mt-2 mb-2">
        <div class="metric-card">
          <div class="metric-value text-danger">${s.face_mismatch_count}</div>
          <div class="metric-label">Face Mismatch</div>
        </div>
        <div class="metric-card">
          <div class="metric-value text-warning">${s.liveness_fail_count}</div>
          <div class="metric-label">Liveness Fail</div>
        </div>
        <div class="metric-card">
          <div class="metric-value" style="color:#eab308;">${s.multi_face_alerts}</div>
          <div class="metric-label">Multi-Face</div>
        </div>
        <div class="metric-card">
          <div class="metric-value" style="color:#6366f1;">${s.absence_alerts}</div>
          <div class="metric-label">Absences</div>
        </div>
      </div>

      <div style="margin-top:1rem;">
        <div style="font-size:0.75rem;color:#94a3b8;text-transform:uppercase;margin-bottom:0.5rem;">Compliance Recommendation</div>
        <div style="background:rgba(30,58,138,0.2);border-left:3px solid #3b82f6;padding:0.8rem;border-radius:4px;font-size:0.9rem;">
          ${r.recommendation}
        </div>
      </div>

      ${s.events.length > 0 ? `
        <div style="margin-top:1rem;">
          <div style="font-size:0.75rem;color:#94a3b8;text-transform:uppercase;margin-bottom:0.5rem;">Recent Events</div>
          <div class="log-container">
            ${s.events.slice(-10).reverse().map(e => `
              <div class="log-entry ${e.event_type !== 'ok' ? 'warn' : 'success'}">
                [${e.time_str}] ${formatEventType(e.event_type)} — ${e.details}
              </div>
            `).join("")}
          </div>
        </div>
      ` : ""}

      <div class="flex gap-1 mt-2">
        <button class="btn btn-accent" onclick="loadAIAnalysis('${sid}')">🤖 AI Analysis</button>
        <button class="btn btn-primary" onclick="downloadReport('${sid}')">📄 Download PDF</button>
      </div>

      <div id="aiAnalysisSection" class="hidden mt-2"></div>
    `;
  } catch (e) {
    content.innerHTML = `<div class="text-danger">Error: ${e.message}</div>`;
  }
}

async function loadAIAnalysis(sid) {
  const section = document.getElementById("aiAnalysisSection");
  section.classList.remove("hidden");
  section.innerHTML = '<div class="text-center"><span class="spinner"></span> Generating AI analysis...</div>';

  try {
    const data = await apiGet(`/api/session/${sid}/analysis`);
    section.innerHTML = `
      <div class="ai-label">AI Summary</div>
      <div class="ai-box">${data.summary}</div>
      <div class="ai-label">Behavior Explanation</div>
      <div class="ai-box">${data.explanation}</div>
      <div class="ai-label">Recommendation</div>
      <div class="ai-box">${data.recommendation}</div>
    `;
  } catch (e) {
    section.innerHTML = `<div class="text-danger">AI analysis failed: ${e.message}</div>`;
  }
}

function downloadReport(sid) {
  showToast("Generating PDF report...", "info");
  window.open(`/api/session/${sid}/report`, "_blank");
}

async function deleteSession(sid) {
  if (!confirm(`Delete session ${sid}?`)) return;
  try {
    await apiDelete(`/api/session/${sid}`);
    showToast("Session deleted", "success");
    loadSessions();
  } catch (e) {
    showToast("Delete failed: " + e.message, "error");
  }
}

function closeModal() {
  document.getElementById("sessionModal").classList.add("hidden");
}

// Close modal on backdrop click
document.getElementById("sessionModal").addEventListener("click", (e) => {
  if (e.target === document.getElementById("sessionModal")) closeModal();
});

// Auto-refresh every 10s
loadSessions();
setInterval(loadSessions, 10000);