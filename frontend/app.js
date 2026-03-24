const API_URL = "http://127.0.0.1:8000/movies";
const SESSION_KEY = "movie-diary-session";

const state = {
    genres: [],
    user: null,
    token: null,
    authMode: "login",
    currentMovie: null,
    authGenresExpanded: false,
    settingsGenresExpanded: false,
};

const authView = document.getElementById("authView");
const appView = document.getElementById("appView");
const authForm = document.getElementById("authForm");
const authTitle = document.getElementById("authTitle");
const authSubmitButton = document.getElementById("authSubmitButton");
const authMessage = document.getElementById("authMessage");
const toggleAuthModeButton = document.getElementById("toggleAuthMode");
const authUsername = document.getElementById("authUsername");
const authPassword = document.getElementById("authPassword");
const toggleAuthPassword = document.getElementById("toggleAuthPassword");
const registerGenresWrapper = document.getElementById("registerGenresWrapper");
const authGenreOptions = document.getElementById("authGenreOptions");
const authGenresToggle = document.getElementById("authGenresToggle");
const activeUsername = document.getElementById("activeUsername");
const homePanel = document.getElementById("homePanel");
const detailPanel = document.getElementById("detailPanel");
const historyPanel = document.getElementById("historyPanel");
const settingsPanel = document.getElementById("settingsPanel");
const mainTitle = document.getElementById("mainTitle");
const mainSubtitle = document.getElementById("mainSubtitle");
const algorithmBadge = document.getElementById("algorithmBadge");
const mainGrid = document.getElementById("mainGrid");
const detailTitle = document.getElementById("detailTitle");
const detailContent = document.getElementById("detailContent");
const relatedGrid = document.getElementById("relatedGrid");
const historyTimeline = document.getElementById("historyTimeline");
const settingsMessage = document.getElementById("settingsMessage");
const settingsGenreOptions = document.getElementById("settingsGenreOptions");
const settingsGenresToggle = document.getElementById("settingsGenresToggle");
const settingsUsername = document.getElementById("settingsUsername");
const settingsCurrentPassword = document.getElementById("settingsCurrentPassword");
const settingsNewPassword = document.getElementById("settingsNewPassword");
const toggleSettingsCurrentPassword = document.getElementById("toggleSettingsCurrentPassword");
const toggleSettingsNewPassword = document.getElementById("toggleSettingsNewPassword");
const deletePassword = document.getElementById("deletePassword");
const toggleDeletePassword = document.getElementById("toggleDeletePassword");
const movieCardTemplate = document.getElementById("movieCardTemplate");


async function fetchJson(url, options = {}) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    if (state.token) {
        headers.Authorization = `Bearer ${state.token}`;
    }
    const response = await fetch(url, {
        headers,
        ...options,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "No se pudo completar la solicitud");
    }

    return response.json();
}


function setStatus(element, message, isError = false) {
    element.textContent = message;
    element.style.color = isError ? "#b42318" : "";
}


function setInputPasswordToggle(button, input) {
    button.addEventListener("click", () => {
        input.type = input.type === "password" ? "text" : "password";
        button.textContent = input.type === "password" ? "Mostrar" : "Ocultar";
    });
}


function renderGenreOptions(container, toggleButton, selectedIds = [], expanded = false) {
    container.innerHTML = "";

    state.genres.forEach((genre, index) => {
        const label = document.createElement("label");
        label.className = "genre-chip";
        if (!expanded && index >= 5) {
            label.classList.add("hidden");
        }

        const input = document.createElement("input");
        input.type = "checkbox";
        input.value = genre.id;
        input.checked = selectedIds.includes(genre.id);

        label.appendChild(input);
        label.appendChild(document.createTextNode(genre.name));
        container.appendChild(label);
    });

    const hasExtraGenres = state.genres.length > 5;
    toggleButton.classList.toggle("hidden", !hasExtraGenres);
    toggleButton.textContent = expanded ? "Mostrar menos" : "Mostrar más";
}


