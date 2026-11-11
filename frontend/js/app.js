/*
  app.js

  Draws the page and handles what the user clicks.
  All data goes through api.js.
*/

import {
  backend,
  checkVin,
  getSettings,
  setSettings,
  resetDemoData,
} from "./api.js";

const $ = (selector) => document.querySelector(selector);

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});
const moneyCents = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const miles = new Intl.NumberFormat("en-US");

const state = {
  view: "lot",
  cars: [],
  loaded: false,
  openId: null,
};

/* ---------- Small helpers ---------- */

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else node.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children) {
    if (child === null || child === undefined) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

function carName(v) {
  return [v.year, titleCase(v.make), v.model, v.trim].filter(Boolean).join(" ") || "Unnamed vehicle";
}

function titleCase(text) {
  if (!text) return "";
  if (text.length <= 3) return text; // keep BMW, GMC, KIA as they are
  return text.charAt(0) + text.slice(1).toLowerCase();
}

function signedMoney(value) {
  if (value === null || value === undefined) return "–";
  return value < 0 ? `−${money.format(Math.abs(value))}` : money.format(value);
}

function toneClass(value) {
  if (value === null || value === undefined) return "";
  return value < 0 ? "loss" : "gain";
}

function setNote(target, message, tone = "error") {
  target.textContent = message || "";
  target.dataset.tone = message ? tone : "";
}

let toastTimer;
function toast(message) {
  const node = $("#toast");
  node.textContent = message;
  clearTimeout(toastTimer);
  // Shown as a popover so it sits above the car panel when that is open.
  if (node.showPopover) {
    try {
      node.hidePopover();
    } catch {
      // not open yet
    }
    node.showPopover();
  }
  requestAnimationFrame(() => node.classList.add("show"));
  toastTimer = setTimeout(() => {
    node.classList.remove("show");
    setTimeout(() => {
      try {
        node.hidePopover();
      } catch {
        // already closed
      }
    }, 200);
  }, 2600);
}

function numberOrNull(value) {
  if (value === "" || value === null || value === undefined) return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function textOrNull(value) {
  const t = (value || "").trim();
  return t === "" ? null : t;
}

/* ---------- Data source switch ---------- */

function renderSource() {
  const { mode, apiUrl } = getSettings();
  document.querySelectorAll(".segmented button").forEach((button) => {
    button.setAttribute("aria-checked", String(button.dataset.mode === mode));
  });
  $("#api-url-form").hidden = mode !== "api";
  $("#api-url").value = apiUrl;
  $("#reset-demo").hidden = mode !== "demo";
}

async function checkConnection() {
  const status = $("#status");
  const { mode, apiUrl } = getSettings();
  if (mode === "demo") {
    status.textContent = "Sample cars saved in this browser only.";
    status.dataset.tone = "";
    return true;
  }
  status.textContent = `Checking ${apiUrl}…`;
  status.dataset.tone = "";
  try {
    await backend().ping();
    status.textContent = `Connected to ${apiUrl}`;
    status.dataset.tone = "ok";
    return true;
  } catch (error) {
    status.textContent = error.message;
    status.dataset.tone = "error";
    return false;
  }
}

/* ---------- Ledger ---------- */

async function renderLedger() {
  let totals;
  try {
    totals = await backend().summary();
  } catch {
    totals = null;
  }
  document.querySelectorAll("#ledger dd").forEach((dd) => {
    const key = dd.dataset.key;
    const value = totals ? totals[key] : null;
    dd.classList.remove("gain", "loss");
    if (value === null || value === undefined) {
      dd.textContent = "–";
    } else if (key === "inventory_count" || key === "vehicles_sold") {
      dd.textContent = value;
    } else if (key.includes("profit")) {
      dd.textContent = signedMoney(value);
      dd.classList.add(toneClass(value));
    } else {
      dd.textContent = money.format(value);
    }
  });
}

/* ---------- Inventory cards ---------- */

function daysOnLot(createdAt) {
  if (!createdAt) return null;
  const days = Math.floor((Date.now() - new Date(createdAt).getTime()) / 86400000);
  return days < 0 ? 0 : days;
}

function carCard({ vehicle: v, financials: f }) {
  const sold = v.status === "sold";
  const price = sold ? v.sale_price : v.asking_price;
  const days = daysOnLot(v.created_at);

  const glass = el(
    "div",
    { class: "glass", "aria-hidden": "true" },
    el("span", { class: "marker-year", text: v.year || "" }),
    el("span", { class: "marker-price", text: price ? money.format(price).replace("$", "$ ") : "Ask" }),
    sold ? el("span", { class: "marker-sold", text: "Sold" }) : null
  );

  const facts = [];
  if (v.mileage !== null && v.mileage !== undefined) facts.push(`${miles.format(v.mileage)} mi`);
  if (v.color) facts.push(v.color);
  if (!sold && days !== null) facts.push(days === 1 ? "1 day on lot" : `${days} days on lot`);

  const profit = sold ? f.actual_profit : f.projected_profit;

  const button = el(
    "button",
    { type: "button", class: `car${sold ? " car-sold" : ""}`, "data-id": v.id },
    glass,
    el(
      "div",
      { class: "car-body" },
      el("h3", { class: "car-name", text: carName(v) }),
      el("p", { class: "car-facts", text: facts.join(", ") }),
      el(
        "dl",
        { class: "car-money" },
        el("div", {}, el("dt", { text: "Into it" }), el("dd", { text: money.format(f.total_investment) })),
        el(
          "div",
          {},
          el("dt", { text: sold ? "Profit" : "Profit at sticker" }),
          el("dd", { class: toneClass(profit), text: signedMoney(profit) })
        )
      ),
      el("p", { class: "car-vin", text: `VIN ${v.vin}` })
    )
  );
  button.setAttribute("aria-label", `${carName(v)}, ${sold ? "sold for" : "asking"} ${price ? money.format(price) : "no price set"}. Open details.`);
  return button;
}

function renderCars() {
  const container = $("#cars");
  container.replaceChildren();

  const onLot = state.cars.filter((c) => c.vehicle.status !== "sold");
  const sold = state.cars.filter((c) => c.vehicle.status === "sold");
  $("#count-lot").textContent = onLot.length;
  $("#count-sold").textContent = sold.length;

  const list = state.view === "sold" ? sold : onLot;
  // Oldest stock first on the lot so aging cars stay visible; newest sales first.
  list.sort((a, b) => {
    const ta = new Date(a.vehicle.created_at || 0).getTime();
    const tb = new Date(b.vehicle.created_at || 0).getTime();
    return state.view === "sold" ? tb - ta : ta - tb;
  });

  if (list.length === 0) {
    const message =
      state.view === "sold"
        ? "No sales yet. Open a car on the lot and use Mark as sold when it goes."
        : "No cars on the lot yet. Add your first one with its VIN.";
    if (state.loaded && state.view === "lot" && state.cars.length === 0) showIntake(true, { focus: false });
    container.append(el("p", { class: "empty", text: message }));
    return;
  }
  for (const car of list) container.append(carCard(car));
}

async function loadCars() {
  try {
    state.cars = await backend().listVehicles();
    state.loaded = true;
  } catch (error) {
    state.cars = [];
    state.loaded = false;
    $("#cars").replaceChildren(el("p", { class: "empty empty-error", text: error.message }));
    $("#count-lot").textContent = "0";
    $("#count-sold").textContent = "0";
    return;
  }
  renderCars();
}

async function refreshAll() {
  await Promise.all([loadCars(), renderLedger()]);
}

/* ---------- Tabs ---------- */

function setView(view) {
  state.view = view;
  document.querySelectorAll(".tabs [role=tab]").forEach((tab) => {
    const selected = tab.dataset.view === view;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  $("#cars").setAttribute("aria-labelledby", view === "sold" ? "tab-sold" : "tab-lot");
  renderCars();
}

/* ---------- Add a car ---------- */

function showIntake(show, { focus = true } = {}) {
  $("#intake").hidden = !show;
  $("#intake-open").hidden = show;
  $("#intake-open").setAttribute("aria-expanded", String(show));
  if (show && focus) $("#vin").focus();
  if (!show) {
    $("#add-form").reset();
    setNote($("#vin-note"), "");
    setNote($("#add-note"), "");
  }
}

async function decodeVin() {
  const note = $("#vin-note");
  const check = checkVin($("#vin").value);
  $("#vin").value = check.vin;
  if (!check.ok) {
    setNote(note, check.message);
    $("#vin").focus();
    return;
  }
  const button = $("#decode-btn");
  button.disabled = true;
  button.textContent = "Decoding…";
  setNote(note, "");
  try {
    const info = await backend().decodeVin(check.vin);
    for (const key of ["year", "make", "model", "trim", "body_type", "fuel_type"]) {
      if (info[key]) $(`#${key}`).value = key === "make" ? titleCase(info[key]) : info[key];
    }
    const found = [info.year, info.make, info.model].filter(Boolean).join(" ");
    setNote(note, found ? `Found: ${found}. Check the trim, then add color, miles and prices.` : "Decoded, but NHTSA had few details. Fill in the rest by hand.", "ok");
    $("#color").focus();
  } catch (error) {
    setNote(note, error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Decode VIN";
  }
}

async function addCar(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const note = $("#add-note");
  const check = checkVin(form.vin.value);
  form.vin.value = check.vin;
  if (!check.ok) {
    setNote($("#vin-note"), check.message);
    form.vin.focus();
    return;
  }
  const mileage = numberOrNull(form.mileage.value);
  const paid = numberOrNull(form.purchase_price.value) ?? 0;
  const asking = numberOrNull(form.asking_price.value) ?? 0;
  if ((mileage !== null && mileage < 0) || paid < 0 || asking < 0) {
    setNote(note, "Miles and prices can't be negative.");
    return;
  }
  const data = {
    vin: check.vin,
    year: textOrNull(form.year.value),
    make: textOrNull(form.make.value),
    model: textOrNull(form.model.value),
    trim: textOrNull(form.trim.value),
    body_type: textOrNull(form.body_type.value),
    fuel_type: textOrNull(form.fuel_type.value),
    color: textOrNull(form.color.value),
    mileage: mileage === null ? null : Math.round(mileage),
    purchase_price: paid,
    asking_price: asking,
  };
  const submit = form.querySelector("[type=submit]");
  submit.disabled = true;
  try {
    const created = await backend().createVehicle(data);
    showIntake(false, { focus: false });
    toast(`Added ${carName(created)} to inventory`);
    setView("lot");
    await refreshAll();
  } catch (error) {
    setNote(note, error.message);
  } finally {
    submit.disabled = false;
  }
}

/* ---------- Car detail sheet ---------- */

function moneyRow(label, value, { tone = false, strong = false } = {}) {
  let text = "–";
  if (value !== null && value !== undefined) {
    text = value < 0 ? `−${moneyCents.format(Math.abs(value))}` : moneyCents.format(value);
  }
  const cell = el("td", { text });
  if (tone) cell.className = toneClass(value);
  const row = el("tr", strong ? { class: "strong" } : {}, el("th", { scope: "row", text: label }), cell);
  return row;
}

async function openCar(id) {
  state.openId = Number(id);
  const sheet = $("#sheet");
  setNote($("#expense-note"), "");
  setNote($("#sell-note"), "");
  $("#expense-form").reset();
  $("#sell-form").reset();
  await renderSheet();
  if (!sheet.open) sheet.showModal();
}

async function renderSheet() {
  let detail;
  let expenses;
  try {
    [detail, expenses] = await Promise.all([
      backend().getVehicle(state.openId),
      backend().listExpenses(state.openId),
    ]);
  } catch (error) {
    toast(error.message);
    return;
  }
  const v = detail.vehicle;
  const f = detail.financials;
  const sold = v.status === "sold";

  $("#sheet-title").textContent = carName(v);
  $("#sheet-vin").textContent = `VIN ${v.vin}`;

  const specs = [
    ["Status", sold ? "Sold" : "On the lot"],
    ["Miles", v.mileage !== null && v.mileage !== undefined ? miles.format(v.mileage) : "–"],
    ["Color", v.color || "–"],
    ["Body", v.body_type || "–"],
    ["Fuel", v.fuel_type || "–"],
  ];
  $("#sheet-specs").replaceChildren(
    ...specs.map(([k, val]) => el("div", {}, el("dt", { text: k }), el("dd", { text: val })))
  );

  const rows = [
    moneyRow("Paid", v.purchase_price),
    moneyRow("Costs", f.total_expenses),
    moneyRow("Total into it", f.total_investment, { strong: true }),
    moneyRow("Asking", v.asking_price),
  ];
  if (sold) {
    rows.push(moneyRow("Sold for", v.sale_price));
    rows.push(moneyRow("Profit", f.actual_profit, { tone: true, strong: true }));
    rows.push(
      el(
        "tr",
        {},
        el("th", { scope: "row", text: "Return on money in" }),
        el("td", { class: toneClass(f.roi), text: f.roi === null ? "–" : `${f.roi.toFixed(1)}%` })
      )
    );
  } else {
    rows.push(moneyRow("Profit at sticker", f.projected_profit, { tone: true, strong: true }));
  }
  $("#sheet-money").replaceChildren(el("tbody", {}, ...rows));

  const costs = $("#sheet-costs");
  if (expenses.length === 0) {
    costs.replaceChildren(el("li", { class: "costs-empty", text: "No costs logged yet. Add detail, repairs, transport and fees as they happen." }));
  } else {
    costs.replaceChildren(
      ...expenses.map((e) =>
        el(
          "li",
          {},
          el("span", { class: "cost-cat", text: e.category }),
          el("span", { class: "cost-desc", text: e.description || "" }),
          el("span", { class: "cost-amt", text: moneyCents.format(e.amount) })
        )
      )
    );
  }

  $("#sell-section").hidden = sold;
  if (!sold && v.asking_price) $("#sale-price").placeholder = String(v.asking_price);
}

async function addExpense(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const note = $("#expense-note");
  const amount = numberOrNull(form.amount.value);
  if (amount === null || amount <= 0) {
    setNote(note, "Enter an amount above $0.");
    form.amount.focus();
    return;
  }
  try {
    await backend().addExpense(state.openId, {
      category: form.category.value,
      description: textOrNull(form.description.value),
      amount,
    });
    form.reset();
    setNote(note, "");
    toast(`Cost added: ${moneyCents.format(amount)}`);
    await Promise.all([renderSheet(), refreshAll()]);
  } catch (error) {
    setNote(note, error.message);
  }
}

async function sellCar(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const note = $("#sell-note");
  const price = numberOrNull(form.sale_price.value);
  if (price === null || price <= 0) {
    setNote(note, "Enter the sale price.");
    form.sale_price.focus();
    return;
  }
  try {
    const result = await backend().sellVehicle(state.openId, price);
    const profit = result.financials ? result.financials.actual_profit : null;
    toast(`Marked as sold. Profit ${signedMoney(profit)}`);
    await Promise.all([renderSheet(), refreshAll()]);
  } catch (error) {
    setNote(note, error.message);
  }
}

/* ---------- Wire up ---------- */

function bind() {
  document.querySelectorAll(".segmented button").forEach((button) => {
    button.addEventListener("click", async () => {
      setSettings({ mode: button.dataset.mode });
      renderSource();
      await checkConnection();
      await refreshAll();
    });
  });

  $("#api-url-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const value = $("#api-url").value.trim();
    if (!value) return;
    setSettings({ apiUrl: value });
    await checkConnection();
    await refreshAll();
  });

  $("#reset-demo").addEventListener("click", async () => {
    resetDemoData();
    toast("Demo data reset");
    await refreshAll();
  });

  document.querySelectorAll(".tabs [role=tab]").forEach((tab) => {
    tab.addEventListener("click", () => setView(tab.dataset.view));
    tab.addEventListener("keydown", (event) => {
      if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
        const next = tab.dataset.view === "lot" ? "sold" : "lot";
        setView(next);
        document.querySelector(`[data-view=${next}]`).focus();
      }
    });
  });

  $("#intake-open").addEventListener("click", () => showIntake(true));
  $("#intake-close").addEventListener("click", () => {
    showIntake(false);
    $("#intake-open").focus();
  });
  $("#decode-btn").addEventListener("click", decodeVin);
  $("#vin").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      decodeVin();
    }
  });
  $("#add-form").addEventListener("submit", addCar);

  $("#cars").addEventListener("click", (event) => {
    const card = event.target.closest(".car");
    if (card) openCar(card.dataset.id);
  });

  const sheet = $("#sheet");
  $("#sheet-close").addEventListener("click", () => sheet.close());
  sheet.addEventListener("click", (event) => {
    if (event.target === sheet) sheet.close();
  });
  $("#expense-form").addEventListener("submit", addExpense);
  $("#sell-form").addEventListener("submit", sellCar);
}

async function start() {
  bind();
  renderSource();
  setView("lot");
  await checkConnection();
  await refreshAll();
}

start();
