/**
 * Global Request Manager
 * Prevents duplicate API calls and manages request lifecycle
 */

interface PendingRequest {
  promise: Promise<any>;
  timestamp: number;
  abortController: AbortController;
}

class RequestManager {
  private pendingRequests = new Map<string, PendingRequest>();
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();
  
  /**
   * Execute a request with deduplication and caching
   */
  async executeRequest<T>(
    key: string,
    requestFn: (signal: AbortSignal) => Promise<T>,
    options: {
      cacheTTL?: number; // Cache time-to-live in ms
      forceRefresh?: boolean;
    } = {}
  ): Promise<T> {
    const { cacheTTL = 30000, forceRefresh = false } = options; // 30s default cache
    
    // Check cache first (unless force refresh)
    if (!forceRefresh) {
      const cached = this.cache.get(key);
      if (cached && Date.now() - cached.timestamp < cached.ttl) {
        console.log(`📦 Using cached data for: ${key}`);
        return cached.data;
      }
    }
    
    // Check if request is already pending
    const pending = this.pendingRequests.get(key);
    if (pending && !forceRefresh) {
      console.log(`⏳ Joining existing request for: ${key}`);
      try {
        return await pending.promise;
      } catch (error) {
        // If the pending request fails, remove it and continue
        this.pendingRequests.delete(key);
        throw error;
      }
    }
    
    // Cancel existing request if force refresh
    if (pending && forceRefresh) {
      console.log(`🚫 Canceling existing request for: ${key}`);
      pending.abortController.abort();
      this.pendingRequests.delete(key);
    }
    
    // Create new request
    const abortController = new AbortController();
    const promise = this.createRequest(key, requestFn, abortController.signal, cacheTTL);
    
    this.pendingRequests.set(key, {
      promise,
      timestamp: Date.now(),
      abortController
    });
    
    try {
      const result = await promise;
      return result;
    } finally {
      // Clean up pending request
      this.pendingRequests.delete(key);
    }
  }
  
  private async createRequest<T>(
    key: string,
    requestFn: (signal: AbortSignal) => Promise<T>,
    signal: AbortSignal,
    cacheTTL: number
  ): Promise<T> {
    console.log(`🚀 Starting new request for: ${key}`);
    
    try {
      const result = await requestFn(signal);
      
      // Cache the result
      this.cache.set(key, {
        data: result,
        timestamp: Date.now(),
        ttl: cacheTTL
      });
      
      console.log(`✅ Request completed for: ${key}`);
      return result;
      
    } catch (error: any) {
      // Don't cache errors, but handle abort gracefully
      if (error.name === 'AbortError' || error.name === 'CanceledError' || error.code === 'ERR_CANCELED') {
        console.log(`🚫 Request aborted for: ${key}`);
      } else {
        console.error(`❌ Request failed for: ${key}`, error);
      }
      throw error;
    }
  }
  
  /**
   * Clear cache for a specific key or all keys
   */
  clearCache(key?: string): void {
    if (key) {
      this.cache.delete(key);
      console.log(`🧹 Cleared cache for: ${key}`);
    } else {
      this.cache.clear();
      console.log(`🧹 Cleared all cache`);
    }
  }
  
  /**
   * Cancel all pending requests
   */
  cancelAllRequests(): void {
    console.log(`🚫 Canceling ${this.pendingRequests.size} pending requests`);
    
    for (const [key, request] of this.pendingRequests.entries()) {
      request.abortController.abort();
    }
    
    this.pendingRequests.clear();
  }
  
  /**
   * Get cache statistics
   */
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    };
  }
  
  /**
   * Get pending requests statistics
   */
  getPendingStats(): { count: number; keys: string[] } {
    return {
      count: this.pendingRequests.size,
      keys: Array.from(this.pendingRequests.keys())
    };
  }
}

// Export singleton instance
export const requestManager = new RequestManager();
export default requestManager;
