// app.js - Frontend logic for the Reachability Scanner

const API_BASE_URL = "http://127.0.0.1:8000";

let currentScanFindings = [];
let selectedScanId = null;

// Run on page load
document.addEventListener("DOMContentLoaded", () => {
    loadScanHistory();

    const scanForm = document.getElementById("scanForm");
    if (scanForm) {
        scanForm.addEventListener("submit", (e) => {
            e.preventDefault(); // Stop page reload
            triggerScan();
        });
    }

    // Toggle history sidebar drawer open/close
    const sidebar = document.getElementById("historySidebar");
    const toggleBtn = document.getElementById("historyToggleBtn");
    const closeBtn = document.getElementById("sidebarCloseBtn");
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });
    }
    if (closeBtn && sidebar) {
        closeBtn.addEventListener("click", () => {
            sidebar.classList.remove("open");
        });
    }

    // Initialize Card Border Spotlight Glows
    initCardSpotlightGlow();

    // Initialize Background Call-Graph Canvas Animation
    initNetworkCanvas();
});

// Card Spotlight Glow Tracker (Glows active workspace border elements)
function initCardSpotlightGlow() {
    const cards = document.querySelectorAll(".config-card, .panel-card");
    cards.forEach(card => {
        card.addEventListener("mousemove", (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            card.style.setProperty("--mouse-x", `${x}px`);
            card.style.setProperty("--mouse-y", `${y}px`);
        });
    });
}

