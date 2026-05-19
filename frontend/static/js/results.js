/**
 * results.js — Renders all result panels from API response data.
 *
 * - renderResults(data, filename, fileSize): main render entry point
 * - renderScoreCircles(data): animates the three circular progress rings
 * - renderQuickStats(data): populates metadata stats bar
 * - renderIssues(issues): builds issue cards in the issues tab
 * - renderSections(parsed_sections, detected_sections): shows section breakdown
 * - renderPositives(positives, suggestions): shows what works + suggestions
 */

function renderResults(data, filename, fileSize) {
  renderFileInfo(filename, fileSize, data.metadata);
  renderScoreCircles(data);
  renderQuickStats(data);
  renderIssues(data.issues || []);
  renderAtsView(data.ats_visible_text || "", data.text_blocks || [], data.metadata);
  renderSections(data.parsed_sections || {}, data.detected_sections || []);
  renderPositives(data.positives || [], data.suggestions || []);
}

// --- FILE INFO BAR ---
function renderFileInfo(filename, fileSize, metadata) {
  document.getElementById("result-filename").textContent = filename;
  const sizeMB = (fileSize / 1024 / 1024).toFixed(2);
  const pages = metadata.page_count || 1;
  const words = metadata.word_count || 0;
  const ft = (metadata.file_type || "").toUpperCase();
  document.getElementById("result-meta").textContent =
    `${ft} · ${sizeMB} MB · ${pages} page${pages !== 1 ? "s" : ""} · ${words} words extracted`;
}

// --- SCORE CIRCLES ---
function renderScoreCircles(data) {
  const CIRCUMFERENCE = 440;

  function animateCircle(circleId, scoreId, score, color) {
    const circle = document.getElementById(circleId);
    const scoreEl = document.getElementById(scoreId);
    if (!circle || !scoreEl) return;

    const offset = CIRCUMFERENCE - (score / 100) * CIRCUMFERENCE;
    circle.style.stroke = color;

    // Animate stroke
    setTimeout(() => {
      circle.style.transition = "stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1)";
      circle.style.strokeDashoffset = offset;
    }, 100);

    // Count up number
    let current = 0;
    const duration = 1200;
    const step = duration / score;
    const counter = setInterval(() => {
      current = Math.min(current + 1, score);
      scoreEl.textContent = current;
      if (current >= score) clearInterval(counter);
    }, step);
  }

  const grade = data.grade || {};
  const gradeColor = grade.color || "#0ea5e9";

  animateCircle("circle-overall", "score-overall", data.overall_score || 0, gradeColor);
  animateCircle("circle-readability", "score-readability", data.readability_score || 0, "#22c55e");
  animateCircle("circle-ats", "score-ats", data.ats_score || 0, "#a855f7");

  // Grade badge
  const badge = document.getElementById("grade-badge");
  if (badge && grade.letter) {
    badge.textContent = `${grade.letter} — ${grade.label}`;
    badge.style.backgroundColor = gradeColor + "20";
    badge.style.color = gradeColor;
    badge.style.border = `1px solid ${gradeColor}40`;
  }
}

// --- QUICK STATS ---
function renderQuickStats(data) {
  const m = data.metadata || {};
  const stats = [
    {
      label: "Words Extracted",
      value: m.word_count || 0,
      icon: "📝",
      good: m.word_count >= 150,
    },
    {
      label: "Pages",
      value: m.page_count || 1,
      icon: "📄",
      good: m.page_count <= 2,
    },
    {
      label: "Images Found",
      value: m.has_images ? "Yes ⚠️" : "None ✓",
      icon: "🖼",
      good: !m.has_images,
    },
    {
      label: "Multi-Column",
      value: m.has_columns ? "Yes ⚠️" : "No ✓",
      icon: "⬛",
      good: !m.has_columns,
    },
  ];

  const container = document.getElementById("quick-stats");
  container.innerHTML = stats
    .map(
      (s) => `
    <div class="text-center">
      <p class="text-2xl mb-0.5">${s.icon}</p>
      <p class="font-bold text-lg ${s.good ? "text-gray-900" : "text-orange-600"}">${s.value}</p>
      <p class="text-xs text-gray-400">${s.label}</p>
    </div>
  `
    )
    .join("");
}

