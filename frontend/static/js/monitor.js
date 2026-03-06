// SightFlow Monitor — Real-time proctoring JavaScript

// ─────────────────────────────────────────────────────────────────
// State
// ─────────────────────────────────────────────────────────────────
let ws                   = null;
let mediaStream          = null;
let captureInterval      = null;
let sessionId            = null;
let isRegistered         = false;
let sessionStartTime     = null;
let allSessionDetections = [];

// ─────────────────────────────────────────────────────────────────
// DOM refs
// ─────────────────────────────────────────────────────────────────
const video            = document.getElementById("videoFeed");
const btnStart         = document.getElementById("btnStart");
const btnRegister      = document.getElementById("btnRegister");
const btnEndSession    = document.getElementById("btnEndSession");
const btnCreateSession = document.getElementById("btnCreateSession");

// ─────────────────────────────────────────────────────────────────
// YOLO icon map
// ─────────────────────────────────────────────────────────────────
const OBJECT_ICONS = {
  "Phone":             "📱",
  "Laptop":            "💻",
  "Tablet":            "📟",
  "Book":              "📖",
  "Headphones":        "🎧",
  "Earphone":          "🎧",
  "Remote/Device":     "📡",
  "External Keyboard": "⌨️",
  "Mouse":             "🖱️",
};

// ═════════════════════════════════════════════════════════════════
// SESSION CREATION
// ═════════════════════════════════════════════════════════════════
btnCreateSession.addEventListener("click", async () => {
  const name = document.getElementById("candidateName").value.trim();
  if (!name) { showToast("Enter candidate name", "warning"); return; }

  try {
    btnCreateSession.disabled  = true;
    btnCreateSession.innerHTML = '<span class="spinner"></span> Creating...';

    const data       = await apiPost("/api/session/create", { candidate_name: name });
    sessionId        = data.session_id;
    sessionStartTime = Date.now() / 1000;
    allSessionDetections = [];

    document.getElementById("sessionSetup").classList.add("hidden");
    document.getElementById("monitorPanel").classList.remove("hidden");
    document.getElementById("currentSessionId").textContent = sessionId;
    document.getElementById("currentCandidate").textContent = name;

    addLog(`Session ${sessionId} created for ${name}`, "success");
    showToast(`Session created: ${sessionId}`, "success");

  } catch (e) {
    showToast("Failed to create session: " + e.message, "error");
    btnCreateSession.disabled  = false;
    btnCreateSession.innerHTML = "🚀 Create Session";
  }
});

// ═════════════════════════════════════════════════════════════════
// CAMERA START
// ═════════════════════════════════════════════════════════════════
btnStart.addEventListener("click", async () => {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 },
      audio: false,
    });
    video.srcObject = mediaStream;
    await video.play();

    btnStart.classList.add("hidden");
    btnRegister.classList.remove("hidden");
    document.getElementById("videoStatus").textContent  = "Camera Active";
    document.getElementById("videoStatusDot").className = "status-dot dot-green";
    addLog("Camera started", "success");

  } catch (e) {
    showToast("Camera access denied: " + e.message, "error");
    addLog("Camera error: " + e.message, "error");
  }
});

// ═════════════════════════════════════════════════════════════════
// REGISTER FACE
// ═════════════════════════════════════════════════════════════════
btnRegister.addEventListener("click", () => {
  if (!mediaStream) { showToast("Start camera first", "warning"); return; }

  // Connect WS first, then wait for it to open before sending
  connectWebSocket();

  btnRegister.disabled  = true;
  btnRegister.innerHTML = '<span class="spinner"></span> Registering...';
  addLog("Registering face… please look directly at the camera.", "info");

  // Poll until WS is open (max 3 seconds), then send register frame
  let attempts = 0;
  const tryRegister = setInterval(() => {
    attempts++;
    if (ws && ws.readyState === WebSocket.OPEN) {
      clearInterval(tryRegister);
      const frame = captureFrame(video);
      ws.send(JSON.stringify({ type: "register", frame: frame }));
    } else if (attempts >= 15) {
      // 15 × 200ms = 3 seconds timeout
      clearInterval(tryRegister);
      showToast("WebSocket did not connect. Try again.", "error");
      btnRegister.disabled  = false;
      btnRegister.innerHTML = "📸 Register Face";
    }
  }, 200);
});

