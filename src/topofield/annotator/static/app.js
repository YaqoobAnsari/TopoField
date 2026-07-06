"use strict";
// TopoField HDG Annotator — front-end. The server is the source of truth for
// every graph edit (POST /api/op returns a validated HDG), so the UI can never
// build an invalid graph. No navigation/routing — this tool creates HDGs.

const LEVEL_COLOR = { 0: "#c9d1d9", 1: "#ff7b7b", 2: "#4ad991", 3: "#ffa94d" };
const SCALE = 820;
let HDG = null;

const $ = (id) => document.getElementById(id);
const msg = (text, ok = true) => {
  const m = $("msg"); m.hidden = false; m.textContent = text;
  m.className = "msg " + (ok ? "ok" : "err");
  if (ok) setTimeout(() => { m.hidden = true; }, 2500);
};

const cy = cytoscape({
  container: $("cy"),
  boxSelectionEnabled: true,
  wheelSensitivity: 0.2,
  style: [
    { selector: "node", style: {
      "background-color": (n) => LEVEL_COLOR[n.data("level")] || "#888",
      "label": "data(label)", "font-size": 9, "color": "#cdd6e6",
      "text-valign": "top", "text-halign": "center", "width": 16, "height": 16,
      "border-width": 1, "border-color": "#0f1420" } },
    { selector: "node[level = 3]", style: { "shape": "round-rectangle", "width": 22, "height": 14 } },
    { selector: "node[level = 2]", style: { "shape": "diamond", "width": 20, "height": 20 } },
    { selector: "node:selected", style: { "border-width": 3, "border-color": "#4f8cff" } },
    { selector: "edge", style: { "width": 2, "curve-style": "bezier", "opacity": 0.9 } },
    { selector: "edge[kind = 'containment']", style: {
      "line-color": "#5a667d", "line-style": "dashed", "width": 1, "opacity": 0.4 } },
    { selector: "edge[tau = 'door-connected']", style: { "line-color": "#4f8cff", "line-style": "solid" } },
    { selector: "edge[tau = 'wall-adjacent']", style: { "line-color": "#8b97ad", "line-style": "dotted" } },
    { selector: "edge[tau = 'corridor-link']", style: { "line-color": "#4ad991", "line-style": "dashed" } },
    { selector: "edge[directed = 'yes']", style: {
      "target-arrow-shape": "triangle", "target-arrow-color": "#ffd24d", "line-color": "#ffd24d" } },
    { selector: "edge:selected", style: { "width": 4, "line-color": "#4f8cff" } },
  ],
});

function toElements(hdg) {
  const els = [];
  const withCentroid = {};
  for (const n of hdg.nodes) {
    const c = (n.attrs || {}).centroid;
    const label = n.level === 3 ? ((n.attrs || {}).type || n.id)
      : n.level === 1 ? ((n.attrs || {}).function_label || n.id) : n.id;
    const el = { data: { id: n.id, level: n.level, label } };
    if (c) { el.position = { x: c[0] * SCALE, y: c[1] * SCALE }; withCentroid[n.id] = el.position; }
    els.push(el);
  }
  // place nodes without a centroid (building/wings): building on top, wings spread
  const wings = hdg.nodes.filter((n) => n.level === 1).map((n) => n.id);
  hdg.nodes.forEach((n) => {
    const el = els.find((e) => e.data.id === n.id);
    if (!el.position) {
      if (n.level === 0) el.position = { x: SCALE / 2, y: -90 };
      else if (n.level === 1) el.position = { x: (wings.indexOf(n.id) + 1) * SCALE / (wings.length + 1), y: -45 };
      else el.position = { x: SCALE / 2, y: SCALE / 2 };
    }
  });
  for (const e of hdg.containment_edges)
    els.push({ data: { id: `c:${e.source}->${e.target}`, source: e.source, target: e.target, kind: "containment" } });
  for (const e of hdg.adjacency_edges) {
    const directed = e.delta && e.delta !== "bidirectional" ? "yes" : "no";
    // draw arrow in the access direction: forward = source->target, backward = target->source
    const [s, t] = e.delta === "backward" ? [e.target, e.source] : [e.source, e.target];
    els.push({ data: { id: `a:${e.source}-${e.target}`, source: s, target: t, kind: "adjacency",
      tau: e.tau, delta: e.delta || "bidirectional", directed, u: e.source, v: e.target } });
  }
  return els;
}