// --- ISSUES ---
const SEVERITY_CONFIG = {
  critical: { color: "red", label: "Critical", dot: "bg-red-500", border: "border-red-300", bg: "bg-red-50" },
  high: { color: "orange", label: "High", dot: "bg-orange-500", border: "border-orange-300", bg: "bg-orange-50" },
  medium: { color: "yellow", label: "Medium", dot: "bg-yellow-500", border: "border-yellow-300", bg: "bg-yellow-50" },
  low: { color: "green", label: "Low", dot: "bg-green-500", border: "border-green-300", bg: "bg-green-50" },
};

const CATEGORY_LABELS = {
  readability: "Readability",
  ats_structure: "ATS Structure",
  contact: "Contact Info",
};

function renderIssues(issues) {
  const container = document.getElementById("tab-issues");
  const countBadge = document.getElementById("issues-count");

  countBadge.textContent = issues.length;

  if (issues.length === 0) {
    container.innerHTML = `
      <div class="bg-green-50 border border-green-200 rounded-2xl p-8 text-center">
        <div class="text-5xl mb-3">🎉</div>
        <h3 class="font-bold text-green-800 text-lg">No issues found!</h3>
        <p class="text-green-600 mt-1">Your resume appears to be highly ATS-compatible.</p>
      </div>
    `;
    return;
  }

  // Group by severity
  const grouped = { critical: [], high: [], medium: [], low: [] };
  issues.forEach((issue) => {
    const sev = issue.severity || "low";
    if (grouped[sev]) grouped[sev].push(issue);
  });

  let html = "";

  Object.entries(grouped).forEach(([sev, sevIssues]) => {
    if (sevIssues.length === 0) return;
    const cfg = SEVERITY_CONFIG[sev];
    html += sevIssues
      .map(
        (issue) => `
      <div class="issue-card bg-white border border-l-4 ${cfg.border} rounded-xl p-4 shadow-sm sev-${sev} cursor-default">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-start gap-3 flex-1">
            <span class="inline-block w-2 h-2 rounded-full ${cfg.dot} mt-1.5 shrink-0"></span>
            <div class="flex-1">
              <div class="flex items-center gap-2 flex-wrap mb-1">
                <span class="text-xs font-bold uppercase tracking-wide text-${cfg.color}-600 ${cfg.bg} px-2 py-0.5 rounded">${cfg.label}</span>
                <span class="text-xs text-gray-400">${CATEGORY_LABELS[issue.category] || issue.category}</span>
              </div>
              <p class="font-semibold text-gray-800 text-sm">${escapeHtml(issue.title)}</p>
              <p class="text-gray-500 text-sm mt-1 leading-relaxed">${escapeHtml(issue.detail)}</p>
            </div>
          </div>
          <div class="shrink-0 text-right">
            <span class="text-xs font-bold text-red-600 bg-red-50 px-2 py-1 rounded-lg whitespace-nowrap">−${issue.points_lost} pts</span>
          </div>
        </div>
      </div>
    `
      )
      .join("");
  });

  container.innerHTML = html;
}

// --- ATS VIEW ---
function renderAtsView(atsText, textBlocks, metadata) {
  const content = document.getElementById("ats-view-content");
  if (!content) return;

  // Highlight special character replacements
  let displayText = escapeHtml(atsText);

  // Highlight warning lines
  displayText = displayText.replace(
    /(\[COLUMN PARSING WARNING[^\]]*\])/g,
    '<span class="bg-red-100 text-red-700 font-bold px-1 rounded">$1</span>'
  );
  displayText = displayText.replace(
    /(\[TABLE CONTENT[^\]]*\])/g,
    '<span class="bg-orange-100 text-orange-700 font-bold px-1 rounded">$1</span>'
  );

  // Highlight replacement characters
  displayText = displayText.replace(
    /(\?{3,})/g,
    '<span class="ats-unreadable">$1</span>'
  );

  content.innerHTML = displayText || '<span class="text-gray-400 italic">No text could be extracted from this document.</span>';

  // Show text block visualizer for PDFs
  if (metadata.file_type === "pdf" && textBlocks.length > 0) {
    const vizEl = document.getElementById("text-block-viz");
    if (vizEl) {
      vizEl.classList.remove("hidden");
      renderTextBlockMap(textBlocks);
    }
  }
}

