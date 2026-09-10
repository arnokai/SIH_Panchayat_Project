import { useEffect, useState } from "react";
import { fetchStatewideStats } from "../services/api";

export default function SystemStatsFooter() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    let mounted = true;
    async function loadStats() {
      try {
        const res = await fetchStatewideStats();
        if (mounted) setStats(res);
      } catch (e) {
        console.warn("Could not load statewide stats:", e);
      }
    }
    loadStats();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <footer className="system-footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <h4>TerraMind Weather Intelligence</h4>
          <p>Statewide Panchayat-Level Downscaling System for West Bengal</p>
        </div>

        <div className="footer-stats-grid">
          <div className="footer-stat-item">
            <span className="footer-stat-num">
              {stats?.total_panchayats ? stats.total_panchayats.toLocaleString() : "3,339"}
            </span>
            <span className="footer-stat-label">Gram Panchayats</span>
          </div>

          <div className="footer-stat-item">
            <span className="footer-stat-num">
              {stats?.total_districts ?? 22}
            </span>
            <span className="footer-stat-label">Districts Covered</span>
          </div>

          <div className="footer-stat-item">
            <span className="footer-stat-num">
              {stats?.total_blocks ?? 342}
            </span>
            <span className="footer-stat-label">Blocks Modeled</span>
          </div>

          <div className="footer-stat-item">
            <span className="footer-stat-num">
              {stats?.total_rows ? `${(stats.total_rows / 1000000).toFixed(2)}M` : "2.44M"}
            </span>
            <span className="footer-stat-label">Parquet Records</span>
          </div>

          <div className="footer-stat-item">
            <span className="footer-stat-status-badge">
              {stats?.qa_status === "PASS" ? "QA VERIFIED" : "ONLINE"}
            </span>
            <span className="footer-stat-label">Data Lake Status</span>
          </div>
        </div>
      </div>
      <div className="footer-bottom-bar">
        <span>© 2026 TerraMind • SIH Agritech Initiative • Strictly English Advisory System</span>
      </div>
    </footer>
  );
}