function render(resp) {
  HDG = resp.hdg;
  cy.elements().remove();
  cy.add(toElements(HDG));
  cy.fit(undefined, 40);
  const s = resp.stats || {};
  const bl = s.nodes_by_level || {};
  $("stats").innerHTML =
    `<b>${s.num_nodes}</b> nodes — building ${bl.building || 0}, wing ${bl["wing/zone"] || 0}, `
    + `corridor ${bl.corridor || 0}, room ${bl.room || 0}<br>`
    + `<b>${s.num_adjacency_edges}</b> adjacency · <b>${s.num_containment_edges}</b> containment<br>`
    + `connectivity: <b>${(resp.navigational_completeness * 100).toFixed(1)}%</b>`;
}

async function api(path, body) {
  const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body) });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || JSON.stringify(data));
  return data;
}

async function op(name, kwargs) {
  try { render(await api("/api/op", { hdg: HDG, name, kwargs })); msg(`${name} ✓`); }
  catch (e) { msg(e.message, false); }
}

// --- selection panels ---
function refreshSelection() {
  const rooms = cy.$("node[level = 3]:selected");
  const edges = cy.$("edge[kind = 'adjacency']:selected");
  $("sel-rooms").hidden = rooms.length === 0;
  $("room-count").textContent = rooms.length;
  const edgePanel = $("sel-edge");
  if (edges.length === 1) {
    const e = edges[0];
    edgePanel.hidden = false;
    $("edge-name").textContent = `${e.data("u")} ↔ ${e.data("v")}`;
    $("edge-tau").value = e.data("tau");
    $("edge-delta").value = e.data("delta");
  } else edgePanel.hidden = true;
}
cy.on("select unselect", refreshSelection);

// --- toolbar / actions ---
$("btn-example").onclick = async () => { try { render(await (await fetch("/api/example")).json()); msg("example loaded"); } catch (e) { msg(e.message, false); } };
$("btn-assign-zone").onclick = () => {
  const label = $("zone-label").value.trim();
  if (!label) return msg("enter a function label", false);
  const ids = cy.$("node[level = 3]:selected").map((n) => n.id());
  op("assign_rooms_to_zone", { room_ids: ids, function_label: label });
};
$("edge-tau").onchange = (ev) => {
  const e = cy.$("edge[kind = 'adjacency']:selected")[0];
  if (e) op("set_edge_type", { u: e.data("u"), v: e.data("v"), tau: ev.target.value });
};
$("edge-delta").onchange = (ev) => {
  const e = cy.$("edge[kind = 'adjacency']:selected")[0];
  if (e) op("set_edge_direction", { source: e.data("u"), target: e.data("v"), delta: ev.target.value });
};
$("btn-remove-edge").onclick = () => {
  const e = cy.$("edge[kind = 'adjacency']:selected")[0];
  if (e) op("remove_adjacency", { u: e.data("u"), v: e.data("v") });
};
$("btn-validate").onclick = async () => {
  try { const r = await api("/api/validate", { hdg: HDG });
    msg(r.ok ? "HDG is valid ✓" : r.errors.join("\n"), r.ok); }
  catch (e) { msg(e.message, false); }
};
$("btn-export").onclick = () => {
  if (!HDG) return msg("nothing to export", false);
  const blob = new Blob([JSON.stringify(HDG, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${(HDG.metadata || {}).building_id || "graph"}.hdg.json`;
  a.click();
};

function readFile(input, handler) {
  const f = input.files[0]; if (!f) return;
  const rd = new FileReader();
  rd.onload = () => { try { handler(JSON.parse(rd.result)); } catch (e) { msg("bad JSON: " + e.message, false); } };
  rd.readAsText(f); input.value = "";
}
$("file-tess").onchange = (ev) => readFile(ev.target, async (j) => {
  try { render(await api("/api/extract", { tesseract: j, building_id: (j.building_id || "building") })); msg("extracted → HDG"); }
  catch (e) { msg(e.message, false); }
});
$("file-hdg").onchange = (ev) => readFile(ev.target, async (j) => {
  try { render(await api("/api/op", { hdg: j, name: "set_function_label",
    kwargs: { zone_id: (j.nodes.find((n) => n.level === 1) || {}).id, function_label:
      (j.nodes.find((n) => n.level === 1) || { attrs: {} }).attrs.function_label || "unassigned" } }));
    msg("HDG loaded"); }
  catch { render({ hdg: j, stats: {}, navigational_completeness: 0 }); msg("HDG loaded (unverified)", false); }
});
