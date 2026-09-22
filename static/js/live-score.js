/**
 * CrickScore Live - Real-time Live Score Updates
 * Connects via Django Channels WebSocket with smooth fallback to AJAX polling
 */

class LiveScoreManager {
    constructor(matchId, matchSlug) {
        this.matchId = matchId;
        this.matchSlug = matchSlug;
        this.socket = null;
        this.pollingInterval = null;
        this.init();
    }

    init() {
        this.connectWebSocket();
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/matches/${this.matchId}/`;

        try {
            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                console.log('✓ Connected to live match WebSocket');
                this.stopPolling();
            };

            this.socket.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleLiveMessage(message);
            };

            this.socket.onclose = () => {
                console.warn('WebSocket closed. Falling back to HTTP polling.');
                this.startPolling();
            };

            this.socket.onerror = () => {
                console.warn('WebSocket error. Falling back to HTTP polling.');
                this.startPolling();
            };
        } catch (e) {
            console.error('WebSocket initialization error:', e);
            this.startPolling();
        }
    }

    startPolling() {
        if (this.pollingInterval) return;
        console.log('Starting live score AJAX polling (every 10s)...');
        this.pollingInterval = setInterval(() => this.pollLiveScore(), 10000);
    }

    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    async pollLiveScore() {
        try {
            const res = await fetch(`/matches/${this.matchSlug}/live-json/`);
            if (!res.ok) return;
            const data = await res.json();
            this.updateDomScore(data);
        } catch (err) {
            console.error('Polling error:', err);
        }
    }

    handleLiveMessage(msg) {
        if (msg.type === 'score_update' || msg.type === 'initial_snapshot') {
            this.updateDomScore(msg.data);
        } else if (msg.type === 'new_ball') {
            this.prependBallCommentary(msg.data);
        }
    }

    updateDomScore(data) {
        const inn = data.current_innings || data;
        if (!inn) return;

        // Update score badges and overs on live page
        const scoreEl = document.getElementById('liveScoreDisplay');
        if (scoreEl && inn.runs !== undefined) {
            scoreEl.textContent = `${inn.runs}/${inn.wickets}`;
        }

        const oversEl = document.getElementById('liveOversDisplay');
        if (oversEl && inn.overs) {
            oversEl.textContent = `(${inn.overs} ov)`;
        }

        const crrEl = document.getElementById('liveCRRDisplay');
        if (crrEl && inn.crr) {
            crrEl.textContent = `CRR: ${inn.crr}`;
        }
    }

    prependBallCommentary(ball) {
        const container = document.getElementById('liveCommentaryStream');
        if (!container) return;

        const ballHtml = `
            <div class="commentary-item p-3 border-bottom animate__animated animate__fadeIn">
                <div class="d-flex align-items-center gap-3">
                    <span class="badge ${ball.is_wicket ? 'bg-danger' : (ball.is_boundary ? 'bg-primary' : 'bg-secondary')} fs-6">
                        ${ball.over}.${ball.ball}
                    </span>
                    <div>
                        <div class="fw-bold">${ball.runs_text || (ball.runs + ' runs')}</div>
                        <p class="text-muted mb-0 small">${ball.commentary}</p>
                    </div>
                </div>
            </div>
        `;

        container.insertAdjacentHTML('afterbegin', ballHtml);
    }
}

window.LiveScoreManager = LiveScoreManager;
