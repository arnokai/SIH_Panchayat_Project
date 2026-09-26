import { useState, useEffect } from "react";
import { fetchInsuranceCertificate } from "../services/api";

export default function InsuranceCertificateModal({ isOpen, onClose, panchayatId, crop = "paddy" }) {
  const [certData, setCertData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!isOpen || !panchayatId) return;

    setLoading(true);
    setError(false);

    fetchInsuranceCertificate(panchayatId, crop)
      .then((data) => {
        setCertData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.warn("Could not generate insurance certificate:", err);
        setError(true);
        setLoading(false);
      });
  }, [isOpen, panchayatId, crop]);

  if (!isOpen) return null;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="cert-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Action Header */}
        <div className="cert-action-bar no-print">
          <div className="cert-bar-title">
            <span className="cert-bar-icon">🛡️</span>
            <div>
              <h3>PMFBY Parametric Weather Loss Certificate</h3>
              <p>Government of India • Ministry of Agriculture & Farmers Welfare • MoES Weather-Index Verification</p>
            </div>
          </div>
          <div className="cert-bar-actions">
            <button className="cert-print-btn" onClick={handlePrint}>
              🖨️ Print Loss Certificate
            </button>
            <button className="cert-close-btn" onClick={onClose}>
              ✕ Close
            </button>
          </div>
        </div>

        {loading ? (
          <div className="cert-modal-loading">
            <span className="trust-spinner"></span>
            <span>Evaluating parametric weather triggers against PMFBY thresholds...</span>
          </div>
        ) : error || !certData ? (
          <div className="cert-error-box">
            <p>Unable to retrieve insurance claim verification for this Gram Panchayat.</p>
          </div>
        ) : (
          <div className="cert-certificate-paper printable-content">
            {/* Certificate Header */}
            <div className="cert-paper-header">
              <div className="cert-crest">🇮🇳</div>
              <h2>PRADHAN MANTRI FASAL BIMA YOJANA (PMFBY)</h2>
              <h4>WEATHER-BASED CROP INSURANCE SCHEME (WBCIS) • PARAMETRIC LOSS CERTIFICATE</h4>
              <span className="cert-subheading">Panchayat-Level Downscaled Micro-Meteorological Verification Audit</span>
            </div>

            <div className="cert-meta-grid">
              <div className="cert-meta-cell">
                <label>Certificate Reference ID</label>
                <strong>{certData.certificate_id}</strong>
              </div>
              <div className="cert-meta-cell">
                <label>Issuance Timestamp (IST)</label>
                <span>{new Date(certData.issued_at).toLocaleString("en-IN")}</span>
              </div>
              <div className="cert-meta-cell">
                <label>Gram Panchayat / LGD</label>
                <strong>{certData.panchayat_name} ({certData.panchayat_id})</strong>
              </div>
              <div className="cert-meta-cell">
                <label>Block & District</label>
                <span>{certData.block_name || "N/A"}, {certData.district_name || "West Bengal"}</span>
              </div>
              <div className="cert-meta-cell">
                <label>Agro-Climatic Zone</label>
                <strong>{certData.agro_climatic_zone}</strong>
              </div>
              <div className="cert-meta-cell">
                <label>Crop & Growth Stage</label>
                <span>
                  {certData.crop.toUpperCase()} • {certData.phenology?.current_stage.toUpperCase()} ({certData.phenology?.accumulated_gdd} GDD)
                </span>
              </div>
            </div>

            {/* Claim Payout Status Banner */}
            <div className={`cert-status-banner ${certData.claim_eligible ? "eligible" : "ineligible"}`}>
              <div className="cert-status-icon">
                {certData.claim_eligible ? "⚠️" : "✓"}
              </div>
              <div>
                <h4>
                  {certData.claim_eligible
                    ? "PARAMETRIC LOSS TRIGGER BREACHED — CLAIM ELIGIBLE"
                    : "NO PARAMETRIC BREACH — NORMAL AGRICULTURAL OPERATION"}
                </h4>
                <p>{certData.payout_recommendation}</p>
              </div>
            </div>

            {/* Triggers Breakdown Table */}
            <div className="cert-triggers-section">
              <h4>EVALUATED WEATHER-INDEX PARAMETERS</h4>
              <table className="cert-triggers-table">
                <thead>
                  <tr>
                    <th>Trigger Parameter</th>
                    <th>Policy Breach Threshold</th>
                    <th>Observed Panchayat Value</th>
                    <th>Breach Status</th>
                    <th>Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {certData.triggers_evaluated.map((t, idx) => (
                    <tr key={idx} className={t.triggered ? "row-triggered" : ""}>
                      <td><strong>{t.trigger_type}</strong></td>
                      <td>{t.threshold}</td>
                      <td><strong>{t.observed_value}</strong></td>
                      <td>
                        <span className={`trigger-pill ${t.triggered ? "breached" : "pass"}`}>
                          {t.triggered ? "TRIGGERED" : "PASS"}
                        </span>
                      </td>
                      <td>
                        <span className={`severity-tag ${t.risk_severity.toLowerCase()}`}>
                          {t.risk_severity}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Cryptographic SHA-256 Proof */}
            <div className="cert-security-footer">
              <div className="cert-hash-block">
                <label>SHA-256 Cryptographic Verification Checksum</label>
                <code>{certData.verification_hash}</code>
                <span className="hash-footnote">
                  Digitally validated against TerraMind Immutable Downscaled Weather Lake (SIH26074)
                </span>
              </div>
              <div className="cert-stamp-block">
                <div className="cert-seal">
                  <span>TERRAMIND</span>
                  <span>VERIFIED</span>
                  <span>WBCIS</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