// ═════════════════════════════════════════════════════════════════
// WEBSOCKET
// ═════════════════════════════════════════════════════════════════
function connectWebSocket() {
  if (ws && ws.readyState === WebSocket.OPEN) return;
  if (ws && ws.readyState === WebSocket.CONNECTING) return;

  const wsUrl = `ws://${window.location.host}/ws/${sessionId}`;
  ws          = new WebSocket(wsUrl);

  ws.onopen = () => {
    document.getElementById("wsStatus").textContent = "Connected";
    addLog("Connected to AI engine", "success");
  };

  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      handleMessage(data);
    } catch (err) {
      console.error("WS JSON parse error:", err, e.data);
    }
  };

  ws.onclose = () => {
    document.getElementById("wsStatus").textContent = "Disconnected";
    addLog("Disconnected from AI engine", "warn");
  };

  ws.onerror = (err) => {
    console.error("WS error:", err);
    addLog("WebSocket error — check console", "error");
  };
}

// ═════════════════════════════════════════════════════════════════
// MESSAGE ROUTER
// ═════════════════════════════════════════════════════════════════
function handleMessage(data) {
  console.log("WS received:", data.type, data);   // debug — visible in browser console

  switch (data.type) {

    case "register_result":
      // ── SUCCESS ────────────────────────────────────────────────
      if (data.success) {
        isRegistered = true;
        btnRegister.classList.add("hidden");
        btnEndSession.classList.remove("hidden");
        document.getElementById("btnAnalyze").classList.remove("hidden");
        addLog("✅ " + data.message, "success");
        showToast("Face registered! Monitoring started.", "success");
        startMonitoring();

      // ── FAILURE ────────────────────────────────────────────────
      } else {
        addLog("⚠️ Registration failed: " + data.message, "error");
        showToast(data.message, "error");
        btnRegister.disabled  = false;
        btnRegister.innerHTML = "📸 Register Face";
      }
      break;

    case "frame_result":
      updateFrameUI(data);
      break;

    case "error":
      addLog("Error: " + data.message, "error");
      break;

    case "pong":
      break;   // keepalive — ignore

    default:
      console.warn("Unknown WS message type:", data.type, data);
  }
}

// ═════════════════════════════════════════════════════════════════
// UPDATE UI FROM frame_result
// ═════════════════════════════════════════════════════════════════
function updateFrameUI(data) {

  // Face count
  document.getElementById("faceCount").textContent = data.face_count != null ? data.face_count : 0;

  // Identity score (0.0–1.0 float from backend → show as %)
  const idRaw = data.identity_score;
  const idEl  = document.getElementById("identityScore");
  const idBar = document.getElementById("identityBar");
  if (idRaw != null) {
    const idPct = Math.round(idRaw * 100);
    idEl.textContent         = idPct + "%";
    idBar.style.width        = idPct + "%";
    idBar.style.background   = idPct >= 45 ? "#22c55e" : "#ef4444";
  } else {
    idEl.textContent  = "—";
    idBar.style.width = "0%";
  }

  // Liveness
  const liveEl = document.getElementById("livenessStatus");
  liveEl.textContent = data.is_live === false ? "⚠️ Spoof" : "✅ Live";
  liveEl.style.color = data.is_live === false ? "#ef4444" : "#22c55e";

  // Risk
  const score = data.risk_score != null ? data.risk_score : 0;
  document.getElementById("riskScore").textContent    = score;
  document.getElementById("riskLevel").textContent    = data.risk_level || "SAFE";
  document.getElementById("riskLevel").className      = "badge " + getRiskBadgeClass(data.risk_level);
  document.getElementById("riskBar").style.width      = Math.min(score, 100) + "%";
  document.getElementById("riskBar").style.background = getRiskBarColor(score);

  // Face / liveness / absence alerts
  const evType = data.event_type;
  if (evType && evType !== "ok") {
    const msgs = {
      face_mismatch: "⚠️ Face mismatch detected",
      liveness_fail: "⚠️ Liveness failed — possible spoofing",
      multi_face:    `⚠️ Multiple faces (${data.face_count})`,
      absence:       "⚠️ Candidate absent from frame",
    };
    if (msgs[evType]) {
      addAlert(evType);
      addLog(msgs[evType], "warn");
    }
  }

  // ── YOLO detections ──────────────────────────────────────────────────────
  if (data.objects && data.objects.length > 0) {
    updateYoloBadge(data.objects);
    data.objects.forEach(function(obj) {
      allSessionDetections.push(obj);
      const relSec = sessionStartTime ? (obj.timestamp - sessionStartTime) : 0;
      addYoloLogEntry(obj.label, obj.confidence, relSec);
      addAlert("object_detected", obj.label);
      addLog(
        (OBJECT_ICONS[obj.label] || "⚠️") + " " + obj.label +
        " detected — " + Math.round(obj.confidence * 100) + "% confidence",
        "warn"
      );
    });
    updateYoloSummary(allSessionDetections);
  } else {
    updateYoloBadge([]);
  }
}

