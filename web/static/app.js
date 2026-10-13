const $ = (id) => document.getElementById(id);

function list(el, items, fmt) {
  el.innerHTML = "";
  (items || []).forEach((x) => {
    const li = document.createElement("li");
    li.textContent = fmt ? fmt(x) : x;
    el.appendChild(li);
  });
}

async function run() {
  const period = $("period").value.trim() || "2026-W41";
  const connectors = [...document.querySelectorAll('input[name="conn"]:checked')].map((c) => c.value);
  $("status").textContent = "running…";
  $("run").disabled = true;
  try {
    const res = await fetch("/api/retro", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ period, connectors }),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const r = await res.json();
    $("r-period").textContent = `Retrospective — ${r.period}  (model: ${r.model})`;
    $("r-summary").textContent = r.summary;
    list($("r-highlights"), r.highlights);
    list($("r-issues"), r.issues);
    list($("r-roots"), r.root_causes);
    list($("r-actions"), r.action_items, (a) => `[${a.priority}] ${a.description} — ${a.owner}`);
    $("r-metrics").textContent = JSON.stringify(r.metrics, null, 2);
    list($("r-trace"), r.trace);
    list($("r-evidence"), r.evidence, (e) => `(${e.source}:${e.title}, ${e.score}) ${e.snippet.slice(0, 120)}`);
    $("report").classList.remove("hidden");
    $("status").textContent = "done";
  } catch (err) {
    $("status").textContent = "error: " + err.message;
  } finally {
    $("run").disabled = false;
  }
}

document.getElementById("run").addEventListener("click", run);