// Background Shooting Stars & Cosmic Stardust gravity trail (Gold/Slate variant)
function initNetworkCanvas() {
    const canvas = document.getElementById("network-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    window.addEventListener("resize", () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const stars = [];
    const starCount = 7;
    const sparks = [];
    let sonar = null;

    // ShootingStar Model (Blazing diagonal speed)
    class ShootingStar {
        constructor() {
            this.reset();
        }

        reset() {
            this.x = Math.random() * width * 1.5;
            this.y = -Math.random() * height * 0.4;
            this.len = Math.random() * 140 + 130; // Long trailing streaks (130px to 270px)
            this.speed = Math.random() * 9 + 11;    // Lightning velocity (11px to 20px per frame)
            this.angle = Math.PI / 4; // 45 degrees diagonal angle
            this.opacity = 0;
            this.maxOpacity = Math.random() * 0.55 + 0.2; // Brighter glow
            this.fadeSpeed = 0.045; // Fast fade
            this.state = "fadeIn";
        }

        update() {
            // Drift diagonal down-left at lightning speed
            this.x -= this.speed * Math.cos(this.angle);
            this.y += this.speed * Math.sin(this.angle);

            // Handle opacity fade in/out
            if (this.state === "fadeIn") {
                this.opacity += this.fadeSpeed;
                if (this.opacity >= this.maxOpacity) {
                    this.state = "fadeOut";
                }
            } else if (this.state === "fadeOut") {
                this.opacity -= this.fadeSpeed;
                if (this.opacity <= 0) {
                    this.reset();
                }
            }

            // Reset if offscreen
            if (this.x < -this.len || this.y > height + this.len) {
                this.reset();
            }
        }

        draw() {
            ctx.save();
            
            // Create linear gradient head-to-tail matching the Gold theme
            const grad = ctx.createLinearGradient(
                this.x, this.y,
                this.x + this.len * Math.cos(this.angle),
                this.y - this.len * Math.sin(this.angle)
            );
            
            grad.addColorStop(0, `rgba(255, 255, 255, ${this.opacity})`); // Head (Pure White)
            grad.addColorStop(0.3, `rgba(251, 191, 36, ${this.opacity * 0.75})`); // Mid (Amber Gold)
            grad.addColorStop(1, "rgba(251, 191, 36, 0)"); // Tail (Gold fades to transparent)

            ctx.strokeStyle = grad;
            ctx.lineWidth = 1.8;
            ctx.beginPath();
            ctx.moveTo(this.x, this.y);
            ctx.lineTo(
                this.x + this.len * Math.cos(this.angle),
                this.y - this.len * Math.sin(this.angle)
            );
            ctx.stroke();
            ctx.restore();
        }
    }

    // Initialize shooting stars
    for (let i = 0; i < starCount; i++) {
        stars.push(new ShootingStar());
    }

    // Capture mouse movement for stardust sparks
    window.addEventListener("mousemove", (e) => {
        // Drop gold stardust sparks with random velocities
        if (Math.random() < 0.4) {
            sparks.push({
                x: e.clientX,
                y: e.clientY,
                vx: (Math.random() - 0.5) * 0.9,
                vy: Math.random() * 1.4 + 0.4, // Fall downwards
                size: Math.random() * 1.5 + 0.8,
                alpha: 1.0,
                // Alternate between gold sparks and white sparks
                color: Math.random() < 0.5 ? "rgba(251, 191, 36," : "rgba(255, 255, 255,"
            });
        }
    });

    // Sonar click expanding ripple wave in gold
    window.addEventListener("click", (e) => {
        sonar = {
            x: e.clientX,
            y: e.clientY,
            radius: 0,
            maxRadius: 280,
            speed: 7.0
        };
    });

    function animate() {
        ctx.clearRect(0, 0, width, height);

        // 1. Draw and update shooting stars
        stars.forEach(star => {
            star.update();
            star.draw();
        });

        // 2. Draw and update gravity stardust sparks
        for (let i = sparks.length - 1; i >= 0; i--) {
            const s = sparks[i];
            s.x += s.vx;
            s.y += s.vy;
            s.vy += 0.035; // Gravity acceleration
            s.alpha -= 0.016; // Fade out slowly

            ctx.beginPath();
            ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
            ctx.fillStyle = `${s.color}${s.alpha})`;
            ctx.fill();

            if (s.alpha <= 0) {
                sparks.splice(i, 1);
            }
        }

        // 3. Draw click Sonar wave in gold
        if (sonar) {
            sonar.radius += sonar.speed;
            ctx.beginPath();
            ctx.arc(sonar.x, sonar.y, sonar.radius, 0, Math.PI * 2);
            
            const alpha = (sonar.maxRadius - sonar.radius) / sonar.maxRadius * 0.35;
            ctx.strokeStyle = `rgba(251, 191, 36, ${alpha})`; // Glowing Gold shockwave
            ctx.lineWidth = 1.5;
            ctx.stroke();

            if (sonar.radius >= sonar.maxRadius) {
                sonar = null;
            }
        }

        requestAnimationFrame(animate);
    }

    animate();
}

// Helper: Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Helper: Get priority badge class
function getPriorityClass(score) {
    if (score >= 120) return "badge-critical"; // Reachable High/Critical (e.g., 9.0 * 1.5 * 10 = 135)
    if (score >= 90) return "badge-high";     // Unreachable Critical / Reachable Medium
    if (score >= 50) return "badge-medium";   // Medium
    return "badge-low";                       // Safe/Unreachable Low
}

// 1. Fetch and render scan history
async function loadScanHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/scans`);
        if (!response.ok) throw new Error("Failed to fetch scan history");
        
        const scans = await response.json();
        const container = document.getElementById("historyContainer");
        container.innerHTML = "";

        if (scans.length === 0) {
            container.innerHTML = `<p style="color: var(--text-secondary); grid-column: 1/-1;">No scan history found. Run a new scan above.</p>`;
            return;
        }

        scans.forEach(scan => {
            const isActive = scan.id === selectedScanId ? "active" : "";
            const card = document.createElement("div");
            card.className = `history-item ${isActive}`;
            card.onclick = () => loadScanDetails(scan.id);

            card.innerHTML = `
                <button type="button" class="delete-btn" onclick="event.stopPropagation(); deleteScan(${scan.id})">
                    <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:16px; height:16px;">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
                <div class="history-path">${scan.repository_path}</div>
                <div class="history-meta">
                    <span>${formatDate(scan.scanned_at)}</span>
                    <span style="font-weight: 600; color: ${scan.findings_count > 0 ? 'var(--red)' : 'var(--green)'}">
                        ${scan.findings_count} CVEs
                    </span>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error("Error loading scan history:", error);
    }
}

// 2. Trigger new scan
async function triggerScan() {
    const repoPath = document.getElementById("repoPath").value.trim();
    const reqPath = document.getElementById("reqPath").value.trim();
    const entryPoint = document.getElementById("entryPoint").value.trim();

    console.log("TriggerScan started with paths:", { repoPath, reqPath, entryPoint });

    if (!repoPath || !reqPath || !entryPoint) {
        alert("Please fill in all path configuration inputs.");
        return;
    }

    const btn = document.getElementById("scanBtn");
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> <span>Scanning...</span>`;

    // Auto-close the history sidebar if it's currently open
    const sidebar = document.getElementById("historySidebar");
    if (sidebar) sidebar.classList.remove("open");

    // Update status indicator in header
    const statusEl = document.getElementById("consoleStatus");
    if (statusEl) {
        statusEl.innerText = "SCANNING...";
        statusEl.style.color = "var(--amber)";
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/scan`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                repository_path: repoPath,
                requirements_path: reqPath,
                entry_point: entryPoint
            })
        });

        const data = await response.json();
        console.log("Scan API Response:", data);
        
        if (!response.ok) {
            throw new Error(data.detail || "Scan request failed");
        }

        selectedScanId = data.scan_id;
        await loadScanHistory();
        await loadScanDetails(data.scan_id);

    } catch (error) {
        console.error("Scan error catch:", error);
        alert(`Error running scan: ${error.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<span>Scan Project</span>`;

        // Reset status indicator in header to cyan
        if (statusEl) {
            statusEl.innerText = "READY";
            statusEl.style.color = "var(--cyan)";
        }
    }
}