function selectedGenreIds(container) {
    return Array.from(container.querySelectorAll("input:checked")).map(input => Number(input.value));
}


function persistSession() {
    if (!state.user) {
        localStorage.removeItem(SESSION_KEY);
        return;
    }
    localStorage.setItem(SESSION_KEY, JSON.stringify({ token: state.token }));
}


function resetAuthMode() {
    const registerMode = state.authMode === "register";
    authTitle.textContent = registerMode ? "Crear cuenta" : "Iniciar sesión";
    authSubmitButton.textContent = registerMode ? "Crear cuenta" : "Entrar";
    toggleAuthModeButton.textContent = registerMode ? "Volver a iniciar sesión" : "Crear cuenta";
    registerGenresWrapper.classList.toggle("hidden", !registerMode);
    state.authGenresExpanded = false;
    renderGenreOptions(authGenreOptions, authGenresToggle, selectedGenreIds(authGenreOptions), state.authGenresExpanded);
}


function showAuth() {
    authView.classList.remove("hidden");
    appView.classList.add("hidden");
}


function activatePanel(panel) {
    [homePanel, detailPanel, historyPanel, settingsPanel].forEach(item => item.classList.add("hidden"));
    panel.classList.remove("hidden");
}


function showApp() {
    authView.classList.add("hidden");
    appView.classList.remove("hidden");
    activeUsername.textContent = state.user.username;
    settingsUsername.value = state.user.username;
    state.settingsGenresExpanded = false;
    renderGenreOptions(
        settingsGenreOptions,
        settingsGenresToggle,
        state.user.favorite_genres.map(genre => genre.id),
        state.settingsGenresExpanded
    );
}


function communityText(movie) {
    const stats = movie.community_stats || {};
    return `${stats.viewed_count || 0} vistas · ${stats.recommend_count || 0} recomiendan · ${stats.not_recommend_count || 0} no recomiendan`;
}


function shorten(text, length = 110) {
    if (!text) {
        return "";
    }
    return text.length > length ? `${text.slice(0, length).trim()}...` : text;
}


function createMovieCard(movie, onClick, { showOverview = true } = {}) {
    const fragment = movieCardTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".movie-card");
    const poster = fragment.querySelector(".movie-poster");
    const title = fragment.querySelector("h3");
    const year = fragment.querySelector(".movie-year");
    const reason = fragment.querySelector(".movie-reason");
    const stats = fragment.querySelector(".movie-stats");
    const overview = fragment.querySelector(".movie-overview");

    title.textContent = movie.title || "Sin título";
    year.textContent = movie.release_date ? movie.release_date.slice(0, 4) : "N/A";
    reason.textContent = movie.reason || "Sugerida por afinidad local";
    stats.textContent = communityText(movie);
    overview.textContent = showOverview ? shorten(movie.overview || "Sin descripción disponible.") : "";

    if (movie.poster_url) {
        poster.src = movie.poster_url;
        poster.alt = movie.title || "Poster";
    } else {
        poster.removeAttribute("src");
        poster.alt = "Poster no disponible";
    }

    card.addEventListener("click", onClick);
    return fragment;
}


function renderGrid(container, items, emptyMessage, onClickFactory, options = {}) {
    container.innerHTML = "";
    if (!items.length) {
        container.innerHTML = `<p class="section-copy">${emptyMessage}</p>`;
        return;
    }

    items.forEach(item => {
        container.appendChild(createMovieCard(item, () => onClickFactory(item), options));
    });
}


async function loadProfile() {
    const payload = await fetchJson(`${API_URL}/auth/me`);
    state.user = payload.user;
    persistSession();
    showApp();
}


async function loadGenres() {
    const payload = await fetchJson(`${API_URL}/genres`);
    state.genres = payload.genres;
    renderGenreOptions(authGenreOptions, authGenresToggle, [], false);
}


