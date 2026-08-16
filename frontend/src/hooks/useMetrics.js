import { useState, useEffect } from 'react';

function useMetrics() {
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const apiHost = window.location.port === '3000' ? 'http://localhost:8000' : '';
        const response = await fetch(`${apiHost}/api/v1/metrics/summary`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        setData(result);
        setLoading(false);
      } catch (err) {
        setError(err);
        setLoading(false);
        console.error('Fetch error:', err);
      }
    };

    fetchMetrics();

    const interval = setInterval(fetchMetrics, 15000);

    return () => clearInterval(interval);
  }, []);

  return { data, loading, error };
}

export default useMetrics;