// ═════════════════════════════════════════════════════════════════
// START MONITORING — sends one frame per second
// ═════════════════════════════════════════════════════════════════
function startMonitoring() {
  if (captureInterval) clearInterval(captureInterval);

  captureInterval = setInterval(() => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const frame = captureFrame(video);
    ws.send(JSON.stringify({ type: "frame", frame: frame }));
  }, 1000);

  document.getElementById("monitorStatus").textContent = "MONITORING ACTIVE";
  document.getElementById("monitorStatus").style.color = "#22c55e";
}

// ═════════════════════════════════════════════════════════════════
// END SESSION
// ═════════════════════════════════════════════════════════════════
btnEndSession.addEventListener("click", async () => {
  if (!sessionId) return;
  if (!confirm("End this proctoring session?")) return;

  clearInterval(captureInterval);
  if (ws)          ws.close();
  if (mediaStream) mediaStream.getTracks().forEach(function(t) { t.stop(); });

  try {
    await apiPost("/api/session/" + sessionId + "/end");
    showToast("Session ended.", "success");
    addLog("Session ended.", "info");
    document.getElementById("monitorStatus").textContent = "SESSION ENDED";
    document.getElementById("monitorStatus").style.color = "#f59e0b";
    btnEndSession.disabled = true;
    document.getElementById("btnDownloadReport").classList.remove("hidden");
  } catch (e) {
    showToast("Error ending session: " + e.message, "error");
  }
});

// ═════════════════════════════════════════════════════════════════
// AI ANALYSIS
// ═════════════════════════════════════════════════════════════════
document.getElementById("btnAnalyze").addEventListener("click", async () => {
  if (!sessionId) return;
  const panel = document.getElementById("analysisPanel");
  panel.classList.remove("hidden");
  panel.innerHTML = '<div class="text-center mt-2"><span class="spinner"></span> Generating AI analysis…</div>';

  try {
    const data = await apiGet("/api/session/" + sessionId + "/analysis");
    panel.innerHTML =
      '<div class="ai-label">AI Session Summary</div>'     +
      '<div class="ai-box">' + data.summary + '</div>'     +
      '<div class="ai-label">Behaviour Analysis</div>'     +
      '<div class="ai-box">' + data.explanation + '</div>' +
      '<div class="ai-label">Compliance Recommendation</div>' +
      '<div class="ai-box">' + data.recommendation + '</div>';
  } catch (e) {
    panel.innerHTML = '<div class="text-danger">Analysis failed: ' + e.message + '</div>';
  }
});

// ═════════════════════════════════════════════════════════════════
// DOWNLOAD REPORT
// ═════════════════════════════════════════════════════════════════
document.getElementById("btnDownloadReport").addEventListener("click", () => {
  if (!sessionId) return;
  showToast("Generating PDF report…", "info");
  window.open("/api/session/" + sessionId + "/report", "_blank");
});

// ═════════════════════════════════════════════════════════════════
// YOLO UI
// ═════════════════════════════════════════════════════════════════

function updateYoloBadge(objects) {
  const badge = document.getElementById("yoloBadge");
  const text  = document.getElementById("yoloBadgeText");
  if (!objects || objects.length === 0) {
    badge.style.display = "none";
    return;
  }
  const icon          = OBJECT_ICONS[objects[0].label] || "⚠️";
  text.textContent    = icon + " " + objects[0].label + " detected";
  badge.style.display = "flex";
}

