"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Search } from "lucide-react";

interface SearchResult {
  medicines: any[];
  sales: any[];
  customers: any[];
}

export default function GlobalSearch() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  // Raccourci Ctrl+K / Cmd+K
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setOpen(true);
        setTimeout(() => inputRef.current?.focus(), 50);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  // Fermer si clic en dehors de la modale
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (overlayRef.current && !overlayRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  // Recherche à la frappe (debounce simple)
  useEffect(() => {
    if (!query.trim()) {
      setResults(null);
      return;
    }
    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const data = await api.globalSearch(query);
        setResults(data);
      } catch (error) {
        console.error("Erreur recherche globale", error);
        setResults(null);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/50 backdrop-blur-sm">
      <div
        ref={overlayRef}
        className="w-full max-w-2xl bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden"
      >
        {/* Barre de recherche */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-200 dark:border-slate-700">
          <Search className="w-5 h-5 text-slate-400" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Rechercher médicament, vente, client..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent outline-none text-slate-800 dark:text-white placeholder:text-slate-400"
          />
          <kbd className="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded text-xs text-slate-500 dark:text-slate-400">ESC</kbd>
        </div>

        {/* Résultats */}
        <div className="max-h-[60vh] overflow-y-auto p-2">
          {loading && <p className="text-center py-8 text-slate-500">Chargement...</p>}

          {!loading && results && (
            <div className="space-y-6">
              {/* Médicaments */}
              {results.medicines.length > 0 && (
                <div>
                  <h3 className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-400">Médicaments</h3>
                  {results.medicines.map((med) => (
                    <button
                      key={med.id}
                      onClick={() => {
                        router.push(`/medicines/${med.id}`);
                        setOpen(false);
                      }}
                      className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 text-left"
                    >
                      <div>
                        <p className="text-sm font-medium text-slate-800 dark:text-white">{med.commercial_name}</p>
                        <p className="text-xs text-slate-500">{med.dci} • {med.category_name}</p>
                      </div>
                      <span className="text-sm font-semibold text-[#0ABAB5]">{med.selling_price.toLocaleString()} FCFA</span>
                    </button>
                  ))}
                </div>
              )}

              {/* Ventes */}
              {results.sales.length > 0 && (
                <div>
                  <h3 className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-400">Ventes</h3>
                  {results.sales.map((sale) => (
                    <button
                      key={sale.id}
                      onClick={() => {
                        router.push(`/sales/${sale.id}`);
                        setOpen(false);
                      }}
                      className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 text-left"
                    >
                      <div>
                        <p className="text-sm font-medium text-slate-800 dark:text-white">Vente #{sale.id} • {sale.customer_name}</p>
                        <p className="text-xs text-slate-500">{sale.created_at} • {sale.payment_method}</p>
                      </div>
                      <span className="text-sm font-semibold text-[#0ABAB5]">{sale.total_amount.toLocaleString()} FCFA</span>
                    </button>
                  ))}
                </div>
              )}

              {/* Clients */}
              {results.customers.length > 0 && (
                <div>
                  <h3 className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-400">Clients</h3>
                  {results.customers.map((customer, idx) => (
                    <div
                      key={idx}
                      className="px-3 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg"
                    >
                      {customer.name}
                    </div>
                  ))}
                </div>
              )}

              {/* Aucun résultat */}
              {results.medicines.length === 0 && results.sales.length === 0 && results.customers.length === 0 && (
                <p className="text-center py-8 text-slate-500">Aucun résultat pour « {query} »</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}