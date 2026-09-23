/*
 * average-worker.js
 * Worker pour créer une moyenne d'un groupe d'image
 * Ouvre les jpeg, les met à l'échelle et les centre sur les coordonnées voulues,
 * fait la moyenne (additive ou composition alpha)
 * et revoit le blob du png obtenu
 * Normalement la mémoire ram est épargnée par :
 *      - le déchargement de chaque image une fois traitée,
 *      - la suppression du worker après la moyenne
 */

self.onmessage = async event => {
    const {
        group,
        width,
        height,
        mode = "additive"
    } = event.data;

    try {
        if (!Array.isArray(group) || group.length === 0) {
            throw new Error("Aucune image à traiter.");
        }

        if (mode !== "additive" && mode !== "alpha") {
            throw new Error(`Mode inconnu : ${mode}`);
        }

        const buffer = await generateGroup(group, width, height, mode);

        self.postMessage({type: "done", buffer}, [buffer]);

    } catch (error) {
        self.postMessage({
            type: "error",
            message: error?.message || String(error),
            stack: error?.stack
        });
    }
};


/*
 ******************************************************************
 * Traitement du groupe
 ******************************************************************
 */
async function generateGroup(group, width, height, mode) {
    const pixelCount = width * height;

    /*
     * Accumulateur RGB.
     * En mode additive :
     *   contient directement la somme pondérée des couleurs.
     * En mode alpha :
     *   contient la couleur résultante du compositing.
     */
    const sum = new Float32Array(pixelCount * 3);

    // seulement pour le mode alpha :
    const alpha = new Float32Array(pixelCount);

    // Chaque image contribue exactement de la même manière à la moyenne.
    const weight = 1 / group.length;

    // Canvas de travail. Il sert uniquement à décoder/redimensionner une image source à la fois.
    const canvas = new OffscreenCanvas(1, 1);
    const ctx = canvas.getContext("2d", { willReadFrequently: true });

    let nextBitmap = await loadBitmap(group[0].url)

    // main loop
    for (let i = 0; i < group.length; i++) {

        const image = group[i];

        // chargement des bitmap avec une boucle d'avance pour optimiser le temps de décodage
        // const bitmap = await loadBitmap(image.url);
        const bitmap = nextBitmap;
        const nextPromise = i + 1 < group.length ? loadBitmap(group[i + 1].url) : null;

        await processImage(image, bitmap, width, height, mode, weight, canvas, ctx, sum, alpha);
        // Le bitmap décodé peut être beaucoup plus gros que le JPG original.
        bitmap.close();

        if (nextPromise) {
            nextBitmap = await nextPromise;
        }

        // Progression.
        // if (i === 0 || i === group.length - 1 || i % 10 === 0) {
        self.postMessage({
            type: "progress",
            current: i + 1,
            total: group.length,
            value: (i + 1) / group.length
        });
        // }

        // Laisser éventuellement le Worker respirer entre deux grosses images.
        if (i % 10 === 0) {
            await yieldToEventLoop();
        }
    }

    /*
     ******************************************************************
     * Conversion finale
     ******************************************************************
     */
    const output = new Uint8ClampedArray(pixelCount * 4);

    for (let p = 0; p < pixelCount; p++) {
        const a = alpha[p]; // alpha only needed for alpha composition average mode

        const outputIndex = p * 4;

        // Aucun pixel n'était ici.
        if (a <= 0) {
            output[outputIndex] = 0;
            output[outputIndex + 1] = 0;
            output[outputIndex + 2] = 0;
            output[outputIndex + 3] = 0;
            continue;
        }

        const sumIndex = p * 3;

        var r, g, b;

        if (mode === "additive") {
            r = linearToSrgb(sum[sumIndex] / group.length);
            g = linearToSrgb(sum[sumIndex + 1] / group.length);
            b = linearToSrgb(sum[sumIndex + 2] / group.length);
        } else {
            r = linearToSrgb(sum[sumIndex] / a);
            g = linearToSrgb(sum[sumIndex + 1] / a);
            b = linearToSrgb(sum[sumIndex + 2] / a);
        }

        output[outputIndex] = r;
        output[outputIndex + 1] = g;
        output[outputIndex + 2] = b;
        /* alpha */
        output[outputIndex + 3] = Math.round(Math.min(1, a) * 255);
    }

    // On utilise un canvas uniquement à la fin pour produire le PNG.
    const resultCanvas = new OffscreenCanvas(width, height);
    const resultCtx = resultCanvas.getContext("2d");
    const imageData = new ImageData(output, width, height);

    resultCtx.putImageData(imageData, 0, 0);

    const blob = await resultCanvas.convertToBlob({ type: "image/png" });

    // Blob.arrayBuffer() crée le buffer qui sera transféré au thread principal.
    const buffer = await blob.arrayBuffer();
    return buffer;
}

/*
 ******************************************************************
 * routine de chargement d'une image
 ******************************************************************
 */
async function loadBitmap(url) {

    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(
            `HTTP ${response.status} lors du chargement de ${url}`
        );
    }

    const blob = await response.blob();

    if (!(blob instanceof Blob)) {
        throw new Error(
            `La réponse de ${url} n'est pas un Blob`
        );
    }

    if (!blob.type.startsWith("image/")) {
        throw new Error(
            `Le serveur renvoie "${blob.type}" pour ${url}`
        );
    }

    return await createImageBitmap(blob);
}

