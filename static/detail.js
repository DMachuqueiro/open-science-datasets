const dialog = document.getElementById("dataset-dialog");
const content = document.getElementById("dataset-dialog-content");
const closeButton = document.getElementById("close-dataset-dialog");

if (dialog && typeof dialog.showModal === "function") {
    let controller;
    let opener;

    document.addEventListener("click", async (event) => {
        const link = event.target.closest("a[data-dataset-detail]");
        if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) {
            return;
        }
        event.preventDefault();
        controller?.abort();
        const request = new AbortController();
        controller = request;
        opener = link;
        const loading = document.createElement("p");
        loading.setAttribute("role", "status");
        loading.textContent = "A carregar os detalhes do dataset…";
        content.replaceChildren(loading);
        content.setAttribute("aria-busy", "true");
        dialog.showModal();

        try {
            const response = await fetch(link.href, {
                headers: {"X-Requested-With": "fetch"},
                signal: request.signal,
            });
            if ((!response.ok && ![404, 502, 504].includes(response.status)) ||
                    !response.headers.get("Content-Type")?.includes("text/html")) {
                throw new Error("Unexpected response");
            }
            const html = await response.text();
            if (!request.signal.aborted && dialog.open) {
                // Fragmento renderizado pelo Flask com escape dos metadados externos.
                content.innerHTML = html;
            }
        } catch (error) {
            if (!request.signal.aborted && dialog.open) {
                const message = document.createElement("p");
                message.setAttribute("role", "alert");
                message.textContent = "Não foi possível carregar os detalhes. Tenta novamente.";
                content.replaceChildren(message);
            }
        } finally {
            if (controller === request) {
                content.setAttribute("aria-busy", "false");
            }
        }
    });

    closeButton.addEventListener("click", () => {
        controller?.abort();
        dialog.close();
    });
    dialog.addEventListener("cancel", () => controller?.abort());
    dialog.addEventListener("close", () => {
        if (dialog.open) {
            return;
        }
        controller?.abort();
        opener?.focus({preventScroll: true});
    });
}
