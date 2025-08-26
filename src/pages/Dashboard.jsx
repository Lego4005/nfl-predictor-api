import { useEffect, useState } from "react";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "https://nfl-predictor-api.onrender.com";

export default function Dashboard() {
  const [week, setWeek] = useState(1);
  const [data, setData] = useState(null);
  const [lineup, setLineup] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const fetchData = async () => {
      try {
        const [picksRes, lineupRes] = await Promise.all([
          axios.get(`${API_BASE}/v1/best-picks/2025/${week}`),
          axios.get(`${API_BASE}/v1/lineup/2025/${week}`),
        ]);
        setData(picksRes.data);
        setLineup(lineupRes.data);
      } catch (err) {
        console.error("Error fetching data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [week]);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">NFL Predictor - Week {week}</h1>

      <div className="mb-6">
        <label>Week: </label>
        <select value={week} onChange={(e) => setWeek(parseInt(e.target.value))}>
          {[...Array(18)].map((_, i) => (
            <option key={i + 1} value={i + 1}>
              Week {i + 1}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <p>Loading data...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Fantasy Picks */}
          <div>
            <h2 className="text-xl font-semibold mb-2">Top 5 Fantasy Value Picks</h2>
            <table className="table-auto w-full">
              <thead>
                <tr>
                  <th>Player</th>
                  <th>Position</th>
                  <th>Salary</th>
                  <th>Value Score</th>
                </tr>
              </thead>
              <tbody>
                {data?.top5_fantasy?.map((pick, idx) => (
                  <tr key={idx}>
                    <td>{pick.player}</td>
                    <td>{pick.position}</td>
                    <td>${pick.salary}</td>
                    <td>{pick.value_score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* DFS Lineup */}
          <div>
            <h2 className="text-xl font-semibold mb-2">Classic DFS Lineup</h2>
            <p className="mb-2 text-sm text-gray-500">
              Salary Cap: ${lineup?.salary_cap} | Used: ${lineup?.total_salary} | Projected Points: {lineup?.projected_points}
            </p>
            <table className="table-auto w-full">
              <thead>
                <tr>
                  <th>Position</th>
                  <th>Player</th>
                  <th>Team</th>
                  <th>Salary</th>
                  <th>Projected Pts</th>
                </tr>
              </thead>
              <tbody>
                {lineup?.lineup?.map((p, i) => (
                  <tr key={i}>
                    <td>{p.position}</td>
                    <td>{p.player}</td>
                    <td>{p.team}</td>
                    <td>${p.salary}</td>
                    <td>{p.proj_points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