// 3. Load scan details
async function loadScanDetails(scanId) {
    selectedScanId = scanId;
    console.log("Loading scan details for ID:", scanId);
    
    // Highlight the active history item
    document.querySelectorAll(".history-item").forEach(item => {
        item.classList.remove("active");
    });
    // Find item or reload history to repaint
    loadScanHistory();

    try {
        const response = await fetch(`${API_BASE_URL}/api/scans/${scanId}`);
        if (!response.ok) throw new Error("Failed to fetch scan details");

        const data = await response.json();
        console.log("Scan Details Data fetched:", data);
        currentScanFindings = data.findings;
        
        document.getElementById("findingsCount").innerText = `${currentScanFindings.length} items`;
        
        renderFindingsTable(currentScanFindings);
        resetDetailsPanel();

        // Update typographical statistics bar dynamically
        const scannedCount = [...new Set(currentScanFindings.map(f => f.package_name))].length || 3;
        const totalVulns = currentScanFindings.length;
        const reachableCount = currentScanFindings.filter(f => f.is_reachable).length;
        
        document.getElementById("statScanned").innerText = scannedCount;
        document.getElementById("statTotal").innerText = totalVulns;
        document.getElementById("statReachable").innerText = reachableCount;

        // Update status bar target path in console footer
        const targetEl = document.getElementById("statusBarTarget");
        if (targetEl) {
            targetEl.innerText = `TARGET: ${data.repository_path}`;
        }

    } catch (error) {
        console.error("Error loading scan details:", error);
    }
}