async function handleAuth(event) {
    event.preventDefault();
    setStatus(authMessage, "");

    try {
        const body = {
            username: authUsername.value.trim(),
            password: authPassword.value,
        };

        const endpoint = state.authMode === "register" ? "/auth/register" : "/auth/login";
        if (state.authMode === "register") {
            body.favorite_genre_ids = selectedGenreIds(authGenreOptions);
        }

        const payload = await fetchJson(`${API_URL}${endpoint}`, {
            method: "POST",
            body: JSON.stringify(body),
        });

        state.user = payload.user;
        state.token = payload.token;
        persistSession();
        authForm.reset();
        showApp();
        await loadRecommendations();
    } catch (error) {
        setStatus(authMessage, error.message, true);
    }
}


async function tryRestoreSession() {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) {
        showAuth();
        return;
    }

    try {
        const session = JSON.parse(raw);
        state.token = session.token;
        await loadProfile();
        await loadRecommendations();
    } catch {
        localStorage.removeItem(SESSION_KEY);
        showAuth();
    }
}


async function loadRecommendations() {
    const payload = await fetchJson(`${API_URL}/users/me/recommendations`);
    state.user = payload.user;
    activeUsername.textContent = state.user.username;

    mainTitle.textContent = "Recomendadas para ti";
    mainSubtitle.textContent = "Ordenadas localmente con afinidad por géneros, actividad reciente y opinión de la comunidad.";
    algorithmBadge.textContent = `${payload.algorithm.name}: ${payload.algorithm.summary}`;

    renderGenreOptions(
        settingsGenreOptions,
        settingsGenresToggle,
        state.user.favorite_genres.map(genre => genre.id),
        state.settingsGenresExpanded
    );

    renderGrid(
        mainGrid,
        payload.results,
        "Todavía no hay suficientes señales para recomendar. Marca películas como vistas o define mejor tus gustos.",
        movie => loadMovie(movie.id)
    );

    activatePanel(homePanel);
}


async function searchMovies(query) {
    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
        await loadRecommendations();
        return;
    }

    const payload = await fetchJson(`${API_URL}/search?query=${encodeURIComponent(trimmedQuery)}`);
    mainTitle.textContent = "Resultados de búsqueda";
    mainSubtitle.textContent = `Coincidencias para "${trimmedQuery}".`;
    algorithmBadge.textContent = "La búsqueda reemplaza temporalmente las recomendaciones. La sinopsis completa solo aparece en la vista detallada.";
    renderGrid(
        mainGrid,
        payload.results || [],
        "No se encontraron resultados.",
        movie => loadMovie(movie.id),
        { showOverview: false }
    );
    activatePanel(homePanel);
}


function renderDetail(movie) {
    const genres = (movie.genres || []).map(genre => `<span class="tag">${genre.name}</span>`).join("");
    const feedbackText =
        movie.user_feedback === true ? "La recomiendas" :
        movie.user_feedback === false ? "No la recomiendas" :
        "Sin voto tuyo";

    detailTitle.textContent = movie.title || "Detalle";
    detailContent.innerHTML = `
        <div class="detail-shell">
            <article class="detail-card">
                <img class="detail-poster" src="${movie.poster_url || ""}" alt="${movie.title || "Poster"}">
                <div class="detail-body">
                    <div>
                        <h2 class="detail-title">${movie.title || "Sin título"}</h2>
                        <p class="detail-copy">${movie.release_date || "Fecha desconocida"} · Rating ${movie.vote_average ?? "N/A"}${movie.runtime ? ` · ${movie.runtime} min` : ""}</p>
                    </div>
                    <p class="detail-copy">${movie.overview || "Sin descripción disponible."}</p>
                    <div class="detail-tags">${genres || '<span class="tag">Sin géneros</span>'}</div>
                    <div class="community-grid">
                        <div class="community-card">
                            <small>Usuarios que la vieron</small>
                            <strong>${movie.community_stats.viewed_count}</strong>
                        </div>
                        <div class="community-card">
                            <small>La recomiendan</small>
                            <strong>${movie.community_stats.recommend_count}</strong>
                        </div>
                        <div class="community-card">
                            <small>No la recomiendan</small>
                            <strong>${movie.community_stats.not_recommend_count}</strong>
                        </div>
                    </div>
                    <div class="detail-actions">
                        <button id="markViewedButton" type="button">Marcar como vista</button>
                        <button id="recommendYesButton" class="ghost-button" type="button">Recomendar</button>
                        <button id="recommendNoButton" class="ghost-button" type="button">No recomendar</button>
                        <span class="stat-chip">${feedbackText}</span>
                    </div>
                </div>
            </article>
        </div>
    `;

    document.getElementById("markViewedButton").addEventListener("click", async () => {
        await fetchJson(`${API_URL}/views`, {
            method: "POST",
            body: JSON.stringify({ movie_id: movie.id }),
        });
        await loadMovie(movie.id);
    });

    document.getElementById("recommendYesButton").addEventListener("click", async () => sendFeedback(movie.id, true));
    document.getElementById("recommendNoButton").addEventListener("click", async () => sendFeedback(movie.id, false));
}


