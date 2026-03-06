// SightFlow - Shared utilities

const API_BASE = window.location.origin;

async function apiGet(path) {
  const res = await fetch(API_BASE + path);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function apiPost(path, body = {}) {
  const res = await fetch(API_BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

async function apiDelete(path) {
  const res = await fetch(API_BASE + path, { method: "DELETE" });
  return res.json();
}

function getRiskBadgeClass(level) {
  if (!level) return "badge-info";
  const l = level.toUpperCase();
  if (l.includes("HIGH")) return "badge-danger";
  if (l.includes("WARNING")) return "badge-warning";
  return "badge-safe";
}

function getRiskBarColor(score) {
  if (score >= 60) return "#ef4444";
  if (score >= 30) return "#f59e0b";
  return "#22c55e";
}

function timeAgo(dateStr) {
  const d = new Date(dateStr);
  const diff = (Date.now() - d) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  return `${Math.floor(diff/3600)}h ago`;
}

function showToast(msg, type = "info") {
  const toast = document.createElement("div");
  const colors = { info: "#06b6d4", success: "#22c55e", error: "#ef4444", warning: "#f59e0b" };
  toast.style.cssText = `
    position: fixed; bottom: 2rem; right: 2rem;
    background: #1e293b; border-left: 4px solid ${colors[type]};
    padding: 0.8rem 1.2rem; border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    color: #e2e8f0; font-size: 0.9rem; z-index: 9999;
    animation: slideIn 0.3s ease;
    max-width: 300px;
  `;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

function formatEventType(type) {
  const map = {
    face_mismatch: "🔴 Face Mismatch",
    liveness_fail: "🟡 Liveness Failed",
    multi_face: "🟠 Multiple Faces",
    absence: "🔵 Absence",
    ok: "🟢 OK",
  };
  return map[type] || type;
}

// Canvas frame capture utility
function captureFrame(video) {
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  canvas.getContext("2d").drawImage(video, 0, 0);
  return canvas.toDataURL("image/jpeg", 0.7);
}