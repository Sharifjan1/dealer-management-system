/*
  api.js

  One place for all data access. The rest of the app calls these
  functions and doesn't care where the data comes from.

  Two modes:
  - "api": talks to the FastAPI backend (backend/app/main.py)
  - "demo": keeps sample data in this browser's localStorage so the
    site works on GitHub Pages without a backend running
*/

const SETTINGS_KEY = "dms-settings";
const DEMO_KEY = "dms-demo-data-v1";
const DEFAULT_API_URL = "http://127.0.0.1:8000";
const NHTSA_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/";

function safeGet(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeSet(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Storage blocked (private window). The app still works for this visit.
  }
}

/* ---------- Settings ---------- */

function defaultMode() {
  const host = window.location.hostname;
  const isLocal = host === "localhost" || host === "127.0.0.1" || host === "";
  return isLocal ? "api" : "demo";
}

export function loadSettings() {
  const fallback = { mode: defaultMode(), apiUrl: DEFAULT_API_URL };
  const raw = safeGet(SETTINGS_KEY);
  if (!raw) return fallback;
  try {
    return { ...fallback, ...JSON.parse(raw) };
  } catch {
    return fallback;
  }
}

export function saveSettings(settings) {
  safeSet(SETTINGS_KEY, JSON.stringify(settings));
}

let settings = loadSettings();

export function getSettings() {
  return settings;
}

export function setSettings(next) {
  settings = { ...settings, ...next };
  settings.apiUrl = settings.apiUrl.replace(/\/+$/, "");
  saveSettings(settings);
}

/* ---------- VIN checks (same rules as vin_service.py) ---------- */

export function checkVin(vin) {
  const clean = (vin || "").trim().toUpperCase();
  if (clean.length !== 17) {
    return { ok: false, vin: clean, message: `A VIN has 17 characters. This one has ${clean.length}.` };
  }
  if (/[IOQ]/.test(clean)) {
    return { ok: false, vin: clean, message: "VINs never use the letters I, O or Q. Check for a 1 or 0." };
  }
  return { ok: true, vin: clean };
}

/* ---------- Money math (same as calculations.py) ---------- */

export function calcFinancials(vehicle, expenses) {
  const totalExpenses = expenses.reduce((sum, e) => sum + Number(e.amount), 0);
  const totalInvestment = Number(vehicle.purchase_price || 0) + totalExpenses;
  const projected = Number(vehicle.asking_price || 0) - totalInvestment;
  const sold = vehicle.sale_price !== null && vehicle.sale_price !== undefined;
  const actual = sold ? vehicle.sale_price - totalInvestment : null;
  let roi = null;
  if (sold) roi = totalInvestment === 0 ? 0 : (actual / totalInvestment) * 100;
  return {
    total_expenses: totalExpenses,
    total_investment: totalInvestment,
    projected_profit: projected,
    actual_profit: actual,
    roi,
  };
}

/* ---------- API mode ---------- */

function readableError(body, status) {
  if (body && typeof body.detail === "string") return body.detail;
  if (body && Array.isArray(body.detail)) {
    return body.detail
      .map((d) => {
        const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : "field";
        return `${field}: ${d.msg}`;
      })
      .join(". ");
  }
  return `The server answered with error ${status}.`;
}

async function request(path, options = {}) {
  const url = `${settings.apiUrl}${path}`;
  let response;
  try {
    response = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error(
      `Can't reach the API at ${settings.apiUrl}. Start the backend with "uvicorn app.main:app --reload" or switch to demo data.`
    );
  }
  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (!response.ok) throw new Error(readableError(body, response.status));
  return body;
}

