/**
 * viewer.js — Renders the interactive text block heat map visualization.
 *
 * - renderTextBlockMap(textBlocks): draws colored text region blocks on the
 *   canvas element, color-coded by parse order. Hovering shows block content.
 *
 * Simulates the visual of what an ATS parser "sees" as it reads through
 * each text region of the PDF in order.
 */

(function () {
  "use strict";

  const PARSE_ORDER_COLORS = [
    "#3b82f6", // blue
    "#22c55e", // green
    "#f59e0b", // amber
    "#ef4444", // red
    "#a855f7", // purple
    "#06b6d4", // cyan
    "#f97316", // orange
    "#84cc16", // lime
    "#ec4899", // pink
    "#14b8a6", // teal
  ];

  function renderTextBlockMap(textBlocks) {
    const canvas = document.getElementById("block-canvas");
    if (!canvas || !textBlocks || textBlocks.length === 0) return;

    canvas.innerHTML = "";

    // Create a page-like white document background
    const docBg = document.createElement("div");
    docBg.className =
      "absolute bg-white border border-gray-300 shadow-md rounded";
    docBg.style.cssText =
      "left: 10%; top: 2%; width: 80%; height: 96%; pointer-events: none;";
    canvas.appendChild(docBg);

    // Tooltip element
    const tooltip = document.createElement("div");
    tooltip.className =
      "absolute z-50 bg-gray-900 text-white text-xs rounded-lg px-3 py-2 max-w-xs shadow-xl pointer-events-none hidden";
    tooltip.style.maxWidth = "200px";
    canvas.appendChild(tooltip);

    // Sort blocks by their parse order (y then x, top-to-bottom, left-to-right)
    const sorted = [...textBlocks].sort((a, b) => {
      const yDiff = a.y - b.y;
      if (Math.abs(yDiff) > 3) return yDiff;
      return a.x - b.x;
    });

    sorted.forEach((block, index) => {
      if (!block.text || block.text.trim().length === 0) return;

      const el = document.createElement("div");
      el.className =
        "absolute cursor-pointer rounded text-white flex items-center justify-center overflow-hidden transition-all hover:z-40 hover:shadow-lg";

      // Map from 0-100% coordinate space to the doc area (10%-90% horizontal, 2%-98% vertical)
      const leftPct = 10 + block.x * 0.8;
      const topPct = 2 + block.y * 0.96;
      const widthPct = block.width * 0.8;
      const heightPct = Math.max(block.height * 0.96, 1.5);

      el.style.cssText = `
        left: ${Math.min(leftPct, 88)}%;
        top: ${Math.min(topPct, 95)}%;
        width: ${Math.min(widthPct, 80)}%;
        height: ${Math.max(heightPct, 1.5)}%;
        background-color: ${PARSE_ORDER_COLORS[index % PARSE_ORDER_COLORS.length]}cc;
        border: 1px solid ${PARSE_ORDER_COLORS[index % PARSE_ORDER_COLORS.length]};
        font-size: 9px;
        padding: 1px 3px;
        z-index: ${10 + index};
      `;

      // Parse order number badge
      const badge = document.createElement("span");
      badge.className =
        "absolute top-0.5 left-0.5 bg-black bg-opacity-40 text-white rounded text-xs font-bold px-1 leading-tight";
      badge.style.fontSize = "7px";
      badge.textContent = index + 1;
      el.appendChild(badge);

      // Truncated text preview
      const preview = document.createElement("span");
      preview.className = "truncate block w-full text-center";
      preview.style.fontSize = "7px";
      preview.style.opacity = "0.9";
      preview.textContent = block.text.replace(/\n/g, " ").trim().slice(0, 40);
      el.appendChild(preview);

      // Hover tooltip
      el.addEventListener("mouseenter", (e) => {
        const rect = canvas.getBoundingClientRect();
        const elRect = el.getBoundingClientRect();

        tooltip.innerHTML = `
          <div class="font-bold text-yellow-300 mb-1">Block #${index + 1} (parse order)</div>
          <div class="text-gray-300 mb-1" style="font-size:10px">Font size: ${block.font_size || "?"}pt · Page ${block.page || 1}</div>
          <div class="text-white leading-snug" style="font-size:10px">${escapeForTooltip(block.text.slice(0, 120))}${block.text.length > 120 ? "…" : ""}</div>
        `;

        let tipLeft = elRect.left - rect.left + el.offsetWidth + 8;
        let tipTop = elRect.top - rect.top;

        // Prevent overflow right
        if (tipLeft + 210 > canvas.offsetWidth) {
          tipLeft = elRect.left - rect.left - 218;
        }
        if (tipTop + 120 > canvas.offsetHeight) {
          tipTop = canvas.offsetHeight - 130;
        }

        tooltip.style.left = Math.max(0, tipLeft) + "px";
        tooltip.style.top = Math.max(0, tipTop) + "px";
        tooltip.classList.remove("hidden");

        el.style.outline = "2px solid white";
        el.style.zIndex = 100;
      });

      el.addEventListener("mouseleave", () => {
        tooltip.classList.add("hidden");
        el.style.outline = "";
        el.style.zIndex = 10 + index;
      });

      canvas.appendChild(el);
    });

    // Parse order legend
    const legend = document.createElement("div");
    legend.className =
      "absolute bottom-2 right-2 bg-white bg-opacity-90 rounded-lg p-2 text-xs text-gray-500 border border-gray-200";
    legend.innerHTML = `
      <div class="font-semibold text-gray-700 mb-1">Parse Order</div>
      <div class="flex items-center gap-1 mb-0.5">
        <span class="w-3 h-3 rounded inline-block" style="background:#3b82f6cc"></span> First read
      </div>
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded inline-block" style="background:#ef4444cc"></span> Later blocks
      </div>
      <div class="text-gray-400 mt-1 text-xs">Hover blocks to inspect</div>
    `;
    canvas.appendChild(legend);
  }

  function escapeForTooltip(text) {
    return (text || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/\n/g, " ");
  }

  window.renderTextBlockMap = renderTextBlockMap;
})();
