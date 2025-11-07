import { useState, useEffect, useCallback } from 'react';
import { getProject, type ProjectDetail } from '@/services/api';

/**
 * Custom hook for managing project data cache
 *
 * Strategy:
 * - Load first project (data-analysis) on mount
 * - Cache project data after first load
 * - Load new project on demand when user switches (use cache if exists)
 * - Avoid reloading already cached projects
 *
 * Caching Flow:
 * 1. User enters page → Load first project (cache miss) → Store in cache
 * 2. User switches project → Check cache (cache hit) → Use cached data
 * 3. User switches back → Check cache (cache hit) → Use cached data
 * 4. (Future) User edits and saves → Update cache with new data
 * 5. (Future) User executes node → Update cache with execution result
 */
export function useProjectCache() {
  const [projectCache, setProjectCache] = useState<Record<string, ProjectDetail>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Map frontend dataset IDs to backend project IDs
  const projectIdMap: Record<string, string> = {
    'data-analysis': 'test_user_behavior_analysis',
    'risk-model': 'test_sales_performance_report',
  };

  /**
   * Load project data with caching
   * - If already cached, use cached data
   * - If not cached, fetch from backend and cache it
   */
  const loadProject = useCallback(
    async (datasetId: string) => {
      const backendProjectId = projectIdMap[datasetId] || datasetId;

      // Use cached data if available
      if (projectCache[backendProjectId]) {
        console.log(`[Cache HIT] Using cached data for ${backendProjectId}`);
        return projectCache[backendProjectId];
      }

      // Fetch from backend
      console.log(`[Cache MISS] Fetching ${backendProjectId} from backend`);
      try {
        setIsLoading(true);
        setError(null);

        const projectData = await getProject(backendProjectId);

        // Store in cache
        setProjectCache((prev) => ({
          ...prev,
          [backendProjectId]: projectData,
        }));

        return projectData;
      } catch (err) {
        const errorMsg = `Failed to load project ${backendProjectId}`;
        console.error(errorMsg, err);
        setError(errorMsg);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [projectCache]
  );

  /**
   * Load first project on mount
   * This ensures the page shows data immediately when user enters
   */
  useEffect(() => {
    const loadFirstProject = async () => {
      try {
        await loadProject('data-analysis');
      } catch (err) {
        console.error('Failed to load first project:', err);
      }
    };

    loadFirstProject();
  }, [loadProject]);

  /**
   * Update project cache (used after editing or execution)
   * This will be called by other components after saving/executing
   */
  const updateProjectCache = useCallback(
    (backendProjectId: string, updatedProject: ProjectDetail) => {
      setProjectCache((prev) => ({
        ...prev,
        [backendProjectId]: updatedProject,
      }));
    },
    []
  );

  /**
   * Clear cache (optional, rarely used)
   */
  const clearCache = useCallback(() => {
    setProjectCache({});
  }, []);

  return {
    projectCache,
    isLoading,
    error,
    loadProject,
    updateProjectCache,
    clearCache,
    projectIdMap,
  };
}