const apiBackend = {
  async ping() {
    return request("/");
  },
  async listVehicles() {
    const vehicles = await request("/vehicles/");
    return Promise.all(vehicles.map((v) => request(`/vehicles/${v.id}`)));
  },
  async getVehicle(id) {
    return request(`/vehicles/${id}`);
  },
  async summary() {
    return request("/vehicles/dashboard/summary");
  },
  async decodeVin(vin) {
    return request(`/vehicles/decode/${encodeURIComponent(vin)}`);
  },
  async createVehicle(data) {
    return request("/vehicles/", { method: "POST", body: JSON.stringify(data) });
  },
  async listExpenses(vehicleId) {
    return request(`/expenses/vehicle/${vehicleId}`);
  },
  async addExpense(vehicleId, expense) {
    return request(`/expenses/vehicle/${vehicleId}`, {
      method: "POST",
      body: JSON.stringify(expense),
    });
  },
  async sellVehicle(vehicleId, salePrice) {
    return request(`/vehicles/${vehicleId}/sell`, {
      method: "PUT",
      body: JSON.stringify({ sale_price: salePrice }),
    });
  },
};

/* ---------- Demo mode ---------- */

function seedData() {
  const day = 24 * 60 * 60 * 1000;
  const now = Date.now();
  const iso = (daysAgo) => new Date(now - daysAgo * day).toISOString();
  const vehicles = [
    {
      id: 1, vin: "2HGFC2F59HH500311", year: "2017", make: "HONDA", model: "Civic", trim: "LX",
      body_type: "Sedan/Saloon", fuel_type: "Gasoline", color: "Silver", mileage: 88410,
      purchase_price: 11200, asking_price: 14995, sale_price: null, status: "inventory", created_at: iso(21),
    },
    {
      id: 2, vin: "1FTEW1EG8JFA10442", year: "2018", make: "FORD", model: "F-150", trim: "XLT",
      body_type: "Pickup", fuel_type: "Gasoline", color: "White", mileage: 102300,
      purchase_price: 19800, asking_price: 25900, sale_price: null, status: "inventory", created_at: iso(9),
    },
    {
      id: 3, vin: "4T1BF1FK5FU900123", year: "2015", make: "TOYOTA", model: "Camry", trim: "SE",
      body_type: "Sedan/Saloon", fuel_type: "Gasoline", color: "Black", mileage: 121050,
      purchase_price: 8900, asking_price: 12495, sale_price: null, status: "inventory", created_at: iso(4),
    },
    {
      id: 4, vin: "1N4AL3AP5EC400871", year: "2014", make: "NISSAN", model: "Altima", trim: "2.5 S",
      body_type: "Sedan/Saloon", fuel_type: "Gasoline", color: "Blue", mileage: 134800,
      purchase_price: 5400, asking_price: 7995, sale_price: 7600, status: "sold", created_at: iso(40),
    },
  ];
  const expenses = [
    { id: 1, vehicle_id: 1, category: "Detail", description: "Full interior and buff", amount: 180 },
    { id: 2, vehicle_id: 1, category: "Tires", description: "Two front tires", amount: 260 },
    { id: 3, vehicle_id: 2, category: "Auction fee", description: "Buyer fee", amount: 395 },
    { id: 4, vehicle_id: 2, category: "Transport", description: "Auction to lot", amount: 150 },
    { id: 5, vehicle_id: 3, category: "Repair", description: "Brake pads and rotors", amount: 420 },
    { id: 6, vehicle_id: 4, category: "Smog", description: "Smog check", amount: 60 },
    { id: 7, vehicle_id: 4, category: "Detail", description: "", amount: 150 },
  ];
  return { vehicles, expenses, nextVehicleId: 5, nextExpenseId: 8 };
}

let demoCache = null;

function demoData() {
  if (demoCache) return demoCache;
  const raw = safeGet(DEMO_KEY);
  if (raw) {
    try {
      demoCache = JSON.parse(raw);
      return demoCache;
    } catch {
      // fall through to a fresh seed
    }
  }
  demoCache = seedData();
  safeSet(DEMO_KEY, JSON.stringify(demoCache));
  return demoCache;
}

function demoSave() {
  safeSet(DEMO_KEY, JSON.stringify(demoCache));
}

export function resetDemoData() {
  demoCache = seedData();
  demoSave();
}

function demoFind(id) {
  const vehicle = demoData().vehicles.find((v) => v.id === Number(id));
  if (!vehicle) throw new Error("Vehicle not found.");
  return vehicle;
}

