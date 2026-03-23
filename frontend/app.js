const API_URL = "http://127.0.0.1:8000/movies";
let historyStack = [];

async function searchMovie() {
    const query = document.getElementById("searchInput").value;

    const res = await fetch(`${API_URL}/search?query=${query}`);
    const data = await res.json();

    const results = document.getElementById("results");
    results.innerHTML = "";

    data.results.forEach(movie => {
        const li = document.createElement("li");
        li.textContent = `${movie.title} (${movie.release_date?.slice(0,4) || "N/A"})`;

        // CLICK → cargar detalles
        li.onclick = () => loadMovie(movie.id);

        results.appendChild(li);
    });
}


async function loadMovie(movieId) {
    historyStack.push(movieId);
    // limpiar recomendaciones anteriores
    document.getElementById("recommendations").innerHTML = "";
    

    // obtener detalles
    const resDetails = await fetch(`${API_URL}/${movieId}`);
    const movie = await resDetails.json();

    document.getElementById("details").innerHTML = `
        <h3>${movie.title}</h3>
        <p><strong>Fecha:</strong> ${movie.release_date}</p>
        <p><strong>Rating:</strong> ⭐ ${movie.vote_average}</p>
        <p>${movie.overview || "Sin descripción disponible"}</p>
    `;

    // obtener recomendaciones
    const resRec = await fetch(`${API_URL}/${movieId}/recommendations`);
    const recData = await resRec.json();

    const recList = document.getElementById("recommendations");
    recList.innerHTML = "";

    recData.results.slice(0, 10).forEach(rec => {
        const li = document.createElement("li");
        li.textContent = `${rec.title} (${rec.release_date?.slice(0,4) || "N/A"})`;

        // IMPORTANTE: cada recomendación también es clickeable
        li.onclick = () => loadMovie(rec.id);

        recList.appendChild(li);
    });
}