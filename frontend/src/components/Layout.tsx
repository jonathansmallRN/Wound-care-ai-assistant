import { NavLink, Outlet } from "react-router-dom";

const NAV_LINKS = [
  { to: "/", label: "Cases", end: true },
  { to: "/validation", label: "Validation Dashboard" },
];

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 bg-white border-r border-slate-200 flex flex-col">
        <div className="px-5 py-4 border-b border-slate-200">
          <span className="text-sm font-semibold text-slate-800 leading-tight">
            Wound Care AI<br />
            <span className="text-xs font-normal text-slate-500">
              Clinical Decision Support
            </span>
          </span>
        </div>
        <nav className="flex-1 py-3 px-2 space-y-0.5">
          {NAV_LINKS.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-blue-50 text-blue-700"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-3 border-t border-slate-200">
          <p className="text-xs text-slate-400">
            For clinical review only.<br />
            Not a diagnostic tool.
          </p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