/*
 ******************************************************************
 * Traitement d'une image
 ******************************************************************
 */

async function processImage(imageData, bitmap, outputWidth, outputHeight, mode, weight, canvas, ctx, sum, alpha) {
    // Dimensions après transformation.
    const scaledWidth = bitmap.width * imageData.scale;
    const scaledHeight = bitmap.height * imageData.scale;

    // Le point (x, y) de l'image source doit être placé
    // au centre de l'image finale.
    const imageX = outputWidth / 2 - imageData.x * imageData.scale;
    const imageY = outputHeight / 2 - imageData.y * imageData.scale;

    // Bounding box de l'image dans la sortie.
    const left = Math.floor(imageX);
    const top = Math.floor(imageY);
    const right = Math.ceil(imageX + scaledWidth);
    const bottom = Math.ceil(imageY + scaledHeight);

    // Crop de la bounding box avec le cadre final.
    const x0 = Math.max(0, left);
    const y0 = Math.max(0, top);
    const x1 = Math.min(outputWidth, right);
    const y1 = Math.min(outputHeight, bottom);

    // Image complètement hors cadre.
    if (x0 >= x1 || y0 >= y1) {
        return;
    }


    // Canvas seulement aussi grand que nécessaire pour limiter la mémoire.
    const drawWidth = x1 - x0;
    const drawHeight = y1 - y0;

    canvas.width = drawWidth;
    canvas.height = drawHeight;

    // Nettoyage du contexte.
    ctx.clearRect(0, 0, drawWidth, drawHeight);

    // Position relative au rectangle découpé.
    const drawX = imageX - x0;
    const drawY = imageY - y0;

    //Redimensionnement par Canvas. On ne garde donc pas une copie redimensionnée complète de l'image.
    // console.time("draw");
    ctx.drawImage(
        bitmap,
        drawX,
        drawY,
        scaledWidth,
        scaledHeight
    );
    // console.timeEnd("draw");

    // Seulement les pixels visibles dans l'image finale.
    // console.time("read");
    const pixels = ctx.getImageData(0, 0, drawWidth, drawHeight).data;
    // console.timeEnd("read")

    // Main loop
    // console.time("loop pixel");
    const rowLength = drawWidth * 4;
    const outputRowLength = outputWidth * 3;
    for (let localY = 0; localY < drawHeight; localY++) {
        // const globalY = y0 + localY;
        const pixelsRow = localY * rowLength;
        const outputRow = (y0 + localY) * outputRowLength;

        for (let localX = 0; localX < drawWidth; localX++) {
            //const globalX = x0 + localX;
            //const localIndex = (localY * drawWidth + localX) * 4;
            const localIndex = pixelsRow + localX * 4;
            // const sumIndex = globalPixelIndex * 3;
            const sumIndex = outputRow + (x0 + localX) * 3;

            const r = pixels[localIndex];
            const g = pixels[localIndex + 1];
            const b = pixels[localIndex + 2];
            const a = pixels[localIndex + 3] / 255; // jpg normalement opaque mais on sait jamais

            if (a <= 0) {
                continue;
            }

            // const globalPixelIndex = globalY * outputWidth + globalX;
            const globalPixelIndex = (y0 + localY) * outputWidth + x0 + localX

            if (mode === "additive") {
                // ----------------------------------------
                // Moyenne additive : Chaque image vaut exactement 1/N.
                // ----------------------------------------

                sum[sumIndex] += srgbToLinearTable[r];
                sum[sumIndex + 1] += srgbToLinearTable[g];
                sum[sumIndex + 2] += srgbToLinearTable[b];

                alpha[globalPixelIndex] += weight * a;
            } else {
                // ----------------------------------------
                // Compositing alpha : Chaque image possède une opacité globale de 1/N.
                // ----------------------------------------
                const sourceAlpha = weight * a;
                const destAlpha = alpha[globalPixelIndex];

                sum[sumIndex] = srgbToLinearTable[r] * sourceAlpha + sum[sumIndex] * (1 - sourceAlpha);
                sum[sumIndex + 1] = srgbToLinearTable[g] * sourceAlpha + sum[sumIndex + 1] * (1 - sourceAlpha);
                sum[sumIndex + 2] = srgbToLinearTable[b] * sourceAlpha + sum[sumIndex + 2] * (1 - sourceAlpha);

                alpha[globalPixelIndex] = sourceAlpha + destAlpha * (1 - sourceAlpha);
            }
        }
    }
    // console.timeEnd("loop pixel");
}


const srgbToLinearTable = new Float32Array(256);
for (let i = 0; i < 256; i++) {
    const c = i / 255;
    srgbToLinearTable[i] = c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

function linearToSrgb(value) {
    value = Math.max(0, Math.min(1, value));
    let c;
    if (value <= 0.0031308) {
        c = value * 12.92;
    } else {
        c = 1.055 * Math.pow(value, 1 / 2.4) - 0.055;
    }
    return Math.round(c * 255);
}

function yieldToEventLoop() {
    return new Promise(resolve => setTimeout(resolve, 0));
}