/**
 * Global Data Provider
 * Simplified version to prevent infinite loops
 */

'use client';

import React, { createContext, useContext, useEffect, ReactNode } from 'react';
import { useGlobalDataStore } from '../store/globalDataStore';

interface GlobalDataContextType {
  initialized: boolean;
  refreshAllData: () => Promise<void>;
}

const GlobalDataContext = createContext<GlobalDataContextType | undefined>(undefined);

interface GlobalDataProviderProps {
  children: ReactNode;
}

export function GlobalDataProvider({ children }: GlobalDataProviderProps) {
  const [initialized, setInitialized] = React.useState(false);
  
  // Get the fetchAllData function once
  const fetchAllData = useGlobalDataStore.getState().fetchAllData;

  // Initialize data on mount - ONLY ONCE
  useEffect(() => {
    let mounted = true;
    
    const initializeData = async () => {
      try {
        console.log('🚀 Initializing global data...');
        await fetchAllData();
        if (mounted) {
          setInitialized(true);
          console.log('✅ Global data initialized');
        }
      } catch (error) {
        console.error('❌ Failed to initialize global data:', error);
        if (mounted) {
          setInitialized(true); // Still mark as initialized to prevent infinite loading
        }
      }
    };

    initializeData();
    
    return () => {
      mounted = false;
    };
  }, []); // CRITICAL: Empty dependency array - only run once on mount

  const refreshAllData = async () => {
    const { fetchAllData } = useGlobalDataStore.getState();
    await fetchAllData(true); // Force refresh
  };

  const value = React.useMemo(() => ({
    initialized,
    refreshAllData,
  }), [initialized]);

  return (
    <GlobalDataContext.Provider value={value}>
      {children}
    </GlobalDataContext.Provider>
  );
}

export function useGlobalData() {
  const context = useContext(GlobalDataContext);
  if (context === undefined) {
    throw new Error('useGlobalData must be used within a GlobalDataProvider');
  }
  return context;
}