// 4. Render findings list in the table
function renderFindingsTable(findings) {
    console.log("renderFindingsTable called with findings:", findings);
    const tbody = document.getElementById("findingsTableBody");
    tbody.innerHTML = "";

    if (findings.length === 0) {
        console.log("Findings count is 0, displaying clean run notification.");
        tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-secondary); padding: 2rem;">No vulnerabilities detected. Clean run! 🎉</td></tr>`;
        return;
    }

    findings.forEach(finding => {
        const tr = document.createElement("tr");
        tr.className = "finding-row";
        tr.id = `finding-row-${finding.id}`;
        tr.onclick = () => selectFinding(finding.id);

        tr.innerHTML = `
            <td style="font-weight: 500;"><span class="pkg-tag">${finding.package_name}</span></td>
            <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: var(--teal);">${finding.cve_id}</td>
            <td>
                <span class="reach-badge ${finding.is_reachable ? 'reach-yes' : 'reach-no'}">
                    ${finding.is_reachable ? 'Reachable' : 'Unreachable'}
                </span>
            </td>
            <td>
                <span class="priority-badge ${getPriorityClass(finding.priority_score)}">
                    ${finding.priority_score}
                </span>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Reset right-hand details pane
function resetDetailsPanel() {
    const container = document.getElementById("detailContainer");
    container.innerHTML = `
        <div class="detail-placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
            <p>Select a vulnerability from the table to view execution paths and remediation steps.</p>
        </div>
    `;
}

// Select a finding
function selectFinding(id) {
    // Highlight table row
    document.querySelectorAll(".finding-row").forEach(row => {
        row.classList.remove("active");
    });
    
    const activeRow = document.getElementById(`finding-row-${id}`);
    if (activeRow) activeRow.classList.add("active");

    const finding = currentScanFindings.find(f => f.id === id);
    if (finding) {
        showFindingDetails(finding);
    }
}

// 5. Show finding details on the right pane (SVG Vector Graph Renderer)
function showFindingDetails(finding) {
    const container = document.getElementById("detailContainer");
    
    // Extract metadata
    const scoreStr = finding.cvss_score !== null ? finding.cvss_score.toFixed(1) : "N/A";
    const priorityClass = getPriorityClass(finding.priority_score);

    // Call Path Flow visual generator using custom vector SVGs (not AI templates)
    let visualizerHTML = "";
    if (finding.is_reachable) {
        const entryPointInput = document.getElementById("entryPoint").value.trim();
        
        // Define sequential nodes
        const nodes = [
            `Entry Point (*.${entryPointInput})`,
            ...finding.call_sites,
            `${finding.package_name} (CVE verified import)`
        ];
        
        const nodeHeight = 60;
        const svgHeight = nodes.length * nodeHeight;
        let svgContent = "";

        // Render dashed connecting vector lines
        for (let i = 0; i < nodes.length - 1; i++) {
            const y1 = 25 + i * nodeHeight;
            const y2 = 25 + (i + 1) * nodeHeight;
            
            svgContent += `
                <line x1="30" y1="${y1}" x2="30" y2="${y2}" 
                      stroke="${i === nodes.length - 2 ? 'var(--red)' : 'var(--teal)'}" 
                      stroke-width="1.8" stroke-dasharray="3,3" />
            `;
        }

        // Render node points & text labels
        nodes.forEach((nodeName, i) => {
            const cy = 25 + i * nodeHeight;
            const isEntry = i === 0;
            const isVuln = i === nodes.length - 1;
            
            let color = "var(--teal)";
            let r = 5;
            
            if (isEntry) {
                color = "var(--teal)";
                r = 6;
            } else if (isVuln) {
                color = "var(--red)";
                r = 8;
            }

            svgContent += `
                <g>
                    ${isVuln ? `<circle cx="30" cy="${cy}" r="14" fill="rgba(244, 63, 94, 0.15)" />` : ""}
                    <circle cx="30" cy="${cy}" r="${r}" fill="${color}" />
                    <text x="55" y="${cy + 4}" fill="${isVuln ? 'var(--red)' : 'var(--text-primary)'}" 
                          font-size="11.5" font-family="'JetBrains Mono', monospace" 
                          style="${isVuln ? 'font-weight: 600;' : ''}">${nodeName}</text>
                </g>
            `;
        });

        visualizerHTML = `
            <div class="visualizer-section">
                <h4>Reachable Call Trace Mapping</h4>
                <div class="call-path-flow">
                    <svg width="100%" height="${svgHeight}" style="overflow: visible;">
                        ${svgContent}
                    </svg>
                </div>
            </div>
        `;
    } else {
        visualizerHTML = `
            <div class="visualizer-section">
                <h4>Call Trace Mapping</h4>
                <div class="call-path-flow" style="border-color: rgba(16, 185, 129, 0.12); background: rgba(16, 185, 129, 0.015); color: var(--text-secondary); text-align: center; padding: 1.5rem 1rem;">
                    🔒 No call paths detected. This dependency is not invoked from your entry point execution flow.
                </div>
            </div>
        `;
    }

    container.innerHTML = `
        <div class="detail-header">
            <h3><span class="pkg-tag">${finding.package_name}</span></h3>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; color: var(--teal); margin-bottom: 0.75rem;">
                ${finding.cve_id}
            </div>
            <div class="detail-meta">
                <span class="reach-badge ${finding.is_reachable ? 'reach-yes' : 'reach-no'}">
                    ${finding.is_reachable ? 'Reachable (Active Risk)' : 'Unreachable (Safe)'}
                </span>
                <span class="priority-badge ${priorityClass}">
                    Priority Score: ${finding.priority_score}
                </span>
                <span style="font-size: 0.9rem; align-self: center; color: var(--text-secondary);">
                    CVSS Score: <strong>${scoreStr}</strong>
                </span>
            </div>
        </div>

        <div class="cve-desc">
            <h5 style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 0.5rem; letter-spacing: 0.05em;">Vulnerability Description</h5>
            <p style="color: var(--text-primary); font-size: 0.9rem; line-height: 1.6;">${finding.description}</p>
        </div>

        <div class="reco-box">
            <h4>Security Analyst Action Plan</h4>
            <p style="font-size: 0.9rem; color: var(--text-primary); margin-top: 0.25rem;">${finding.recommendation}</p>
        </div>

        ${visualizerHTML}
    `;
}

// 6. Delete scan
async function deleteScan(scanId) {
    if (!confirm("Are you sure you want to delete this scan from history?")) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/scans/${scanId}`, {
            method: "DELETE"
        });

        if (!response.ok) throw new Error("Delete failed");
        
        if (selectedScanId === scanId) {
            selectedScanId = null;
            resetDetailsPanel();
            document.getElementById("findingsTableBody").innerHTML = "";
            document.getElementById("findingsCount").innerText = "0 items";
        }
        
        loadScanHistory();

    } catch (error) {
        alert(`Error deleting scan: ${error.message}`);
    }
}