async function loadMovie(movieId) {
    const movie = await fetchJson(`${API_URL}/${movieId}`);
    const related = await fetchJson(`${API_URL}/${movieId}/recommendations`);

    state.currentMovie = movie;
    renderDetail(movie);
    renderGrid(
        relatedGrid,
        related.results || [],
        "No hay películas relacionadas disponibles.",
        item => loadMovie(item.id),
        { showOverview: false }
    );
    activatePanel(detailPanel);
}


async function sendFeedback(movieId, recommended) {
    await fetchJson(`${API_URL}/feedback`, {
        method: "POST",
        body: JSON.stringify({
            movie_id: movieId,
            recommended,
        }),
    });
    await loadMovie(movieId);
}


async function loadHistory() {
    const payload = await fetchJson(`${API_URL}/users/me/history`);
    state.user = payload.user;
    activeUsername.textContent = state.user.username;
    historyTimeline.innerHTML = "";

    if (!(payload.history || []).length) {
        historyTimeline.innerHTML = `<p class="section-copy">Todavía no hay películas vistas registradas.</p>`;
        activatePanel(historyPanel);
        return;
    }

    payload.history.forEach(group => {
        const section = document.createElement("section");
        section.className = "timeline-group";
        section.innerHTML = `<h3>${group.period}</h3><div class="timeline-list"></div>`;
        const list = section.querySelector(".timeline-list");

        group.entries.forEach(entry => {
            const wrapper = document.createElement("article");
            wrapper.className = "timeline-entry";
            const recommendationText =
                entry.recommended === true ? "La recomendarías" :
                entry.recommended === false ? "No la recomendarías" :
                "Sin voto registrado";

            wrapper.innerHTML = `
                <img src="${entry.movie.poster_url || ""}" alt="${entry.movie.title || "Poster"}">
                <div>
                    <strong>${entry.movie.title || "Sin título"}</strong>
                    <p class="timeline-copy">${new Date(entry.viewed_at).toLocaleDateString()} · ${recommendationText}</p>
                </div>
            `;
            wrapper.addEventListener("click", () => loadMovie(entry.movie.id));
            list.appendChild(wrapper);
        });

        historyTimeline.appendChild(section);
    });

    activatePanel(historyPanel);
}


async function saveFavoriteGenres() {
    try {
        const payload = await fetchJson(`${API_URL}/users/me/favorite-genres`, {
            method: "PUT",
            body: JSON.stringify({ genre_ids: selectedGenreIds(settingsGenreOptions) }),
        });
        state.user.favorite_genres = payload.favorite_genres;
        setStatus(settingsMessage, "Gustos actualizados.");
        await loadRecommendations();
    } catch (error) {
        setStatus(settingsMessage, error.message, true);
    }
}