function updateYoloSummary(allDetections) {
  if (!allDetections || allDetections.length === 0) return;
  const card  = document.getElementById("yoloSummaryCard");
  const list  = document.getElementById("yoloObjectList");
  const badge = document.getElementById("yoloTotalBadge");

  card.style.display = "block";

  const groups = {};
  allDetections.forEach(function(d) {
    if (!groups[d.label]) groups[d.label] = [];
    groups[d.label].push(d);
  });

  const n           = Object.keys(groups).length;
  badge.textContent = n + " item" + (n !== 1 ? "s" : "");
  list.innerHTML    = "";

  for (const label in groups) {
    const items    = groups[label];
    const bestConf = Math.max.apply(null, items.map(function(i) { return i.confidence; }));
    const icon     = OBJECT_ICONS[label] || "⚠️";
    const row      = document.createElement("div");
    row.style.cssText =
      "display:flex;align-items:center;justify-content:space-between;" +
      "background:rgba(239,68,68,0.08);border-radius:6px;padding:0.35rem 0.6rem;";
    row.innerHTML =
      '<span style="color:#fca5a5;font-size:0.82rem;font-weight:600;">' + icon + " " + label + "</span>" +
      '<span style="color:#94a3b8;font-size:0.75rem;">' + items.length + "&times;&nbsp;&middot;&nbsp;" +
      Math.round(bestConf * 100) + "% conf</span>";
    list.appendChild(row);
  }
}

function addYoloLogEntry(label, confidence, relSeconds) {
  document.getElementById("yoloLogCard").style.display = "block";
  const log   = document.getElementById("yoloLog");
  const mins  = String(Math.floor(relSeconds / 60)).padStart(2, "0");
  const secs  = String(Math.floor(relSeconds % 60)).padStart(2, "0");
  const icon  = OBJECT_ICONS[label] || "⚠️";
  const entry = document.createElement("div");
  entry.className   = "log-entry warning";
  entry.textContent = "[" + mins + ":" + secs + "]  " + icon + " " + label +
                      " — " + Math.round(confidence * 100) + "% confidence";
  log.prepend(entry);
}

// ═════════════════════════════════════════════════════════════════
// HELPERS
// ═════════════════════════════════════════════════════════════════

function addAlert(type, label) {
  const container   = document.getElementById("alertContainer");
  const placeholder = container.querySelector(".text-muted");
  if (placeholder) placeholder.remove();

  const labels = {
    face_mismatch:   "🔴 Face Mismatch",
    liveness_fail:   "🟡 Liveness Failed",
    multi_face:      "🟠 Multiple Faces",
    absence:         "🔵 Candidate Absent",
    object_detected: "🔴 Object: " + (label || "Unknown"),
  };

  const div = document.createElement("div");
  div.className = "alert-item alert-" + type;
  div.innerHTML =
    "<strong>" + (labels[type] || type) + "</strong>" +
    '<span class="text-muted" style="margin-left:auto;font-size:0.75rem;">' +
    new Date().toLocaleTimeString() + "</span>";
  container.prepend(div);
  while (container.children.length > 20) container.removeChild(container.lastChild);
}

function addLog(msg, level) {
  level       = level || "info";
  const el    = document.getElementById("eventLog");
  const entry = document.createElement("div");
  entry.className   = "log-entry " + level;
  entry.textContent = "[" + new Date().toLocaleTimeString() + "] " + msg;
  el.prepend(entry);
  while (el.children.length > 100) el.removeChild(el.lastChild);
}

function getRiskBadgeClass(level) {
  if (!level) return "badge-safe";
  const l = level.toUpperCase();
  if (l.includes("CRITICAL") || l.includes("HIGH")) return "badge-danger";
  if (l.includes("MODERATE") || l.includes("WARNING")) return "badge-warning";
  return "badge-safe";
}

function getRiskBarColor(score) {
  if (score >= 60) return "#ef4444";
  if (score >= 30) return "#f59e0b";
  return "#22c55e";
}


// Paste in browser console to test WS manually
console.log("WS state:", ws ? ws.readyState : "null");
console.log("handleMessage exists:", typeof handleMessage);
console.log("monitor.js version check — should see register_result handler");