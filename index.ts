const APP_NAME = "{{APP_NAME}}";

export {};

declare global {
   var loadPyodide: any;
}

window.addEventListener("load", async () => {
    const loadingText = document.body.appendChild(document.createElement("div"));
    loadingText.id = "loading-text";
    loadingText.textContent = "Loading ...";

    let response = await fetch(`./${APP_NAME}.tgz`);
    let buffer = await response.arrayBuffer();
    let pyodide = await loadPyodide();
    await pyodide.unpackArchive(buffer, "gztar");
    let app = pyodide.pyimport(`${APP_NAME}.main`);

    loadingText.remove();
    app.main();
});