async function saveAccount(event) {
    event.preventDefault();
    setStatus(settingsMessage, "");

    try {
        const payload = await fetchJson(`${API_URL}/users/me/account`, {
            method: "PUT",
            body: JSON.stringify({
                current_password: settingsCurrentPassword.value,
                new_username: settingsUsername.value.trim() || null,
                new_password: settingsNewPassword.value || null,
            }),
        });

        state.user = payload.user;
        settingsCurrentPassword.value = "";
        settingsNewPassword.value = "";
        settingsUsername.value = state.user.username;
        persistSession();
        setStatus(settingsMessage, "Cuenta actualizada.");
        showApp();
    } catch (error) {
        setStatus(settingsMessage, error.message, true);
    }
}


async function deleteAccount() {
    try {
        await fetchJson(`${API_URL}/users/me`, {
            method: "DELETE",
            body: JSON.stringify({ password: deletePassword.value }),
        });
        state.user = null;
        state.token = null;
        state.currentMovie = null;
        persistSession();
        showAuth();
        setStatus(authMessage, "Cuenta eliminada.");
    } catch (error) {
        setStatus(settingsMessage, error.message, true);
    }
}


function logout() {
    if (state.token) {
        fetchJson(`${API_URL}/auth/logout`, { method: "POST" }).catch(() => null);
    }
    state.user = null;
    state.token = null;
    state.currentMovie = null;
    persistSession();
    showAuth();
}


document.getElementById("searchForm").addEventListener("submit", event => {
    event.preventDefault();
    searchMovies(document.getElementById("searchInput").value);
});

document.getElementById("searchInput").addEventListener("input", event => {
    if (!event.target.value.trim()) {
        loadRecommendations();
    }
});

document.getElementById("historyButton").addEventListener("click", loadHistory);
document.getElementById("settingsButton").addEventListener("click", () => activatePanel(settingsPanel));
document.getElementById("closeSettingsButton").addEventListener("click", loadRecommendations);
document.getElementById("historyBackButton").addEventListener("click", loadRecommendations);
document.getElementById("saveGenresButton").addEventListener("click", saveFavoriteGenres);
document.getElementById("accountForm").addEventListener("submit", saveAccount);
document.getElementById("deleteAccountButton").addEventListener("click", deleteAccount);
document.getElementById("logoutButton").addEventListener("click", logout);
document.getElementById("backToHomeButton").addEventListener("click", loadRecommendations);
document.getElementById("homeButton").addEventListener("click", loadRecommendations);

toggleAuthModeButton.addEventListener("click", () => {
    state.authMode = state.authMode === "login" ? "register" : "login";
    resetAuthMode();
    setStatus(authMessage, "");
});

authForm.addEventListener("submit", handleAuth);
authGenresToggle.addEventListener("click", () => {
    state.authGenresExpanded = !state.authGenresExpanded;
    renderGenreOptions(authGenreOptions, authGenresToggle, selectedGenreIds(authGenreOptions), state.authGenresExpanded);
});
settingsGenresToggle.addEventListener("click", () => {
    state.settingsGenresExpanded = !state.settingsGenresExpanded;
    renderGenreOptions(
        settingsGenreOptions,
        settingsGenresToggle,
        selectedGenreIds(settingsGenreOptions),
        state.settingsGenresExpanded
    );
});

setInputPasswordToggle(toggleAuthPassword, authPassword);
setInputPasswordToggle(toggleSettingsCurrentPassword, settingsCurrentPassword);
setInputPasswordToggle(toggleSettingsNewPassword, settingsNewPassword);
setInputPasswordToggle(toggleDeletePassword, deletePassword);


async function bootstrap() {
    try {
        await loadGenres();
        resetAuthMode();
        await tryRestoreSession();
    } catch (error) {
        showAuth();
        setStatus(authMessage, error.message, true);
    }
}


bootstrap();