// --- SECTIONS TAB ---
const SECTION_COLORS = {
  contact: "section-contact",
  experience: "section-experience",
  education: "section-education",
  skills: "section-skills",
  summary: "section-summary",
};

const SECTION_ICONS = {
  contact: "📞",
  experience: "💼",
  education: "🎓",
  skills: "⚡",
  summary: "👤",
  projects: "🚀",
  certifications: "🏅",
  awards: "🏆",
  languages: "🌍",
  publications: "📚",
  volunteer: "🤝",
};

const CRITICAL_SECTIONS = ["contact", "experience", "education", "skills"];

function renderSections(parsedSections, detectedSections) {
  const container = document.getElementById("sections-content");

  // Show all critical sections, mark missing ones
  const allSections = new Set([...CRITICAL_SECTIONS, ...detectedSections]);
  let html = "";

  // Missing sections first
  const missing = CRITICAL_SECTIONS.filter((s) => !detectedSections.includes(s));
  if (missing.length > 0) {
    html += `
      <div class="bg-red-50 border border-red-200 rounded-xl p-4 mb-2">
        <p class="font-semibold text-red-700 text-sm mb-1">⚠️ Missing critical sections</p>
        <p class="text-red-600 text-sm">ATS systems couldn't find: <strong>${missing.map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join(", ")}</strong>. Add clearly labeled section headers using these exact words.</p>
      </div>
    `;
  }

  // Detected sections
  detectedSections.forEach((section) => {
    const content = parsedSections[section] || "";
    const colorClass = SECTION_COLORS[section] || "section-other";
    const icon = SECTION_ICONS[section] || "📌";
    const label = section.charAt(0).toUpperCase() + section.slice(1);
    const preview = content ? content.slice(0, 300) : "Section header detected but content could not be extracted.";
    const hasContent = !!content;

    html += `
      <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
        <div class="${colorClass} px-4 py-3 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-lg">${icon}</span>
            <span class="font-bold text-gray-800">${label}</span>
          </div>
          <span class="text-xs font-semibold ${hasContent ? "text-green-600 bg-green-50" : "text-orange-600 bg-orange-50"} px-2 py-0.5 rounded-full">
            ${hasContent ? "✓ Readable" : "⚠ Partial"}
          </span>
        </div>
        ${
          preview
            ? `<div class="px-4 py-3">
          <p class="font-mono text-xs text-gray-600 leading-relaxed whitespace-pre-wrap bg-gray-50 rounded p-3 border border-gray-100 max-h-32 overflow-y-auto">${escapeHtml(preview)}${content.length > 300 ? "…" : ""}</p>
          <p class="text-xs text-gray-400 mt-1.5">↑ What the ATS parser reads from this section</p>
        </div>`
            : ""
        }
      </div>
    `;
  });

  container.innerHTML = html || `<div class="text-center text-gray-400 py-12">No sections detected in this document.</div>`;
}

// --- POSITIVES & SUGGESTIONS ---
function renderPositives(positives, suggestions) {
  const list = document.getElementById("positives-list");
  const sugBlock = document.getElementById("suggestions-block");
  const sugList = document.getElementById("suggestions-list");

  if (positives.length === 0) {
    list.innerHTML = `<p class="text-gray-400 text-sm">No particular strengths detected. Focus on fixing the issues listed above.</p>`;
  } else {
    list.innerHTML = positives
      .map(
        (p) => `
      <div class="flex items-start gap-3 p-3 bg-green-50 rounded-lg border border-green-100">
        <span class="text-green-500 mt-0.5 shrink-0">✓</span>
        <p class="text-sm text-green-800">${escapeHtml(p)}</p>
      </div>
    `
      )
      .join("");
  }

  if (suggestions.length > 0) {
    sugBlock.classList.remove("hidden");
    sugList.innerHTML = suggestions
      .map(
        (s, i) => `
      <div class="flex items-start gap-3 p-3 bg-sky-50 rounded-lg border border-sky-100">
        <span class="text-sky-500 font-bold text-sm shrink-0">${i + 1}.</span>
        <p class="text-sm text-sky-800">${escapeHtml(s)}</p>
      </div>
    `
      )
      .join("");
  }
}

// --- UTILITY ---
function escapeHtml(text) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(text || ""));
  return div.innerHTML;
}

window.renderResults = renderResults;
