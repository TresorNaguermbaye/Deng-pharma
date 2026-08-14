"use client";
import { createContext, useContext, useState, useCallback } from "react";

interface DashboardContextType {
  refreshKey: number;
  triggerRefresh: () => void;
}

const DashboardContext = createContext<DashboardContextType>({
  refreshKey: 0,
  triggerRefresh: () => {},
});

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [refreshKey, setRefreshKey] = useState(0);
  const triggerRefresh = useCallback(() => setRefreshKey(prev => prev + 1), []);

  return (
    <DashboardContext.Provider value={{ refreshKey, triggerRefresh }}>
      {children}
    </DashboardContext.Provider>
  );
}

export const useDashboard = () => useContext(DashboardContext);
