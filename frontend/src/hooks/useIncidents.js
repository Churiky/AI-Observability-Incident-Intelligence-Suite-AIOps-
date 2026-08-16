import { useState, useEffect } from 'react';

function useIncidents() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        setLoading(true);
        const apiHost = window.location.port === '3000' ? 'http://localhost:8000' : '';
        const response = await fetch(`${apiHost}/api/v1/incidents`);
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

    fetchIncidents();

    // Set up interval to refresh data
    const interval = setInterval(fetchIncidents, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  return { data, setData, loading, error };
}

export default useIncidents;