function demoExpensesFor(id) {
  return demoData().expenses.filter((e) => e.vehicle_id === Number(id));
}

function demoDetail(vehicle) {
  return { vehicle: { ...vehicle }, financials: calcFinancials(vehicle, demoExpensesFor(vehicle.id)) };
}

const demoBackend = {
  async ping() {
    return { status: "demo" };
  },
  async listVehicles() {
    return demoData().vehicles.map(demoDetail);
  },
  async getVehicle(id) {
    return demoDetail(demoFind(id));
  },
  async summary() {
    const all = demoData().vehicles;
    const active = all.filter((v) => v.status !== "sold");
    const sold = all.filter((v) => v.status === "sold");
    const totals = {
      inventory_count: active.length,
      vehicles_sold: sold.length,
      total_invested: 0,
      inventory_value: 0,
      potential_profit: 0,
      total_sales: 0,
      total_actual_profit: 0,
    };
    for (const v of active) {
      const f = calcFinancials(v, demoExpensesFor(v.id));
      totals.total_invested += f.total_investment;
      totals.inventory_value += v.asking_price || 0;
      totals.potential_profit += f.projected_profit;
    }
    for (const v of sold) {
      const f = calcFinancials(v, demoExpensesFor(v.id));
      totals.total_sales += v.sale_price || 0;
      totals.total_actual_profit += f.actual_profit || 0;
    }
    return totals;
  },
  async decodeVin(vin) {
    // In demo mode the browser asks NHTSA directly.
    let data;
    try {
      const response = await fetch(`${NHTSA_URL}${encodeURIComponent(vin)}?format=json`);
      data = await response.json();
    } catch {
      throw new Error("Unable to connect to the VIN decoding service. Fill in the details by hand.");
    }
    const r = data && data.Results && data.Results[0];
    if (!r) throw new Error("No vehicle information was found for this VIN.");
    if (r.ErrorCode && r.ErrorCode !== "0" && !r.Make) {
      throw new Error(r.ErrorText || "VIN could not be decoded.");
    }
    return {
      vin,
      year: r.ModelYear || null,
      make: r.Make || null,
      model: r.Model || null,
      trim: r.Trim || null,
      body_type: r.BodyClass || null,
      fuel_type: r.FuelTypePrimary || null,
    };
  },
  async createVehicle(data) {
    const store = demoData();
    if (store.vehicles.some((v) => v.vin === data.vin)) {
      throw new Error("A vehicle with this VIN already exists.");
    }
    const vehicle = {
      id: store.nextVehicleId++,
      year: null, make: null, model: null, trim: null, body_type: null, fuel_type: null,
      color: null, mileage: null, purchase_price: 0, asking_price: 0,
      ...data,
      sale_price: null,
      status: "inventory",
      created_at: new Date().toISOString(),
    };
    store.vehicles.push(vehicle);
    demoSave();
    return { ...vehicle };
  },
  async listExpenses(vehicleId) {
    demoFind(vehicleId);
    return demoExpensesFor(vehicleId).map((e) => ({ ...e }));
  },
  async addExpense(vehicleId, expense) {
    demoFind(vehicleId);
    if (!(expense.amount > 0)) throw new Error("amount: Input should be greater than 0");
    const store = demoData();
    const row = { id: store.nextExpenseId++, vehicle_id: Number(vehicleId), ...expense };
    store.expenses.push(row);
    demoSave();
    return { ...row };
  },
  async sellVehicle(vehicleId, salePrice) {
    const vehicle = demoFind(vehicleId);
    if (vehicle.status === "sold") throw new Error("This vehicle is already marked as sold.");
    vehicle.sale_price = salePrice;
    vehicle.status = "sold";
    demoSave();
    return { message: "Vehicle marked as sold.", ...demoDetail(vehicle) };
  },
};

/* ---------- Public interface ---------- */

export function backend() {
  return settings.mode === "api" ? apiBackend : demoBackend;
}
